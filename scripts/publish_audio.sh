#!/usr/bin/env bash
# Publiceer expliciet gekozen audio-uitvoer naar de externe assetserver.
set -euo pipefail

if (( $# == 0 )); then
    echo "Gebruik: $0 audio/pad [audio/pad ...]" >&2
    exit 2
fi

for tool in git realpath rsync ssh; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Vereist programma ontbreekt: $tool" >&2
        exit 1
    fi
done

PROJECT_ROOT=$(git rev-parse --show-toplevel)
REMOTE_TARGET=${OV_ASSET_SSH_TARGET:-root@kleineark.com}
REMOTE_ROOT=${OV_ASSET_REMOTE_ROOT:-/srv/openvertaling/assets}

if [[ "$REMOTE_ROOT" != /* || "$REMOTE_ROOT" == / ]]; then
    echo "OV_ASSET_REMOTE_ROOT moet een specifieke absolute map zijn." >&2
    exit 1
fi

cd "$PROJECT_ROOT"
paths=()
for requested in "$@"; do
    relative=$(realpath --canonicalize-existing --relative-to="$PROJECT_ROOT" "$requested")
    case "$relative" in
        audio/*) ;;
        *)
            echo "Alleen paden binnen audio/ kunnen worden gepubliceerd: $requested" >&2
            exit 1
            ;;
    esac
    paths+=("./$relative")
done

printf -v quoted_remote_root '%q' "$REMOTE_ROOT"
ssh "$REMOTE_TARGET" "install -d -m 0755 -- $quoted_remote_root/audio"

rsync -aR --partial --human-readable --info=progress2 \
    --exclude='*.log' \
    "${paths[@]}" \
    "$REMOTE_TARGET:$REMOTE_ROOT/"

differences=$(rsync -acnR --exclude='*.log' "${paths[@]}" "$REMOTE_TARGET:$REMOTE_ROOT/")
if [[ -n "$differences" ]]; then
    echo "Controle na publicatie vond afwijkingen:" >&2
    echo "$differences" >&2
    exit 1
fi

echo "Audio gepubliceerd en met checksums gecontroleerd."
