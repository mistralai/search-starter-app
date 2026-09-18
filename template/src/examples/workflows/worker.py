"""Start a worker that registers search ingestion workflows for search-starter-app.

The workflow definitions and activities come from ``mistralai-workflows-plugins-search``;
this module's job is to build the Search Toolkit pipelines, register them (and a
``RoutedPipeline``) on the plugin's ``pipeline_registry``, and hand the plugin's
workflow classes to ``run_worker``.
"""
# ruff: noqa: E402

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(override=True)

from mistralai.client import Mistral
from mistralai.search.toolkit.embedders import MistralEmbedder
from mistralai.search.toolkit.ingestion.extractors import (
    MistralOCRExtractor,
    PlainTextExtractor,
)
from mistralai.search.toolkit.ingestion.loaders import FilesystemFileLoader
from mistralai.search.toolkit.ingestion.pipelines import Pipeline, RoutedPipeline
from mistralai.search.toolkit.ingestion.text_splitters import (
    MarkdownTextSplitter,
    MarkdownTextSplitterConfig,
)
from mistralai.workflows import run_worker
from mistralai.workflows.plugins.search import (
    IngestBatchWorkflow,
    IngestDocumentsWorkflow,
    pipeline_registry,
)
from search_app import get_index

EXAMPLE_WORKFLOWS = [IngestDocumentsWorkflow, IngestBatchWorkflow]


def _build_pipelines(collection_name: str) -> tuple[Pipeline, Pipeline]:
    """Assemble the plain-text and OCR pipelines from shared components."""
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY is not set. Check your .env file.")

    mistral_client = Mistral(
        api_key=api_key,
        server_url=os.getenv("MISTRAL_API_URL", "https://api.mistral.ai"),
    )

    shared = dict(
        loader=FilesystemFileLoader(),
        text_splitter=MarkdownTextSplitter(
            MarkdownTextSplitterConfig(chunk_size=4096, chunk_overlap=50)
        ),
        embedder=MistralEmbedder(client=mistral_client),
        stores=get_index(collection_name),
    )

    return (
        Pipeline(extractor=PlainTextExtractor(), **shared),
        Pipeline(extractor=MistralOCRExtractor(client=mistral_client), **shared),
    )


def _register_pipelines(collection_name: str) -> None:
    """Register pipelines and a router on the plugin's ``pipeline_registry``."""
    plain_text_pipeline, ocr_pipeline = _build_pipelines(collection_name)

    pipeline_registry.register("plain-text", plain_text_pipeline)
    pipeline_registry.register("ocr", ocr_pipeline)
    pipeline_registry.register_router(
        "default",
        RoutedPipeline(
            {
                "plain_text": plain_text_pipeline,
                "ocr": ocr_pipeline,
            }
        ),
    )


async def main() -> None:
    if not os.environ.get("DEPLOYMENT_NAME"):
        print(
            "Error: DEPLOYMENT_NAME is not set. Add it to your .env file, e.g.:\n"
            "  DEPLOYMENT_NAME=my-search-project",
            file=sys.stderr,
        )
        raise SystemExit(1)

    collection_name = os.environ.get("COLLECTION_NAME", "exampledocs")
    _register_pipelines(collection_name)

    names = [wf.__name__ for wf in EXAMPLE_WORKFLOWS]
    print(
        f"Starting worker with {len(EXAMPLE_WORKFLOWS)} workflow(s): "
        f"{', '.join(names)}"
    )
    await run_worker(EXAMPLE_WORKFLOWS)


if __name__ == "__main__":
    asyncio.run(main())
