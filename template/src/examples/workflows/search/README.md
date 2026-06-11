# Document Ingestion Workflow Example

This example wraps the search-starter-app ingestion pipeline in a [Mistral Workflow](https://docs.mistral.ai/capabilities/workflows/), adding durability, observability, and retry support.

## What It Demonstrates

| Primitive | Where |
|-----------|-------|
| `@workflows.workflow.define` | `workflow.py` — defines the workflow with a name visible in the Mistral Console |
| `@workflows.workflow.entrypoint` | `workflow.py` — pure orchestration, no I/O |
| `@workflows.activity` | `activities.py` — all file I/O, embedding calls, and Vespa writes |
| Pydantic input/output models | `models.py` — typed boundaries between workflow and activities |
| `workflows.run_worker()` | `worker.py` — registers workflows with the Temporal engine |

## Architecture

```
IngestionWorkflow.run(IngestionInput)
└── ingest_documents activity
    ├── FilesystemFileLoader     [loads documents]
    ├── PlainTextExtractor       [for .txt, .md, .csv, .json files]
    │   or MistralOCRExtractor  [for PDFs and images]
    ├── MarkdownTextSplitter     [chunks the content]
    ├── MistralEmbedder          [generates vector embeddings]
    └── VespaSearchIndex         [stores chunks in Vespa]
```

## Prerequisites

1. Install the workflows extra:
   ```bash
   make install-workflows
   ```

2. Vespa must be running:
   ```bash
   make setup-vespa
   ```

3. Set `MISTRAL_API_KEY` in your `.env` file.

## Running the Example

> The worker must be running before you trigger the workflow, otherwise the API returns `Workflow not found`.

**Terminal 1 — start the worker (leave this running):**
```bash
make start-examples
```

**Terminal 2 — trigger ingestion:**
```bash
# Ingest a single file
make execute-ingestion input='{"file_path": "sample_data/hello.txt"}'

# Ingest a directory
make execute-ingestion input='{"file_path": "sample_data"}'

# Use a custom collection name
make execute-ingestion input='{"file_path": "sample_data/hello.txt", "collection_name": "mydocs"}'
```

You can also trigger the workflow from the [Mistral Console](https://console.mistral.ai/build/workflows) by selecting `document-ingestion` and providing the input JSON.

## Key Difference from Direct Ingestion

The existing `make ingest` command runs ingestion synchronously in the terminal. The workflow approach adds:

- **Durability**: the worker can restart mid-ingestion and resume from the last completed step
- **Observability**: each execution is visible in the Mistral Console with a full timeline
- **Retries**: the activity retries automatically on transient errors (network blips, API rate limits)

Search operations remain direct queries — they don't benefit from workflow orchestration since they complete in milliseconds.
