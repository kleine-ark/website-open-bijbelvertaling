#!/bin/bash
# Volledige sync van GitHub → Dropbox (waar localhost:8888 vandaan serveert).
# Voor elke commit: git push && ./sync-dropbox.sh
set -e
SRC="/home/maarten/Documents/GitHub/website-open-bijbelvertaling"
DST="/home/maarten/3BM Dropbox/Maarten Vroegindeweij/de kleine ark/Projecten/19 Open Vertaling"
rsync -av --delete \
    --exclude='.git' --exclude='node_modules' --exclude='.venv*' \
    --exclude='__pycache__' --exclude='scripts/' \
    --exclude='*.pyc' --exclude='.DS_Store' \
    "$SRC/" "$DST/" | tail -10
echo "✅ Dropbox in sync met GitHub"
