"""Trigger the search ingestion workflow from the command line.

Builds ``IngestDocumentsInput`` (router name + document refs) from a local file or
directory path and executes the ``search-ingest-documents`` workflow via the Mistral
Workflows API.
"""
# ruff: noqa: E402

import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from mistralai.extra.workflows import WorkflowEncodingConfig, configure_workflow_encoding
from mistralai.workflows.client import get_mistral_client
from mistralai.workflows.plugins.search import DocumentRef


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trigger the search ingestion workflow."
    )
    parser.add_argument(
        "--workflow",
        default="search-ingest-documents",
        help="Workflow name (default: search-ingest-documents)",
    )
    parser.add_argument(
        "--router-name",
        default="default",
        help="Router registered on the worker (default: default)",
    )
    parser.add_argument(
        "--file-path",
        default="sample_data/hello.txt",
        help="Local path to a file or directory to ingest",
    )
    return parser.parse_args()


def _collect_refs(file_path: str) -> list[DocumentRef]:
    """Walk a file or directory and return ``DocumentRef`` objects."""
    root = Path(file_path)
    if not root.exists():
        raise SystemExit(f"Error: path not found: {root}")
    if root.is_file():
        paths = [root]
    else:
        paths = sorted(p for p in root.rglob("*") if p.is_file())
        if not paths:
            raise SystemExit(f"Error: no files found under {root}")
    return [DocumentRef(path=str(p), name=p.name) for p in paths]


async def main() -> None:
    args = parse_args()

    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        raise SystemExit("Error: MISTRAL_API_KEY is not set. Check your .env file.")

    deployment_name = os.environ.get("DEPLOYMENT_NAME")
    if not deployment_name:
        raise SystemExit(
            "Error: DEPLOYMENT_NAME is not set. Add it to your .env file, e.g.:\n"
            "  DEPLOYMENT_NAME=my-search-project"
        )

    refs = _collect_refs(args.file_path)
    raw_input = {
        "router_name": args.router_name,
        "refs": [ref.model_dump() for ref in refs],
    }

    client = get_mistral_client(
        api_key=api_key,
        server_url=os.environ.get("MISTRAL_API_URL", "https://api.mistral.ai"),
    )

    await configure_workflow_encoding(WorkflowEncodingConfig(), client=client)

    try:
        result = await client.workflows.execute_workflow_and_wait_async(
            workflow_identifier=args.workflow,
            input=raw_input,
            deployment_name=deployment_name,
        )
    except Exception as exc:
        if "Workflow not found" in str(exc) or "404" in str(exc):
            raise SystemExit(
                f"Error: workflow '{args.workflow}' not found.\n"
                "Start the examples worker first (separate terminal):\n"
                "  make start-examples\n"
                "Then retry this command."
            ) from exc
        raise

    print(f"Result: {json.dumps(result, default=str)}")


if __name__ == "__main__":
    asyncio.run(main())
