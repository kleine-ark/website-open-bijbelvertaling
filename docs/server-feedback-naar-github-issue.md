# Vers-opmerkingen → GitHub-issue (server-side, via token)

De bezoeker stuurt een opmerking via de site (POST naar `/api/feedback`). De
**server** maakt daarvan automatisch een GitHub-issue aan met een token. De
bezoeker heeft **geen** GitHub-account nodig en ziet GitHub niet.

> De client (`js/feedback.js`) POST't alleen een JSON-payload naar
> `/api/feedback`. Onderstaande code voeg je toe aan je `server.py` op de
> productieserver (openvertaling.nl). Het token blijft server-side — nooit in de
> browser.

## 1. Maak een GitHub Personal Access Token

- GitHub → Settings → Developer settings → **Fine-grained tokens** → *Generate new token*.
- Repository access: alleen `kleine-ark/website-open-bijbelvertaling`.
- Permissions → Repository → **Issues: Read and write**.
- Kopieer het token (begint met `github_pat_…`).

## 2. Zet het token als omgevingsvariabele op de server

```bash
# bijv. in /etc/environment, een systemd unit, of het start-script van server.py
export OSV_GITHUB_TOKEN="github_pat_xxxxxxxxxxxxxxxx"
```

## 3. Voeg dit toe aan server.py

```python
import os
import json
import urllib.request

GITHUB_REPO = "kleine-ark/website-open-bijbelvertaling"
GITHUB_TOKEN = os.environ.get("OSV_GITHUB_TOKEN", "")

def create_github_issue(payload: dict) -> bool:
    """Maak een GitHub-issue van een vers-opmerking. Retourneert True bij succes."""
    if not GITHUB_TOKEN:
        return False
    ref = payload.get("ref", "onbekend vers")
    title = f"Vers-opmerking: {ref}"
    body = (
        f"**Vers:** {ref}\n\n"
        f"**Geselecteerde tekst:**\n> {payload.get('selected') or '(geen selectie)'}\n\n"
        f"**Opmerking / suggestie:**\n{payload.get('suggestion', '')}\n\n"
        f"---\n"
        f"_Ingezonden via openvertaling.nl"
        + (f" door {payload['user']['name']}" if payload.get('user', {}).get('name') and payload['user']['name'] != 'anoniem' else "")
        + "_"
    )
    data = json.dumps({"title": title, "body": body, "labels": ["vers-opmerking"]}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GITHUB_REPO}/issues",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "openvertaling-feedback",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except Exception as e:
        print(f"[feedback] GitHub-issue mislukt: {e}")
        return False
```

Roep `create_github_issue(payload)` aan in je bestaande `/api/feedback`-handler
(naast of in plaats van de mail). Geef in de JSON-respons bijv. terug:

```python
ok = create_github_issue(payload)
return {"issue": ok}   # de client toont "Bedankt! Je opmerking is verstuurd."
```

## Waarom niet client-side?

Een token in de browser-JS is voor iedereen zichtbaar → misbruik/spam. Daarom
moet de issue-aanmaak op de server gebeuren. De static site (`js/feedback.js`)
doet alleen de POST; de server houdt het geheim.
