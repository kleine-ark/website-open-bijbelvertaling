#!/usr/bin/env bash
set -euo pipefail

if (( $# != 1 )); then
    echo "Gebruik: $0 MAP_MET_SERVERBESTANDEN" >&2
    exit 2
fi

SOURCE_DIR=$1
NGINX_SITE=${OV_NGINX_SITE:-/etc/nginx/sites-available/openvertaling.nl}
INCLUDE_LINE='    include /etc/nginx/snippets/openvertaling-collaboration.conf;'

for tool in curl install nginx python3 systemctl; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "Vereist programma ontbreekt: $tool" >&2
        exit 1
    }
done
python3 -c 'import cryptography'
for file in collaboration_api.py openvertaling-collaboration.service openvertaling-collaboration.nginx; do
    test -f "$SOURCE_DIR/$file" || {
        echo "Installatiebestand ontbreekt: $file" >&2
        exit 1
    }
done
test -f "$NGINX_SITE"

install -d -m 0755 /opt/openvertaling-collaboration
install -m 0644 "$SOURCE_DIR/collaboration_api.py" /opt/openvertaling-collaboration/collaboration_api.py
install -d -o www-data -g www-data -m 0700 /var/lib/openvertaling-collaboration
install -m 0644 "$SOURCE_DIR/openvertaling-collaboration.service" /etc/systemd/system/openvertaling-collaboration.service
install -m 0644 "$SOURCE_DIR/openvertaling-collaboration.nginx" /etc/nginx/snippets/openvertaling-collaboration.conf

SITE_BACKUP=$(mktemp)
cp -- "$NGINX_SITE" "$SITE_BACKUP"
site_changed=false
rollback() {
    if [[ "$site_changed" == true ]]; then
        install -m 0644 "$SITE_BACKUP" "$NGINX_SITE"
        nginx -t >/dev/null 2>&1 && systemctl reload nginx
    fi
    unlink -- "$SITE_BACKUP"
}
trap rollback ERR

if ! grep -Fqx "$INCLUDE_LINE" "$NGINX_SITE"; then
    python3 - "$NGINX_SITE" "$INCLUDE_LINE" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
include = sys.argv[2]
text = path.read_text(encoding="utf-8")
marker = "    location / {"
if text.count(marker) != 1:
    raise SystemExit("Nginx-site bevat niet exact één primaire location")
path.write_text(text.replace(marker, include + "\n\n" + marker), encoding="utf-8")
PY
    site_changed=true
fi

systemctl daemon-reload
systemctl enable --now openvertaling-collaboration.service
systemctl restart openvertaling-collaboration.service
nginx -t
systemctl reload nginx
curl --fail --silent --show-error http://127.0.0.1:8787/api/collaboration/health >/dev/null

trap - ERR
unlink -- "$SITE_BACKUP"
echo "Collaboration API geïnstalleerd en gecontroleerd."
