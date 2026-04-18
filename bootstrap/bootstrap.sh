#!/usr/bin/env bash
# =============================================================================
# RentalApp — App Bootstrap Script
#
# Adds GitHub Actions OIDC federated credentials to the platform Managed Identity
# so that RentalApp-Build can authenticate with Azure and push to ACR.
# =============================================================================
set -euo pipefail

# Disable Git Bash path conversion
export MSYS_NO_PATHCONV=1

# ── Colours ────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RESET='\033[0m'

info()    { echo -e "${CYAN}==>${RESET} $*"; }
success() { echo -e "${GREEN}✔${RESET}  $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET}  $*"; }
error()   { echo -e "${RED}✘${RESET}  $*" >&2; }

# ── Load .env ──────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  error ".env not found at $ENV_FILE"
  exit 1
fi

while IFS= read -r line; do
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
  [[ "$line" != *"="* ]] && continue
  key="${line%%=*}"
  val="${line#*=}"
  export "$key=$val"
done < "$ENV_FILE"

ORG="${GITHUB_ORG:-techwizard-platformlab}"
REPO="${GITHUB_REPO:-RentalApp-Build}"
IDENTITY_NAME="automation-identity"
PLATFORM_RG="techwizard-platformlab-apps"

info "Verifying Azure login..."
if ! az account show >/dev/null 2>&1; then
  error "Not logged in to Azure CLI. Run: az login"
  exit 1
fi
success "Azure login OK."

info "Adding OIDC credentials for $ORG/$REPO to $IDENTITY_NAME..."

_add_federated_credential() {
  local fc_name="$1"
  local subject="$2"

  local existing
  existing=$(az identity federated-credential list \
    --identity-name "$IDENTITY_NAME" \
    --resource-group "$PLATFORM_RG" \
    --query "[?name=='${fc_name}'].name" \
    -o tsv 2>/dev/null || true)

  if [[ -n "$existing" ]]; then
    success "Federated credential already exists: $fc_name (skipping)"
    return 0
  fi

  if az identity federated-credential create \
      --identity-name   "$IDENTITY_NAME" \
      --resource-group  "$PLATFORM_RG" \
      --name            "$fc_name" \
      --issuer          "https://token.actions.githubusercontent.com" \
      --subject         "$subject" \
      --audiences       "api://AzureADTokenExchange" >/dev/null 2>&1; then
    success "Federated credential added: $fc_name"
  else
    warn "Could not add $fc_name"
  fi
}

_add_federated_credential "github-${REPO}-main" "repo:${ORG}/${REPO}:ref:refs/heads/main"
_add_federated_credential "github-${REPO}-pr" "repo:${ORG}/${REPO}:pull_request"

echo ""
success "App bootstrap complete. You can now use set-github-secrets.py to push secrets."
