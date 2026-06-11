"""Advanced ingestion workflow — one activity per pipeline step.

Demonstrates granular workflow orchestration over the Search Toolkit pipeline:
  load → extract → split → embed → index

Each stage is a separate @workflows.activity with its own timeout and retry
policy. The workflow fans out over files and branches deterministically on
file suffix to pick PlainTextExtractor vs MistralOCRExtractor.
"""

import mistralai.workflows as workflows
from mistralai.workflows import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import (
        collect_document_paths,
        embed_document,
        extract_plain_text,
        extract_with_ocr,
        index_document,
        load_document,
        split_document,
    )

from .models import PipelineIngestionInput, PipelineIngestionResult  # noqa: E402

_TEXT_SUFFIXES = frozenset({".txt", ".md", ".markdown", ".csv", ".json"})


@workflows.workflow.define(
    name="document-ingestion-pipeline",
    workflow_display_name="Document Ingestion (Pipeline Steps)",
    workflow_description=(
        "Advanced ingestion example: each Search Toolkit stage runs as its own "
        "activity (load → extract → split → embed → index) with per-step retries "
        "and observability in the Mistral Console."
    ),
)
class PipelineIngestionWorkflow:
    """Orchestrate ingestion with one durable activity per pipeline stage."""

    @workflows.workflow.entrypoint
    async def run(self, params: PipelineIngestionInput) -> PipelineIngestionResult:
        paths = await collect_document_paths(file_path=params.file_path)

        total_chunks = 0
        for path in paths:
            suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
            file_data = await load_document(file_path=path)

            if f".{suffix}" in _TEXT_SUFFIXES:
                document_data = await extract_plain_text(file_data=file_data)
            else:
                document_data = await extract_with_ocr(file_data=file_data)

            document_data = await split_document(document_data=document_data)
            document_data = await embed_document(document_data=document_data)
            total_chunks += await index_document(
                document_data=document_data,
                collection_name=params.collection_name,
            )

        return PipelineIngestionResult(
            status="success",
            total_chunks=total_chunks,
            file_count=len(paths),
            collection_name=params.collection_name,
        )
