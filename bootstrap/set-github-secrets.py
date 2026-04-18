#!/usr/bin/env python3
"""
set-github-secrets.py  (RentalApp)
====================================
Sets GitHub Actions secrets for the RentalApp-Build repo.

All sensitive values are fetched from Azure Key Vault — nothing sensitive
lives in bootstrap/.env or shell history.

KV secrets read from techwizard-plt-kv:
  github-pat            → GITHUB_PAT (used to push secrets, not pushed itself)
  azure-client-id       → AZURE_CLIENT_ID
  azure-tenant-id       → AZURE_TENANT_ID
  azure-subscription-id → AZURE_SUBSCRIPTION_ID
  dockerhub-token       → DOCKERHUB_TOKEN
  sonar-token           → SONAR_TOKEN  (optional)

Non-sensitive values read from bootstrap/.env:
  GITHUB_ORG, GITHUB_REPO, PLATFORM_KV_NAME
  DOCKERHUB_USERNAME, SONAR_HOST_URL

Usage:
  az login
  python bootstrap/set-github-secrets.py
  python bootstrap/set-github-secrets.py --dry-run
  python bootstrap/set-github-secrets.py --list

Prerequisites:
  pip install requests pynacl
  az login  (needs Key Vault Secrets User role on techwizard-plt-kv)
"""

import argparse
import base64
import getpass
import re
import subprocess
import sys
from pathlib import Path

import requests
from nacl import encoding, public


# ── Key Vault helper ──────────────────────────────────────────────────────────
def kv_get_secret(vault_name: str, secret_name: str) -> str:
    """Fetch a secret from Azure Key Vault via az CLI. Returns empty string on failure."""
    if not vault_name:
        return ""
    try:
        az_cmd = "az.cmd" if sys.platform == "win32" else "az"
        result = subprocess.run(
            [az_cmd, "keyvault", "secret", "show",
             "--vault-name", vault_name,
             "--name", secret_name,
             "--query", "value", "-o", "tsv"],
            capture_output=True, text=True, timeout=15,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


# ── .env loader ───────────────────────────────────────────────────────────────
def load_env(env_path: Path) -> dict:
    """Parse a .env file — strips quotes, skips comments and blank lines."""
    if not env_path.exists():
        return {}
    env = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        m = re.match(r'^["\'](.*)["\']$', val)
        if m:
            val = m.group(1)
        if key and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            env[key] = val
    return env


# ── GitHub API helpers ────────────────────────────────────────────────────────
def auth_headers(token: str) -> dict:
    return {
        "Authorization":        f"Bearer {token}",
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_public_key(owner: str, repo: str, token: str) -> dict:
    url  = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    resp = requests.get(url, headers=auth_headers(token), timeout=15)
    resp.raise_for_status()
    return resp.json()


def list_existing_secrets(owner: str, repo: str, token: str) -> list[str]:
    url    = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets"
    names  = []
    params = {"per_page": 100, "page": 1}
    while True:
        resp = requests.get(url, headers=auth_headers(token), params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        names += [s["name"] for s in data.get("secrets", [])]
        if len(data.get("secrets", [])) < 100:
            break
        params["page"] += 1
    return sorted(names)


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    pub_key    = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(pub_key)
    encrypted  = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def set_secret(owner: str, repo: str, token: str,
               name: str, value: str, key_id: str, key: str,
               dry_run: bool = False) -> bool:
    if dry_run:
        print(f"  [dry-run]  {name}")
        return True
    encrypted = encrypt_secret(key, value)
    url       = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{name}"
    resp      = requests.put(
        url,
        headers=auth_headers(token),
        json={"encrypted_value": encrypted, "key_id": key_id},
        timeout=15,
    )
    ok = resp.status_code in (201, 204)
    print(f"  {'✔' if ok else '✘'}  {name}" + (f"  [{resp.status_code}]" if not ok else ""))
    return ok


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Push GitHub Actions secrets to RentalApp-Build repo from Key Vault."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be set without making any changes")
    parser.add_argument("--list", action="store_true",
                        help="List existing secret names in the repo (no values shown)")
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()

    env_file = Path(__file__).parent / ".env"
    env      = load_env(env_file)

    owner    = env.get("GITHUB_ORG",  "techwizard-platformlab")
    repo     = env.get("GITHUB_REPO", "RentalApp-Build")
    kv_name  = env.get("PLATFORM_KV_NAME", "techwizard-plt-kv")

    print(f"Platform Key Vault: {kv_name}")
    print(f"Target repo:        {owner}/{repo}")
    print()

    # ── Fetch secrets from Key Vault ─────────────────────────────────────────
    print("Fetching secrets from Key Vault...")
    client_id       = kv_get_secret(kv_name, "azure-client-id")
    tenant_id       = kv_get_secret(kv_name, "azure-tenant-id")
    subscription_id = kv_get_secret(kv_name, "azure-subscription-id")
    dockerhub_token = kv_get_secret(kv_name, "dockerhub-token")
    sonar_token     = kv_get_secret(kv_name, "sonar-token")

    # Non-sensitive values from .env
    dockerhub_user = env.get("DOCKERHUB_USERNAME", "")
    sonar_host     = env.get("SONAR_HOST_URL", "")

    # ── Build secret map ─────────────────────────────────────────────────────
    secret_map = {
        # Azure OIDC auth
        "AZURE_CLIENT_ID":       client_id,
        "AZURE_TENANT_ID":       tenant_id,
        "AZURE_SUBSCRIPTION_ID": subscription_id,
        # Docker Hub
        "DOCKERHUB_USERNAME":    dockerhub_user,
        "DOCKERHUB_TOKEN":       dockerhub_token,
        # SonarQube (optional)
        "SONAR_TOKEN":           sonar_token,
        "SONAR_HOST_URL":        sonar_host,
        # NOTE: ACR_NAME / ACR_LOGIN_SERVER are NOT static secrets.
        # The build workflow fetches acr-login-server from Key Vault at runtime
        # after Terraform apply writes it there.
    }

    # Drop empty values
    secrets = {k: v for k, v in secret_map.items() if v and "<" not in v}

    # ── PAT: KV → interactive prompt ─────────────────────────────────────────
    token = kv_get_secret(kv_name, "github-pat")
    if token:
        print("  ✔  GITHUB_PAT loaded from Key Vault")
    else:
        print("  ⚠  github-pat not found in Key Vault — falling back to prompt")
        print()
        token = getpass.getpass("GitHub PAT (repo scope): ").strip()

    if not token:
        print("ERROR: No token provided. Exiting.")
        sys.exit(1)

    # ── List mode ─────────────────────────────────────────────────────────────
    if args.list:
        print(f"\n{'='*60}")
        print(f"  {owner}/{repo}  — existing secrets")
        print(f"{'='*60}")
        try:
            for n in list_existing_secrets(owner, repo, token):
                print(f"  •  {n}")
        except requests.HTTPError as e:
            print(f"  ERROR: {e}")
        print(f"\n  Manage at: https://github.com/{owner}/{repo}/settings/secrets/actions")
        return

    # ── Push ──────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  {owner}/{repo}{'  [DRY RUN]' if args.dry_run else ''}")
    print(f"{'='*60}")
    print(f"  Secrets to push: {len(secrets)}")
    print()

    if not args.dry_run:
        print("  Fetching repo public key...")
        try:
            pub_key_data = get_public_key(owner, repo, token)
        except requests.HTTPError as e:
            print(f"  ERROR: could not fetch public key — {e}")
            sys.exit(1)
        key_id = pub_key_data["key_id"]
        key    = pub_key_data["key"]
    else:
        key_id = key = ""

    for name, value in secrets.items():
        set_secret(owner, repo, token, name, value, key_id, key, dry_run=args.dry_run)

    print()
    if not args.dry_run:
        missing = {"AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID"} - set(secrets)
        if missing:
            print(f"  ⚠  Missing required secrets (check KV entries): {', '.join(sorted(missing))}")
        print(f"  Verify at: https://github.com/{owner}/{repo}/settings/secrets/actions")
    print("\nDone.")


if __name__ == "__main__":
    main()
