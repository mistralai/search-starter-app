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

Optional wrapper (same as `copier copy`, no extra flags):

```bash
./search-starter-app/scripts/setup my-search-project
```

Copier uses the **latest git tag** of the template (not uncommitted files). After changing the template, commit and tag a new release so `copier copy ./search-starter-app` picks up the changes.

Initial setup asks for **Mistral API key** and **collection name**. The **destination folder** is the project name (`pyproject.toml`, README, Vespa container). Ports default to `18080` / `19072` in `.env`.

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
| (destination path) | Project name = folder you pass to `copier copy`  |
| `mistral_api_key`  | Mistral API key (written to `.env`, git-ignored)   |
| `collection_name`  | Vespa collection / schema name                   |

Generated `.env` also sets default Vespa ports and `WORKSPACE_ROOT=.`.
