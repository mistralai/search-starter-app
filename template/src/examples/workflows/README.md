# Workflow Examples

This folder contains examples that integrate the search-starter-app with the [Mistral Workflows](https://docs.mistral.ai/capabilities/workflows/) framework.

Workflow-based examples live under `examples/workflows/`. Other examples that do not use the workflows framework (standalone scripts, direct API calls, etc.) live directly under `examples/`.

## Available examples

| Example | Workflow name | Makefile target | Description |
| --- | --- | --- | --- |
| [search/](search/) | `document-ingestion` | `make execute-ingestion` | Basic: 2 activities wrapping the full pipeline |
| [search_pipeline/](search_pipeline/) | `document-ingestion-pipeline` | `make execute-pipeline-ingestion` | Advanced: one activity per pipeline stage |

Both examples ingest local files into Vespa using the same Search Toolkit components as `make ingest`. Choose the basic example to get started; use the pipeline example when you want per-step retries, timeouts, and a detailed timeline in the Mistral Console.

## Prerequisites

The workflows framework is an **optional** dependency — the core search project works without it.

> Run these commands from your **generated project root** (the folder created by `copier copy`), not from the `search-starter-app` template repo itself.

```bash
make install-workflows   # uv sync --extra workflows
make setup-vespa
```

Ensure these are set in your `.env` file:

- `MISTRAL_API_KEY`
- `DEPLOYMENT_NAME` — a stable identifier for this worker (defaults to your project name when generated via `copier copy`)

## Workflow input

Both workflows accept the same JSON input:

```json
{
  "file_path": "sample_data/hello.txt",
  "collection_name": "exampledocs"
}
```

| Field | Required | Default | Description |
| --- | --- | --- | --- |
| `file_path` | yes | — | Path to a file or directory to ingest |
| `collection_name` | no | `"exampledocs"` | Vespa collection name |

## How to run

> **Important:** execution commands call the Mistral Workflows API. The workflow must be registered first by a running worker. If you see `Workflow not found`, start the worker below and retry.

**Terminal 1 — start the examples worker (leave this running):**

```bash
make start-examples
```

Wait until the worker is listening for execution requests. It registers all workflows listed in `worker.py`.

**Terminal 2 — trigger a workflow:**

```bash
# Basic example (2 activities)
make execute-ingestion
make execute-ingestion input='{"file_path": "sample_data/hello.txt"}'

# Advanced example — one activity per pipeline stage
make execute-pipeline-ingestion
make execute-pipeline-ingestion input='{"file_path": "sample_data", "collection_name": "mydocs"}'
```

You can also trigger workflows from the [Mistral Console](https://console.mistral.ai/build/workflows): select `document-ingestion` or `document-ingestion-pipeline`, click **Start Workflow**, and provide the input JSON.

After ingestion, search directly (no workflow):

```bash
make search query="hello world"
```

## Folder layout

```text
examples/workflows/
├── README.md              # This file
├── worker.py              # Registers and runs all workflow examples
├── start.py               # CLI to trigger a workflow execution
├── search/                # Basic example (2 activities)
│   ├── models.py
│   ├── activities.py
│   ├── workflow.py
│   └── README.md
└── search_pipeline/       # Advanced example (7 activities)
    ├── models.py
    ├── activities.py
    ├── workflow.py
    └── README.md
```

## Design principles

- **Workflows for ingestion** — document ingestion is long-running and benefits from durability, retries, and observability in the Mistral Console.
- **Search stays direct** — search queries use `make search` / `entrypoints/search.py` for low latency. Workflows are not needed for simple queries.
- **Activities own all I/O** — filesystem access, API calls, and Vespa writes live in `activities.py`. The workflow body in `workflow.py` only orchestrates.
- **Granular vs bundled activities** — the basic example bundles the pipeline into fewer activities; the pipeline example exposes each stage separately for production-style observability. The pipeline example passes serialized document data between steps and is best suited to **small files** (~2 MB activity payload limit); see [search_pipeline/README.md](search_pipeline/README.md#large-files-and-payload-limits).

## Adding a new workflow example

1. Create a subdirectory under `examples/workflows/` (e.g. `my_example/`).
2. Add `models.py`, `activities.py`, `workflow.py`, and a `README.md`.
3. Export the workflow class from the package `__init__.py`.
4. Register it in `EXAMPLE_WORKFLOWS` in `worker.py`.
5. Add a Makefile target that calls `examples.workflows.start --workflow <name>`.

Example structure:

```text
examples/workflows/my_example/
├── __init__.py
├── models.py
├── activities.py
├── workflow.py
└── README.md
```

## Troubleshooting

| Issue | Fix |
| --- | --- |
| `Workflow not found` | Start `make start-examples` in a separate terminal, then retry |
| `DEPLOYMENT_NAME is required` | Add `DEPLOYMENT_NAME=<your-project>` to `.env` |
| Worker fails on startup | Ensure `imports_passed_through()` wraps activity imports in `workflow.py` when activities use `mistralai.client` |
| `unserializable_payload_error` / payload too large | Advanced pipeline passes full document dicts between activities (~2 MB limit). Use `make ingest`, the basic `document-ingestion` workflow, or OffloadableField + blob storage for larger files — see [search_pipeline/README.md](search_pipeline/README.md#large-files-and-payload-limits) |
| Vespa errors during indexing | Run `make setup-vespa` before triggering ingestion |

Enable verbose logging:

```bash
LOG_LEVEL=DEBUG make start-examples
```
