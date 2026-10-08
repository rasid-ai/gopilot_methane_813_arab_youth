"""Where the repository is, and whether GoPilot flies live (credentials found) or replays recordings."""

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # src/gopilot813/config.py -> the repository root
IN_COLAB = "google.colab" in sys.modules


def _creds_file():
    values, f = {}, REPO / "creds.env"
    if f.exists():
        for line in f.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip().strip("\"'")
    return values


def _real(v):
    return bool(v) and not v.startswith("<") and "PASTE" not in v.upper()


def _secret(name, from_file):
    # creds.env first, then environment variables, then Colab Secrets. Placeholders count as missing.
    for source in (lambda: from_file.get(name), lambda: os.environ.get(name), lambda: _colab_secret(name)):
        v = source()
        if _real(v):
            return v
    return None


def _colab_secret(name):
    if not IN_COLAB:
        return None
    try:
        from google.colab import userdata
        return userdata.get(name)
    except Exception:
        return None


_from_file = _creds_file()
AWS_ACCESS_KEY_ID = _secret("AWS_ACCESS_KEY_ID", _from_file)
AWS_SECRET_ACCESS_KEY = _secret("AWS_SECRET_ACCESS_KEY", _from_file)
GOPILOT_AGENT_ARN = _secret("GOPILOT_AGENT_ARN", _from_file)
GOPILOT_REGION = _secret("GOPILOT_REGION", _from_file) or (GOPILOT_AGENT_ARN.split(":")[3] if GOPILOT_AGENT_ARN else "eu-central-1")
MODE = "live" if (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and GOPILOT_AGENT_ARN) else "replay"
BANNER = ("🟢 LIVE: each mission calls GoPilot now." if MODE == "live" else
          "🔁 REPLAY: no credentials found, so each mission replays our recorded GoPilot run from results/. "
          "Fill creds.env to fly the missions live.")
