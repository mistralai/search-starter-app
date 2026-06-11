# Document Ingestion Pipeline (Advanced)

Advanced workflow example where **each Search Toolkit pipeline stage is its own activity**. Use this when you want per-step retries, timeouts, and a detailed timeline in the Mistral Console.

## Comparison with the basic example

| | [search/](../search/) (basic) | search_pipeline/ (this example) |
| --- | --- | --- |
| Workflow name | `document-ingestion` | `document-ingestion-pipeline` |
| Activities | 2 (`collect_document_paths`, `ingest_documents`) | 7 (one per pipeline stage) |
| Console timeline | Coarse-grained | Fine-grained: load → extract → split → embed → index |
| Best for | Getting started, minimal boilerplate | Production patterns, per-step retry policies |

## Pipeline stages (activities)

```
For each file:
  pipeline_load_document        → FilesystemFileLoader
  pipeline_extract_plain_text   → PlainTextExtractor   (.txt, .md, .csv, …)
    or pipeline_extract_with_ocr → MistralOCRExtractor (PDFs, images)
  pipeline_split_document       → MarkdownTextSplitter
  pipeline_embed_document       → MistralEmbedder
  pipeline_index_document       → VespaSearchIndex
```

## Workflow input

```json
{
  "file_path": "sample_data/hello.txt",
  "collection_name": "exampledocs"
}
```

## Run

**Terminal 1:**
```bash
make start-examples
```

**Terminal 2:**
```bash
make execute-pipeline-ingestion
make execute-pipeline-ingestion input='{"file_path": "sample_data", "collection_name": "mydocs"}'
```

Or from the [Mistral Console](https://console.mistral.ai/build/workflows): select `document-ingestion-pipeline`.

## What to look for in the Console

Each file should produce a sequence of activity events:

1. **pipeline_load_document** — file read from disk
2. **pipeline_extract_plain_text** or **pipeline_extract_with_ocr** — text extraction
3. **pipeline_split_document** — chunking
4. **pipeline_embed_document** — embedding API call
5. **pipeline_index_document** — Vespa write

If a step fails (e.g. transient OCR error), only that activity retries — completed steps are not re-run.

## Large files and payload limits

This example passes **serialized file and document data** between activities (see `_file_to_dict` / `_document_to_dict` in `activities.py`). Workflows enforce Temporal's **~2 MB limit** on each activity input and output.

Payload size grows at every stage:

| Stage | What crosses the activity boundary |
| --- | --- |
| load → extract | Raw file bytes (JSON-serialised) |
| extract → split | Full extracted text |
| split → embed | Text duplicated in every chunk |
| embed → index | Chunk text + embedding vectors |

**This example is intended for small files** (e.g. `sample_data/hello.txt`) where the goal is per-step retries, timeouts, and a detailed timeline in the Mistral Console.

### What to use instead for larger files

| Scenario | Recommendation |
| --- | --- |
| Local files or directories, no per-step Console timeline needed | `make ingest` |
| Workflow durability with minimal payload size | [Basic example](../search/) (`document-ingestion`) — passes only file paths; the full pipeline runs inside one activity |
| Production ingestion with per-step activities and large documents | Pass **references** (paths, S3/GCS URIs, artifact IDs) between activities instead of inline payloads, or use **OffloadableField** with blob storage — see the [Handling Large Data](https://docs.mistral.ai/capabilities/workflows/guides/handling-large-data/) guide |

We deliberately keep this starter example simple (inline dicts, no cloud storage setup).
