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

From a local git checkout:

```bash
copier copy ./search-starter-app my-search-project
```

Or use the setup wrapper (passes `MISTRAL_API_KEY` when exported):

```bash
export MISTRAL_API_KEY=your-key   # optional
./search-starter-app/scripts/setup my-search-project
```

Copier uses the **latest git tag** of the template (not uncommitted files). After changing the template, commit and tag a new release (e.g. `v1.0.2`) so `copier copy ./search-starter-app` picks up the changes.

Initial setup only asks for **project name** and **collection name** (no port questions). Ports default to `18080` / `19072` in `.env`. If `MISTRAL_API_KEY` is exported in your shell, a post-copy task writes it into `.env` automatically (not prompted).

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

Port selection is intentionally not part of the initial Copier questions. Generated projects default to `18080` / `19072`; if needed later, users can edit `.env` (`VESPA_QUERY_PORT`, `VESPA_CONFIG_PORT`) without re-generating the project.

## Variables

| Variable           | Description                                      |
| ------------------ | ------------------------------------------------ |
| `project_name`     | Name of the project (pyproject.toml, container)  |
| `collection_name`  | Vespa collection / schema name                   |

Generated `.env` sets default Vespa ports and `WORKSPACE_ROOT=.`; `MISTRAL_API_KEY` is filled from your shell when set, otherwise add it manually before ingest/search.
