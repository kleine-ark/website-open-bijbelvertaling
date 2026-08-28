"""Gedragsregressie voor geopende pagina's bij een nieuwe inhoudsversie."""

import base64
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def _service_worker_registration_script():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    section = html.split("<!-- Service Worker: offline-cache + instant 2e bezoek -->", 1)[1]
    return re.search(r"<script>(.*?)</script>", section, flags=re.DOTALL).group(1)


def _reloads_after_worker_activation(has_active_controller):
    encoded = base64.b64encode(
        _service_worker_registration_script().encode("utf-8")
    ).decode("ascii")
    script = f"""
const registrationScript = Buffer.from('{encoded}', 'base64').toString('utf8');
let loadHandler;
let updateHandler;
let stateHandler;
let reloads = 0;
const worker = {{
  state: 'installing',
  addEventListener: (name, handler) => {{ if (name === 'statechange') stateHandler = handler; }}
}};
const registration = {{
  installing: worker,
  addEventListener: (name, handler) => {{ if (name === 'updatefound') updateHandler = handler; }}
}};
global.window = {{
  addEventListener: (name, handler) => {{ if (name === 'load') loadHandler = handler; }},
  location: {{ reload: () => {{ reloads += 1; }} }}
}};
Object.defineProperty(global, 'navigator', {{
  configurable: true,
  value: {{
    serviceWorker: {{
      controller: {json.dumps(bool(has_active_controller)).lower()},
      register: async () => registration
    }}
  }}
}});
global.console = {{ info: () => undefined, warn: () => undefined }};
(async () => {{
  eval(registrationScript);
  loadHandler();
  await Promise.resolve();
  updateHandler();
  worker.state = 'activated';
  stateHandler();
  process.stdout.write(String(reloads));
}})();
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return int(result.stdout)


def test_bestaande_lezer_herlaadt_na_nieuwe_workeractivatie():
    assert _reloads_after_worker_activation(has_active_controller=True) == 1


def test_eerste_workerinstallatie_herlaadt_de_lezer_niet_dubbel():
    assert _reloads_after_worker_activation(has_active_controller=False) == 0
