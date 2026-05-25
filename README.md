# search-starter-app

Copier template for bootstrapping [Mistral Search Toolkit](https://pypi.org/project/mistralai-search-toolkit/) projects.

Built on the SDK in [mistralai/search/toolkit](https://github.com/mistralai/mistral-pro/tree/main/dashboards/main/search/toolkit) — ingestion pipelines, Vespa indexing, and hybrid retrieval.

## Prerequisites

This repo is a **[Copier](https://copier.readthedocs.io/)** template — a Python CLI that scaffolds a new project from `template/` (not the French verb *copier*).

Install Copier once (pick one):

```bash
uv tool install copier
```

Or run it without a global install via [uv](https://docs.astral.sh/uv/):

```bash
uvx copier copy gh:mistralai/search-starter-app my-search-project
```

You also need [Docker](https://docs.docker.com/get-docker/) for local Vespa and [uv](https://docs.astral.sh/uv/) in the generated project.

## Usage

```bash
copier copy gh:mistralai/search-starter-app my-search-project
```

## Template Structure

```
template/
├── .env.jinja
├── pyproject.toml.jinja
├── README.md.jinja
├── Makefile.jinja                  # → Makefile in generated project
├── docker-compose.yaml.jinja
├── sample_data/hello.txt
├── .agents/skills/search/          # Search Toolkit agent skill
└── src/
    ├── entrypoints/
    │   ├── ingest.py               # Pipeline → VespaSearchIndex (file or directory)
    │   └── search.py               # QueryEngine → VectorRetriever
    └── vespa_app/
        ├── __init__.py               # VespaApp definition
        └── migrations/               # mistral-vespa migrate (hybrid query profile)
```

## Quick start (after `copier copy`)

These commands run in the **generated project**. The repo root `Makefile` is only for template CI.

```bash
cd my-search-project
make setup-vespa
make ingest path=sample_data/hello.txt
make search query="hello world"
make bruno   # optional: API files under vespa/bruno/vespa/
```

## Variables

| Variable           | Description                                      |
| ------------------ | ------------------------------------------------ |
| `project_name`     | Name of the project (pyproject.toml, container)  |
| `mistral_api_key`  | Mistral API key (written to `.env`, git-ignored) |
| `collection_name`  | Vespa collection / schema name                   |
| `vespa_query_port` | Host port for query API (default `18080`, maps to container `:8080`) |
| `vespa_config_port`| Host port for config server (default `19072`, maps to `:19071`) |

Generated `.env` also sets `WORKSPACE_ROOT=.` so Bruno files are written inside the project.
