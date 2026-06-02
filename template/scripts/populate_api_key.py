#!/usr/bin/env python3
"""Write MISTRAL_API_KEY from the shell into .env (run via `make installdeps`)."""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        return

    env_path = Path(".env")
    if not env_path.exists():
        return

    lines: list[str] = []
    for line in env_path.read_text().splitlines():
        if line.startswith("MISTRAL_API_KEY="):
            lines.append(f"MISTRAL_API_KEY={api_key}")
        else:
            lines.append(line)
    env_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
