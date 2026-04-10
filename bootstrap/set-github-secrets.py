#!/usr/bin/env python3
"""
set-github-secrets.py  (RentalApp)
====================================
Sets GitHub Actions secrets for the RentalApp repo.

Secrets set
-----------
  From AI-RentalApp-Ledger/bootstrap/.env  (auto-detected):
    AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID,
    AZURE_SUBSCRIPTION_ID

  From bootstrap/.env  (local, required):
    ACR_NAME, ACR_LOGIN_SERVER
    DOCKERHUB_USERNAME, DOCKERHUB_TOKEN
    SONAR_TOKEN, SONAR_HOST_URL  (optional)
    GCP_PROJECT_ID, GCP_SERVICE_ACCOUNT, GCR_REGION (optional)
    GCP_WORKLOAD_IDENTITY_PROVIDER (optional)

Usage
-----
  cd RentalApp
  cp bootstrap/.env.example bootstrap/.env   # fill in values
  pip install -r bootstrap/requirements.txt
  python bootstrap/set-github-secrets.py
"""

import base64
import getpass
import re
import sys
from pathlib import Path

import requests
from nacl import encoding, public


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
        m = re.match(r'^["\'](.+)["\']$', val)
        if m:
            val = m.group(1)
        if key:
            env[key] = val
    return env


def find_platform_env() -> Path | None:
    """
    Walk up from this script's location looking for
    AI-RentalApp-Ledger/bootstrap/.env
    Tries common relative paths so the script works regardless of where
    both repos are cloned.
    """
    script_dir = Path(__file__).resolve().parent   # RentalApp/bootstrap/
    candidates = [
        script_dir.parent.parent / "AI-RentalApp-Ledger" / "bootstrap" / ".env",
        script_dir.parent.parent / "AI-RentalApp-Ledger-App" / "bootstrap" / ".env",
        script_dir.parent.parent.parent / "AI-RentalApp-Ledger" / "bootstrap" / ".env",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


# ── GitHub API helpers ────────────────────────────────────────────────────────

def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_public_key(owner: str, repo: str, token: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    resp = requests.get(url, headers=auth_headers(token), timeout=15)
    resp.raise_for_status()
    return resp.json()


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    pub_key = public.PublicKey(
        public_key_b64.encode("utf-8"), encoding.Base64Encoder()
    )
    sealed_box = public.SealedBox(pub_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def set_secret(
    owner: str, repo: str, token: str,
    name: str, value: str,
    key_id: str, key: str,
) -> None:
    encrypted = encrypt_secret(key, value)
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{name}"
    resp = requests.put(
        url,
        headers=auth_headers(token),
        json={"encrypted_value": encrypted, "key_id": key_id},
        timeout=15,
    )
    if resp.status_code in (201, 204):
        print(f"  [OK]   {name}")
    else:
        print(f"  [FAIL] {name}  ->  HTTP {resp.status_code}: {resp.text}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    local_env_path = Path(__file__).parent / ".env"

    # Load local bootstrap/.env (required)
    if not local_env_path.exists():
        print(f"ERROR: {local_env_path} not found.")
        print("  cp bootstrap/.env.example bootstrap/.env  and fill in your values.")
        sys.exit(1)

    local_env = load_env(local_env_path)

    # Auto-detect platform .env and merge (platform values are used as fallback)
    platform_env: dict = {}
    platform_path = find_platform_env()
    if platform_path:
        platform_env = load_env(platform_path)
        print(f"  Found platform .env: {platform_path}")
    else:
        print("  Platform .env not auto-detected — using local .env only.")
        print("  (Expected at: ../../AI-RentalApp-Ledger/bootstrap/.env)")

    # Merged: local wins, platform fills in missing keys
    merged = {**platform_env, **local_env}

    # ── Resolve target repo ──────────────────────────────────────────────────
    owner = merged.get("GITHUB_ORG", "").strip()
    repo  = merged.get("GITHUB_REPO", "RentalApp-Build").strip()

    if not owner:
        print("ERROR: GITHUB_ORG not set in bootstrap/.env")
        sys.exit(1)

    # ── Resolve ACR login server ─────────────────────────────────────────────
    acr_login_server = merged.get("ACR_LOGIN_SERVER", "").strip()
    acr_name         = merged.get("ACR_NAME", "").strip()

    # Derive ACR_LOGIN_SERVER from ACR_NAME if not explicitly set
    if not acr_login_server and acr_name:
        acr_login_server = f"{acr_name}.azurecr.io"

    # ── Build secrets map ────────────────────────────────────────────────────
    secret_map = {
        # Azure (from platform .env or local)
        "AZURE_CLIENT_ID":        merged.get("AZURE_APP_ID", merged.get("AZURE_CLIENT_ID", "")),
        "AZURE_CLIENT_SECRET":    merged.get("AZURE_CLIENT_SECRET", ""),
        "AZURE_TENANT_ID":        merged.get("AZURE_TENANT_ID", ""),
        "AZURE_SUBSCRIPTION_ID":  merged.get("AZURE_SUBSCRIPTION_ID", ""),

        # ACR (from local .env)
        "ACR_NAME":               acr_name,
        "ACR_LOGIN_SERVER":       acr_login_server,

        # GCP (from local .env or platform)
        "GCP_PROJECT_ID":                 merged.get("GCP_PROJECT_ID", ""),
        "GCP_SERVICE_ACCOUNT":            merged.get("GCP_SERVICE_ACCOUNT", ""),
        "GCR_REGION":                     merged.get("GCR_REGION", ""),
        "GCP_WORKLOAD_IDENTITY_PROVIDER": merged.get("GCP_WORKLOAD_IDENTITY_PROVIDER", ""),

        # Docker Hub (from local .env)
        "DOCKERHUB_USERNAME":     merged.get("DOCKERHUB_USERNAME", ""),
        "DOCKERHUB_TOKEN":        merged.get("DOCKERHUB_TOKEN", ""),

        # SonarQube — optional
        "SONAR_TOKEN":            merged.get("SONAR_TOKEN", ""),
        "SONAR_HOST_URL":         merged.get("SONAR_HOST_URL", ""),
    }

    # Drop empty / placeholder values
    secrets = {
        k: v for k, v in secret_map.items()
        if v and "<" not in v
    }

    # ── Print plan ───────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"  Setting GitHub Secrets -> {owner}/{repo}")
    print("=" * 60)
    print(f"  Secrets to set ({len(secrets)}):")
    for k in secrets:
        display = secrets[k][:4] + "****" if len(secrets[k]) > 4 else "****"
        print(f"    {k:<30} {display}")
    print()

    # ── PAT ─────────────────────────────────────────────────────────────────
    token = merged.get("GITHUB_PAT", "").strip()
    if not token:
        print("Enter your GitHub Personal Access Token (PAT).")
        print("Needs 'repo' scope (classic token) or 'secrets:write' (fine-grained).")
        print("Create at: https://github.com/settings/tokens/new")
        print()
        token = getpass.getpass("PAT: ").strip()
    if not token:
        print("No token provided. Exiting.")
        sys.exit(1)

    # ── Fetch repo public key ─────────────────────────────────────────────
    print("Fetching repo public key...")
    try:
        pub_key_data = get_public_key(owner, repo, token)
    except requests.HTTPError as exc:
        print(f"Failed to fetch public key: {exc}")
        print("Check: PAT has 'repo' scope, repo name is correct, you have admin access.")
        sys.exit(1)

    key_id = pub_key_data["key_id"]
    key    = pub_key_data["key"]
    print(f"Public key fetched (key_id: {key_id})")
    print()

    # ── Set secrets ──────────────────────────────────────────────────────
    print("Setting secrets:")
    for name, value in secrets.items():
        set_secret(owner, repo, token, name, value, key_id, key)

    print()
    print("Done!")
    print(f"Verify at: https://github.com/{owner}/{repo}/settings/secrets/actions")


if __name__ == "__main__":
    main()
