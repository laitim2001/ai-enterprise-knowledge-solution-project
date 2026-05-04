"""Create / get / delete Azure AI Search index via REST (stdlib only).

Stdlib-only path (no `azure-search-documents` SDK) per C03 design note,
to bypass Ricoh corp proxy block on PyPI wheels (RISK_REGISTER R8).

Usage:
    python -m scripts.create_index create [--schema PATH] [--name NAME]
    python -m scripts.create_index get    [--name NAME]
    python -m scripts.create_index delete [--name NAME]

Env (loaded from project-root .env if python-dotenv installed,
otherwise must be set in shell):
    AZURE_SEARCH_ENDPOINT     e.g. https://azureaisearchtesting.search.windows.net
    AZURE_SEARCH_ADMIN_KEY    admin key

Refs:
    docs/architecture.md §3.6 (index schema)
    docs/02-architecture/components/C03-indexing.md
"""

from __future__ import annotations

# Use OS trust store (Windows Cert Store) for TLS verification so Ricoh corp
# proxy SSL inspection is honoured. Must run before urllib import (urllib uses
# stdlib ssl module, which truststore patches).
import truststore

truststore.inject_into_ssl()

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_VERSION = "2024-07-01"
DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "backend" / "indexing" / "schema.json"
)
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env_file(path: Path) -> None:
    """Minimal .env loader (no python-dotenv dep). Skips comments + blank lines."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_endpoint_and_key() -> tuple[str, str]:
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT", "").rstrip("/")
    key = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "")
    if not endpoint or not key:
        sys.exit(
            "ERROR: AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_ADMIN_KEY must be set "
            "(via .env at project root or shell environment)."
        )
    return endpoint, key


def request_json(
    method: str, url: str, key: str, payload: dict | None = None
) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "api-key": key,
            "Accept": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def cmd_create(args: argparse.Namespace) -> int:
    endpoint, key = get_endpoint_and_key()
    schema_path = Path(args.schema) if args.schema else DEFAULT_SCHEMA_PATH
    if not schema_path.is_file():
        sys.exit(f"ERROR: schema file not found: {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    name = args.name or schema["name"]
    schema["name"] = name

    url = f"{endpoint}/indexes/{name}?api-version={API_VERSION}"
    status, body = request_json("PUT", url, key, schema)
    print(f"PUT {url}")
    print(f"-> {status}")
    # Azure AI Search returns 201 on create-new, 204 on in-place update;
    # 200 retained for forward compatibility.
    if status in (200, 201, 204):
        print(f"OK: index '{name}' created/updated.")
        return 0
    print(f"FAILED:\n{body}")
    return 1


def cmd_get(args: argparse.Namespace) -> int:
    endpoint, key = get_endpoint_and_key()
    name = args.name
    url = f"{endpoint}/indexes/{name}?api-version={API_VERSION}"
    status, body = request_json("GET", url, key)
    print(f"GET {url}")
    print(f"-> {status}")
    if status == 200:
        try:
            obj = json.loads(body)
            print(
                json.dumps(
                    {
                        "name": obj.get("name"),
                        "field_count": len(obj.get("fields", [])),
                        "vectorSearch_profiles": [
                            p.get("name")
                            for p in obj.get("vectorSearch", {}).get("profiles", [])
                        ],
                        "semantic_configs": [
                            c.get("name")
                            for c in obj.get("semantic", {}).get("configurations", [])
                        ],
                    },
                    indent=2,
                )
            )
        except json.JSONDecodeError:
            print(body)
        return 0
    print(f"FAILED:\n{body}")
    return 1


def cmd_delete(args: argparse.Namespace) -> int:
    endpoint, key = get_endpoint_and_key()
    name = args.name
    if not args.yes:
        sys.exit("ERROR: refusing destructive delete without --yes flag.")
    url = f"{endpoint}/indexes/{name}?api-version={API_VERSION}"
    status, body = request_json("DELETE", url, key)
    print(f"DELETE {url}")
    print(f"-> {status}")
    if status == 204:
        print(f"OK: index '{name}' deleted.")
        return 0
    print(f"FAILED:\n{body}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="create_index", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    pc = sub.add_parser("create", help="PUT index (create or update)")
    pc.add_argument(
        "--schema", help=f"Path to schema JSON (default: {DEFAULT_SCHEMA_PATH.name})"
    )
    pc.add_argument("--name", help="Override index name from schema file")
    pc.set_defaults(func=cmd_create)

    pg = sub.add_parser("get", help="GET index")
    pg.add_argument("--name", default="ekp-kb-drive-v1")
    pg.set_defaults(func=cmd_get)

    pd = sub.add_parser("delete", help="DELETE index (destructive — requires --yes)")
    pd.add_argument("--name", default="ekp-kb-drive-v1")
    pd.add_argument("--yes", action="store_true", help="Confirm destructive delete")
    pd.set_defaults(func=cmd_delete)

    return p


def main(argv: list[str] | None = None) -> int:
    load_env_file(ENV_PATH)
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
