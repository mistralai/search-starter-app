import os
from pathlib import Path

from mistralai.search.toolkit.plugins.vespa import VespaApp

app = VespaApp(Path(__file__).parent)


def vespa_endpoint() -> str:
    """Query API URL from VESPA_QUERY_PORT (or optional VESPA_ENDPOINT override)."""
    if url := os.environ.get("VESPA_ENDPOINT"):
        return url
    port = os.environ.get("VESPA_QUERY_PORT", "18080")
    return f"http://localhost:{port}"
