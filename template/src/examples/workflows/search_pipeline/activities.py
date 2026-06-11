"""Activities for the pipeline-step ingestion workflow.

Each Search Toolkit pipeline stage is a separate durable activity so the Mistral
Console timeline shows load → extract → split → embed → index as distinct steps
with independent retry policies.
"""

import os
from datetime import timedelta
from functools import cache
from pathlib import Path
from typing import Any

import mistralai.workflows as workflows
from mistralai.client import Mistral
from mistralai.search.toolkit.context import IngestContext
from mistralai.search.toolkit.document import Document
from mistralai.search.toolkit.embedders import MistralEmbedder
from mistralai.search.toolkit.ingestion import File
from mistralai.search.toolkit.ingestion.extractors import (
    MistralOCRExtractor,
    PlainTextExtractor,
)
from mistralai.search.toolkit.ingestion.loaders import FilesystemFileLoader
from mistralai.search.toolkit.ingestion.text_splitters import (
    MarkdownTextSplitter,
    MarkdownTextSplitterConfig,
)
from mistralai.search.toolkit.plugins.vespa import VespaClientConfig
from mistralai.workflows import Depends
from vespa_app import app, vespa_endpoint


@cache
def get_mistral_client() -> Mistral:
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY is not set. Check your .env file.")
    return Mistral(
        api_key=api_key,
        server_url=os.getenv("MISTRAL_API_URL", "https://api.mistral.ai"),
    )


def get_embedder() -> MistralEmbedder:
    return MistralEmbedder(client=get_mistral_client())


def get_ocr_extractor() -> MistralOCRExtractor:
    return MistralOCRExtractor(client=get_mistral_client())


def get_loader() -> FilesystemFileLoader:
    return FilesystemFileLoader()


def get_text_splitter() -> MarkdownTextSplitter:
    return MarkdownTextSplitter(
        MarkdownTextSplitterConfig(chunk_size=4096, chunk_overlap=50)
    )


def get_plain_text_extractor() -> PlainTextExtractor:
    return PlainTextExtractor()


def _file_to_dict(file: File) -> dict[str, Any]:
    return file.model_dump(mode="json")


def _file_from_dict(data: dict[str, Any]) -> File:
    return File.model_validate(data)


def _document_to_dict(document: Document) -> dict[str, Any]:
    return document.model_dump(mode="json")


def _document_from_dict(data: dict[str, Any]) -> Document:
    return Document.model_validate(data)


@workflows.activity(
    name="pipeline_collect_document_paths",
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy_max_attempts=1,
)
async def collect_document_paths(file_path: str) -> list[str]:
    """List all files under a path (file or directory)."""
    root = Path(file_path)
    if root.is_file():
        documents = [root]
    elif root.is_dir():
        documents = sorted(p for p in root.rglob("*") if p.is_file())
    else:
        raise ValueError(f"Path not found: {file_path}")

    if not documents:
        raise ValueError(f"No files found at: {file_path}")

    return [str(p) for p in documents]


@workflows.activity(
    name="pipeline_load_document",
    start_to_close_timeout=timedelta(minutes=1),
    retry_policy_max_attempts=2,
)
async def load_document(
    file_path: str,
    loader: FilesystemFileLoader = Depends(get_loader),
) -> dict[str, Any]:
    """Load a single file from disk into a serialisable File payload."""
    file = await loader.load_file(file_path)
    return _file_to_dict(file)


@workflows.activity(
    name="pipeline_extract_plain_text",
    start_to_close_timeout=timedelta(minutes=2),
    retry_policy_max_attempts=2,
)
async def extract_plain_text(
    file_data: dict[str, Any],
    extractor: PlainTextExtractor = Depends(get_plain_text_extractor),
) -> dict[str, Any]:
    """Extract text from plain-text formats (.txt, .md, .csv, .json, …)."""
    file = _file_from_dict(file_data)
    document = await extractor.extract(file, context=IngestContext())
    return _document_to_dict(document)


@workflows.activity(
    name="pipeline_extract_with_ocr",
    start_to_close_timeout=timedelta(minutes=10),
    retry_policy_max_attempts=3,
)
async def extract_with_ocr(
    file_data: dict[str, Any],
    ocr_extractor: MistralOCRExtractor = Depends(get_ocr_extractor),
) -> dict[str, Any]:
    """Extract text from PDFs and images via Mistral OCR."""
    file = _file_from_dict(file_data)
    document = await ocr_extractor.extract(file, context=IngestContext())
    return _document_to_dict(document)


@workflows.activity(
    name="pipeline_split_document",
    start_to_close_timeout=timedelta(minutes=2),
    retry_policy_max_attempts=2,
)
async def split_document(
    document_data: dict[str, Any],
    text_splitter: MarkdownTextSplitter = Depends(get_text_splitter),
) -> dict[str, Any]:
    """Split an extracted document into chunks."""
    document = _document_from_dict(document_data)
    chunks = text_splitter.split_document(document, context=IngestContext())
    return _document_to_dict(document.model_copy(update={"chunks": chunks}))


@workflows.activity(
    name="pipeline_embed_document",
    start_to_close_timeout=timedelta(minutes=5),
    retry_policy_max_attempts=3,
)
async def embed_document(
    document_data: dict[str, Any],
    embedder: MistralEmbedder = Depends(get_embedder),
) -> dict[str, Any]:
    """Generate vector embeddings for all chunks in a document."""
    document = _document_from_dict(document_data)
    if not document.chunks:
        return document_data

    embedded_chunks = await embedder.embed_chunks(list(document.chunks))
    return _document_to_dict(document.model_copy(update={"chunks": embedded_chunks}))


@workflows.activity(
    name="pipeline_index_document",
    start_to_close_timeout=timedelta(minutes=5),
    retry_policy_max_attempts=2,
)
async def index_document(
    document_data: dict[str, Any],
    collection_name: str,
) -> int:
    """Write an embedded document to Vespa and return the number of chunks indexed."""
    document = _document_from_dict(document_data)
    vector_store = app.get_search_index(
        VespaClientConfig(endpoint=vespa_endpoint()),
        collection_name=collection_name,
    )
    await vector_store.index_document(document, context=IngestContext())
    return len(document.chunks)
