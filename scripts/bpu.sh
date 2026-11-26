#!/usr/bin/env bash
# Build, push et update du Raspberry Pi en une commande :
#   1. scripts/publier-images.sh : construit et publie les images sur Docker Hub, crée le tag git vX.Y.Z
#   2. scripts/deployer-rpi.sh   : déploie ce tag sur le Raspberry Pi
# Si l'arbre git contient des modifications, elles sont commitées avant la publication, puis la branche est poussée.
#
# Usage :
#   ./scripts/bpu.sh                      # version automatique (patch + 1)
#   ./scripts/bpu.sh 1.2.0                # version explicite X.Y.Z
#   ./scripts/bpu.sh -m "Message" [X.Y.Z] # message du commit (défaut : « Mise à jour »)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

MESSAGE="Mise à jour"
if [ "${1:-}" = "-m" ]; then
  MESSAGE="${2:?Erreur : -m attend un message.}"
  shift 2
fi

if [ -n "$(git status --porcelain)" ]; then
  git status --short
  git add -A
  git commit -m "$MESSAGE"
fi
git push

./scripts/publier-images.sh "$@"
./scripts/deployer-rpi.sh "$@"
