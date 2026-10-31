#!/usr/bin/env bash
# Construit et publie les images backend et frontend sur Docker Hub (amd64 + arm64).
#
# Usage :
#   ./scripts/publier-images.sh            # auto : incrémente le patch depuis Docker Hub
#   ./scripts/publier-images.sh 1.2.0      # version explicite X.Y.Z
#
# Tags produits : cuzub/pharma:backend-X.Y.Z et cuzub/pharma:frontend-X.Y.Z (+ -latest).
# Un tag git local vX.Y.Z est créé après publication (non poussé).

set -euo pipefail

DOCKERHUB_REPO="${DOCKERHUB_REPO:-cuzub/pharma}"
PLATEFORMES="linux/amd64,linux/arm64"
CONSTRUIRE_BASE_PATH="/pharmacie/"
BUILDER="pharma-builder"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "Erreur : l'arbre git contient des modifications non commitées. Commitez avant de publier." >&2
  exit 1
fi

# Liste les versions X.Y.Z déjà publiées (backend-* et frontend-*) sur Docker Hub.
versions_publiees() {
  local url="https://hub.docker.com/v2/repositories/${DOCKERHUB_REPO}/tags?page_size=100"
  curl -fsSL "$url" 2>/dev/null \
    | grep -oE '"name":"(backend|frontend)-[0-9]+\.[0-9]+\.[0-9]+"' \
    | sed -E 's/"name":"(backend|frontend)-([^"]+)"/\2/' \
    | sort -t. -k1,1n -k2,2n -k3,3n -u || true
}

if [ -n "${1:-}" ]; then
  VERSION="$1"
else
  derniere="$(versions_publiees | tail -n 1)"
  if [ -z "$derniere" ]; then
    VERSION="1.0.0"
  else
    IFS=. read -r maj min pat <<< "$derniere"
    VERSION="${maj}.${min}.$((pat + 1))"
  fi
fi

if ! printf '%s' "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Erreur : version invalide '$VERSION' (attendu X.Y.Z)." >&2
  exit 1
fi

if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
  echo "Erreur : le tag git v${VERSION} existe déjà." >&2
  exit 1
fi

COMMIT="$(git rev-parse --short HEAD)"
echo "Publication de la version ${VERSION} (commit ${COMMIT}) vers ${DOCKERHUB_REPO}"

if ! docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  docker buildx create --name "$BUILDER" --driver docker-container >/dev/null
fi
docker buildx inspect "$BUILDER" --bootstrap >/dev/null

docker buildx build \
  --builder "$BUILDER" \
  --platform "$PLATEFORMES" \
  --build-arg "APP_VERSION=${VERSION}" \
  --tag "${DOCKERHUB_REPO}:backend-${VERSION}" \
  --tag "${DOCKERHUB_REPO}:backend-latest" \
  --push \
  backend

docker buildx build \
  --builder "$BUILDER" \
  --platform "$PLATEFORMES" \
  --build-arg "VITE_BASE_PATH=${CONSTRUIRE_BASE_PATH}" \
  --tag "${DOCKERHUB_REPO}:frontend-${VERSION}" \
  --tag "${DOCKERHUB_REPO}:frontend-latest" \
  --push \
  frontend

git tag -a "v${VERSION}" -m "Version ${VERSION}"

echo "Publié : ${DOCKERHUB_REPO}:backend-${VERSION} et ${DOCKERHUB_REPO}:frontend-${VERSION}"
echo "Tag git local créé : v${VERSION} (non poussé)"
