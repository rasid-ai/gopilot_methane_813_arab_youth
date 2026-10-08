"""Builds notebooks/GoPilot_813.ipynb from the cell sources below.

    python tools/build_notebook.py

Cell sources live here as strings, so tools/test_notebook.py runs exactly the code that ships.
"""

import base64
import json
from pathlib import Path

import re

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "GoPilot_813.ipynb"


def _md_spacing(src):
    # A blank line before every list, so any markdown renderer starts the list.
    out = []
    for line in src.split("\n"):
        if re.match(r"\s*(?:[-*]|\d+\.) ", line) and out and out[-1].strip() and \
                not re.match(r"\s*(?:[-*]|\d+\.) |\s{2,}\S", out[-1]):
            out.append("")
        out.append(line)
    return "\n".join(out)


def _lines(src):
    lines = src.strip("\n").split("\n")
    return [l + "\n" for l in lines[:-1]] + [lines[-1]]

# --------------------------------------------------------------------------------------------- story
MD_PROBLEM = r"""<a name="1"></a>
## 🎯 1. The problem, and who it is for

**Methane warms about 80 times more than CO₂ over 20 years**, and a small number of oil and gas point sources
emit a large share of it. Many of those sources are in the Arab region. Finding them still means campaigns,
aircraft or a specialist working through satellite data by hand, site by site.

**Sentinel-2 can see many of them for free**: global coverage every 5 days, with two SWIR bands where methane
absorbs. What has been missing is a model that reads that signal reliably, and a way for a non-specialist to use
it.

**Who uses this:**
- **Operators' LDAR and ESG teams**: find and fix leaks before they become a reporting problem.
- **Regulators and environment agencies**: screen many facilities without a field campaign.
- **MRV and carbon verifiers**: an independent, repeatable check on reported emissions.

With GoPilot the request is one sentence, and the answer is a map.
"""

MD_HERO = r"""# 🛰️ GoPilot × Challenge 813
### Ask in one sentence. Get a methane map back.

**Theme 06, Air Quality & Environmental Intelligence.** Below, GoPilot, our geospatial AI agent, takes a single
request, picks the satellite data, runs **MethaneMapper** (our own methane model), and returns map layers, live
in this notebook. Then it does the same for date palms, solar panels and farm fields.

> 👀 **Just reviewing?** Every cell is saved with its output: scroll and watch.
> ▶️ **Running it?** *Run all* works anywhere: without credentials it **replays** our recorded GoPilot
> missions from `results/`; with `creds.env` filled in, it flies them **live**.
"""

MD_GOPILOT = r"""## 🤖 2. Meet GoPilot

**A geospatial AI agent you talk to.** It plans the job, chooses the data and the models, runs them through 93
tools, and hands back map layers. No GIS, no code.

**Already a product:** live in the browser ([app.rasid.ai](https://app.rasid.ai)), in ArcGIS Pro and QGIS, and as
an API, with paying users. RASID has 11 years of Earth-observation work behind it, and GoPilot has been six
years in the making. 🏆 Winner of the AWS GenAI for Geospatial Challenge 2026 (EMEA).

![GoPilot in one picture](attachment:gopilot_overview.png)
"""

MD_MODEL = r"""## 🧪 3. MethaneMapper, our methane model

**Ours, end to end:** a six-month project that trained a methane detector **only on physically simulated
plumes**, because real labelled plumes are too few to learn from. It finds **75%+ of confirmed real plumes** in
Sentinel-2.

**Why methane, for 813:** it runs on Sentinel-2 today, and the same physics extends to hyperspectral sensors such
as **Satellite 813**, whose hundreds of narrow bands trace the methane absorption directly.

![How MethaneMapper sees methane](attachment:methane_model.png)
"""

MD_SETUP = r"""## 🚀 4. Mission 1: methane at a gas plant in Algeria

The **UTGA gas treatment facility at Tabankourt, Algeria**, where MethaneMapper has recorded a plume of about
3,900 kg/h on 3 January 2024. The request names the site, the date and a small box, so the mission stays short.

First, the three tool cells. They are collapsed: just run them. The first one says whether this run is live or a replay.
"""

MD_MISSION = r"""### 🎮 Launch

Watch the console: every **quest** is a tool GoPilot calls on its own.
"""

MD_RESULT = r"""### 🗺️ What GoPilot found

The mission postcard below shows on any screen. Under it is the interactive map: zoom in, toggle layers, click a
plume.
"""

MD_BEYOND = r"""## 🌍 5. Beyond methane

We chose methane as our theme, but GoPilot is not a methane tool. The same one-sentence pattern drives our other
models. Each mission below names a small box and the data to use, so it finishes in a minute or two.
"""

MD_PALMS = r"""### 🌴 Mission 2: count date palms, Al-Ahsa oasis (Theme 02, agriculture)
Our Saudi palm detector, on a single 30 cm image of a 300 × 300 m farm block.
"""

MD_SOLAR = r"""### ☀️ Mission 3: map solar panels, Dubai (Theme 05, cities and energy)
Our solar-panel model, on a 400 × 400 m block of the Mohammed bin Rashid Al Maktoum Solar Park.
"""

MD_FIELDS = r"""### 🌾 Mission 4: draw farm fields, Wadi Ad-Dawasir (Theme 02, agriculture)
Field boundaries from one Sentinel-2 scene, over a 6 × 6 km box of desert farms.
"""

MD_NOTES = r"""## 📐 6. The fine print

**Method.** GoPilot (Claude on Amazon Bedrock AgentCore) plans each request and calls GoServer, our MCP tool
servers on serverless GPUs. For methane, it compares a Sentinel-2 L1C target scene with clean reference scenes;
MethaneMapper segments plumes from the B12/B11 change.

**Limits, briefly:**
- Sentinel-2's 20 m SWIR sees large point sources (hundreds of kg/h and up), not small leaks.
- Bright, dark or wet surfaces can mimic the signal; a cloudy target date means no detection.
- An agent can choose different reference scenes between runs; the saved run is the one shown.

| Data | Use | Licence |
|---|---|---|
| Copernicus Sentinel-2 L1C / L2A (ESA), via Element84 Earth Search | Methane and field missions | Free and open. *Contains modified Copernicus Sentinel data.* |
| Mapbox Satellite | Palm and solar missions | © Mapbox, © Maxar, used through GoPilot |
| Esri World Imagery | Basemaps here | © Esri, with attribution on the maps |
| GoPilot, MethaneMapper and our models | Detection and orchestration | RASID, used as a service |

**Run it yourself:** *Run all* replays the recorded missions with no setup. To fly them live, put the three values in
`creds.env` at the repo root (or as environment variables or Colab Secrets): `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY` and `GOPILOT_AGENT_ARN`. They belong to a GoPilot-only IAM user that RASID can revoke at any
time.

**Team RASID** · [rasid.ai](https://www.rasid.ai) · [app.rasid.ai](https://app.rasid.ai) · info@rasid.ai
"""

# --------------------------------------------------------------------------------------------- code
PY_SETUP = r'''# @title 🔧 Setup: find the repo, load credentials (run once) { display-mode: "form" }
import os
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/rasid-ai/gopilot_methane_813_arab_youth"
IN_COLAB = "google.colab" in sys.modules


def _find_repo():
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "results").is_dir() and (p / "data" / "sample_input").is_dir():
            return p
    if IN_COLAB:                       # Colab opened the notebook on its own: fetch the rest of the repo
        target = Path("/content") / REPO_URL.rsplit("/", 1)[1]
        if not target.exists():
            subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(target)], check=True)
        return target
    raise FileNotFoundError("Run this notebook from inside the repository; see the README.")


REPO = _find_repo()
if IN_COLAB:                           # Colab already has numpy, matplotlib, folium and markdown
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "boto3==1.43.37", "rasterio==1.4.3"], check=True)


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
print(f"📁 Repository: {REPO}")
print("🟢 LIVE: each mission calls GoPilot now." if MODE == "live" else
      "🔁 REPLAY: no credentials found, so each mission replays our recorded GoPilot run from results/. "
      "Fill creds.env to fly the missions live.")'''

PY_CONSOLE = r'''# @title 🎮 GoPilot mission console { display-mode: "form" }
import html as _html
import json
import re
import time
import uuid

import boto3
import markdown as _markdown
from botocore.config import Config
from IPython.display import HTML, display

_TOOL = re.compile(r'<tool id="(\d+)" status="(\w+)">(.*?)</tool>', re.S)
_TOKENS = re.compile(r"<(input|output|cache_read|cache_write|total)_tokens>(\d+)</\1_tokens>")
_FINAL = re.compile(r"<final>(.*?)(?:</final>|$)", re.S)
_THINK = re.compile(r"<think(?:_final)?>(.*?)(?:</think(?:_final)?>|(?=<tool|<final>)|$)", re.S)
_META = re.compile(r"```file-meta\s*(\{.*?\})\s*```", re.S)
_LINK = re.compile(r"\[([^\]]+)\]\(((?:https?://|files/)[^)\s]+)\)")   # signed links, or a recording's files

# What each tool is, as a quest. Anything not listed shows its own name.
QUESTS = {
    "geocode": "LOCATE THE SITE", "locate_point": "LOCATE THE SITE", "pre_order_tools": "EQUIP TOOLS",
    "load_tools": "EQUIP TOOLS", "list_tools": "BROWSE THE ARSENAL", "catalog_tools": "READ TOOL MANUALS",
    "sentinel2_search_goserver": "SCAN SENTINEL-2 ARCHIVE", "sentinel2_fetch_goserver": "DOWNLOAD SCENE",
    "detect_methane_plumes_goserver": "RUN METHANEMAPPER", "calculate_methane_index_goserver": "INDEX CROSS-CHECK",
    "mapbox_fetch_goserver": "FETCH 30 CM IMAGE", "google_satellite_fetch_goserver": "FETCH 30 CM IMAGE",
    "ksa_palm_detection_goserver": "RUN PALM DETECTOR", "segment_solar_panels_goserver": "RUN SOLAR MODEL",
    "delineate_fields_goserver": "RUN FIELD MODEL", "ksa_delineate_fields_goserver": "RUN FIELD MODEL",
    "inspect_file": "INSPECT RESULT", "present_files": "PACK THE LAYERS", "signal_end": "WRITE MISSION REPORT",
    "execute_tool": "RUN A TOOL",
}

# 14 x 14 pixel robot. Y antenna, W body, D visor, E eyes, G trim, O lights, F thruster flames.
_ROBOT = ["......YY......", ".......G......", "...WWWWWWWW...", "..WWDDDDDDWW..", "..WDEEDDEEDW..",
          "..WDEEDDEEDW..", "..WWDDDDDDWW..", "...WWWWWWWW...", "....WGGGGW....", ".WWWWWWWWWWWW.",
          ".W.WWOOOOWW.W.", ".W.WWWWWWWW.W.", "...WW....WW...", "...FF....FF..."]
_PAL = {"Y": "#ffcc4d", "W": "#e9fff6", "D": "#0b1a2e", "E": "#59ff9c", "G": "#00e0a4", "O": "#ff5a36", "F": "#ffb020"}


def _robot_svg(px=5):
    cells = []
    for r, row in enumerate(_ROBOT):
        for c, k in enumerate(row):
            if k != ".":
                cls = ' class="gp-eye"' if k == "E" else (' class="gp-flame"' if k == "F" else "")
                cells.append(f'<rect{cls} x="{c * px}" y="{r * px}" width="{px}" height="{px}" fill="{_PAL[k]}"/>')
    n = len(_ROBOT) * px
    return f'<svg width="{n}" height="{n}" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">{"".join(cells)}</svg>'


_ROBOT_SVG = _robot_svg()


def _decode(line):
    # AgentCore sends each chunk as `data: <json string>` (or a {"t","d"} envelope).
    if not line.startswith("data: "):
        return line
    try:
        obj = json.loads(line[6:])
    except ValueError:
        return line[6:]
    return obj["d"] if isinstance(obj, dict) and "d" in obj else obj


class Run:
    """One mission: the raw stream, and what the notebook reads out of it."""

    def __init__(self, prompt, mode="live"):
        self.prompt, self.raw, self.error, self.mode = prompt, "", None, mode
        self.t0, self.t1, self.session_id = time.time(), None, None
        self.speed, self.base_dir, self.missing = 1.0, None, False

    done = property(lambda self: self.t1 is not None)
    # Mission time: a replay plays faster, but the console shows the time the real run took.
    elapsed = property(lambda self: ((self.t1 or time.time()) - self.t0) * self.speed)

    @property
    def tools(self):
        calls = {}
        for i, status, name in _TOOL.findall(self.raw):
            calls[int(i)] = (name.strip(), status)
        return [calls[i] for i in sorted(calls)]

    @property
    def tokens(self):
        return {k: int(v) for k, v in _TOKENS.findall(self.raw)}

    @property
    def final_md(self):
        m = _FINAL.search(self.raw)
        return m.group(1).strip() if m else ""

    @property
    def files(self):
        return {name.strip(): url for name, url in _LINK.findall(self.final_md)}

    @property
    def file_meta(self):
        m = _META.search(self.raw)
        try:
            return json.loads(m.group(1)) if m else {}
        except ValueError:
            return {}

    @property
    def thinking(self):
        return "\n".join(t.strip() for t in _THINK.findall(self.raw) if t.strip())

    def to_html(self):
        return _console(self)

    def _repr_html_(self):
        return _console(self)


def _console(run):
    t = run.elapsed
    d = lambda period: f"-{t % period:.2f}s"        # keep every animation continuous across re-renders
    mm, ss = divmod(int(t), 60)
    tools = run.tools
    n_done = sum(s == "done" for _, s in tools)
    tok = run.tokens.get("total")
    if run.missing:
        state, state_c = "NO RECORDING", "#9fb8d6"
    elif run.error:
        state, state_c = "MISSION FAILED", "#ff5a5a"
    elif run.done:
        state, state_c = "MISSION COMPLETE", "#ffcc4d"
    else:
        state, state_c = "LIVE", "#59ff9c"
    xp = 100 if run.done else (100 * n_done / max(len(tools) + 1, 1))
    rows = []
    shown = tools[-10:]
    if len(tools) > len(shown):
        rows.append(f'<div class="gp-q gp-dim">… {len(tools) - len(shown)} earlier quests cleared</div>')
    for k, (name, status) in enumerate(shown, start=len(tools) - len(shown) + 1):
        label = QUESTS.get(name, name.replace("_goserver", "").replace("_", " ").upper())
        raw = _html.escape(name.replace("_goserver", ""))
        if status == "done":
            tail = '<span class="gp-ok">CLEAR ✓</span>'
        else:
            tail = f'<span class="gp-run"><span class="gp-spin" style="animation-delay:{d(.8)}">◐</span> RUNNING</span>'
        rows.append(f'<div class="gp-q"><span class="gp-lvl">LV{k:02d}</span><span class="gp-name">{label}'
                    f'<span class="gp-raw"> · {raw}</span></span><span class="gp-dots"></span>{tail}</div>')
    if not tools:
        rows.append(f'<div class="gp-q gp-dim">… booting up <span class="gp-blink" style="animation-delay:{d(1)}">▮</span></div>')
    think = run.thinking
    comms = ""
    if think and not run.done:
        comms = (f'<div class="gp-term"><span class="gp-tlabel">◆ COMMS FROM GOPILOT</span>\n'
                 f'{_html.escape(think[-320:])}<span class="gp-blink" style="animation-delay:{d(1)}">▮</span></div>')
    banner = ""
    if run.done:
        mark = "✖" if run.error else "★"
        sub = (_html.escape(run.error) if run.error else
               f"{mm}:{ss:02d} · {len(tools)} quests" + (f" · {tok / 1000:,.0f}K tokens" if tok else ""))
        banner = (f'<div class="gp-win" style="color:{state_c};animation-delay:{d(1.2)}">{mark} {state} {mark}</div>'
                  f'<div class="gp-winsub">{sub}</div>')
    answer = ""
    if run.done and run.final_md:
        md = _LINK.sub(lambda m: f"`{m.group(1)}`", run.final_md)        # never print a signed link
        answer = f'<div class="gp-answer">{_markdown.markdown(md, extensions=["tables", "fenced_code"])}</div>'
        if think:
            answer += (f'<details class="gp-log"><summary>🧠 GoPilot\'s full log ({len(think):,} characters)</summary>'
                       f'<pre>{_html.escape(think)}</pre></details>')
    bob = "" if run.done else f"animation:gp-bob 1.4s ease-in-out infinite;animation-delay:{d(1.4)}"
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap');
.gp{{font-family:'VT323','Courier New',monospace;background:#070b1a;color:#cfe9ff;border-radius:16px;overflow:hidden;
 position:relative;max-width:1000px;border:2px solid #1f3b5c;box-shadow:0 0 28px rgba(0,224,164,.18)}}
.gp-stars{{position:absolute;inset:0;opacity:.55;pointer-events:none;background-image:
 radial-gradient(1.5px 1.5px at 12% 22%,#fff 50%,transparent 51%),radial-gradient(1px 1px at 33% 70%,#9fd 50%,transparent 51%),
 radial-gradient(1.2px 1.2px at 58% 18%,#fff 50%,transparent 51%),radial-gradient(1px 1px at 76% 62%,#fd9 50%,transparent 51%),
 radial-gradient(1.6px 1.6px at 90% 30%,#fff 50%,transparent 51%),radial-gradient(1px 1px at 45% 45%,#fff 50%,transparent 51%);
 background-size:340px 220px;animation:gp-drift 40s linear infinite;animation-delay:{d(40)}}}
.gp-scan{{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(255,255,255,.035) 0 1px,transparent 1px 3px)}}
.gp-hud{{position:relative;display:flex;align-items:center;gap:14px;padding:12px 18px;border-bottom:2px dashed #1f3b5c;
 font-family:'Press Start 2P','Courier New',monospace;font-size:10px;color:#7CFFCB}}
.gp-hud .gp-sp{{flex:1}}
.gp-pill{{padding:4px 8px;border:1px solid currentColor;border-radius:4px}}
.gp-body{{position:relative;display:flex;gap:18px;padding:14px 18px}}
.gp-bot{{flex:0 0 76px;text-align:center}}
.gp-mis{{font-size:21px;color:#ffe9a8;margin-bottom:8px}}
.gp-q{{display:flex;align-items:baseline;gap:8px;font-size:20px;line-height:1.25}}
.gp-lvl{{color:#ffcc4d}} .gp-raw{{color:#5b7aa6;font-size:16px}}
.gp-dots{{flex:1;border-bottom:2px dotted #2a4a6b;transform:translateY(-5px)}}
.gp-ok{{color:#59ff9c}} .gp-run{{color:#ffcc4d}} .gp-dim{{color:#5b7aa6}}
.gp-spin{{display:inline-block;animation:gp-spin .8s linear infinite}}
.gp-blink{{animation:gp-blink 1s steps(2,start) infinite}}
.gp-xp{{height:12px;background:#10213a;border-radius:6px;overflow:hidden;margin:10px 0 4px;border:1px solid #1f3b5c}}
.gp-xp>div{{height:100%;background:linear-gradient(90deg,#00e0a4,#b6ffe6,#00e0a4);background-size:200% 100%;
 animation:gp-shim 1.6s linear infinite;animation-delay:{d(1.6)}}}
.gp-term{{margin-top:10px;font-size:18px;color:#59ff9c;background:#03140b;border:1px solid #0f3d24;border-radius:8px;
 padding:8px 10px;white-space:pre-wrap;text-shadow:0 0 6px rgba(89,255,156,.45)}}
.gp-tlabel{{color:#7CFFCB;font-family:'Press Start 2P',monospace;font-size:9px}}
.gp-win{{font-family:'Press Start 2P','Courier New',monospace;font-size:17px;text-align:center;padding:14px 0 4px;
 animation:gp-glow 1.2s ease-in-out infinite alternate}}
.gp-winsub{{text-align:center;font-size:20px;color:#9fb8d6;padding-bottom:12px}}
.gp-answer{{position:relative;background:#f7fbf9;color:#1a1f1c;font-family:system-ui,sans-serif;font-size:14px;
 line-height:1.55;padding:14px 20px;border-top:3px solid #00e0a4}}
.gp-answer table{{border-collapse:collapse;margin:6px 0}} .gp-answer td,.gp-answer th{{border:1px solid #d6e5df;padding:3px 8px}}
.gp-answer code{{background:#e7f2ee;padding:1px 4px;border-radius:3px}}
.gp-log{{position:relative;background:#03140b;color:#59ff9c;padding:6px 18px;font-size:16px}}
.gp-log pre{{white-space:pre-wrap;max-height:260px;overflow:auto;font-family:'VT323',monospace;font-size:17px}}
.gp-eye{{animation:gp-wink 4s infinite;transform-origin:center;transform-box:fill-box;animation-delay:{d(4)}}}
.gp-flame{{animation:gp-flick .25s steps(2) infinite;animation-delay:{d(.25)}}}
@keyframes gp-drift{{to{{background-position:-340px 220px}}}}
@keyframes gp-spin{{to{{transform:rotate(360deg)}}}}
@keyframes gp-blink{{to{{visibility:hidden}}}}
@keyframes gp-shim{{to{{background-position:-200% 0}}}}
@keyframes gp-glow{{from{{text-shadow:0 0 4px currentColor}}to{{text-shadow:0 0 16px currentColor,0 0 30px #ff8a00}}}}
@keyframes gp-wink{{0%,92%,100%{{transform:scaleY(1)}}95%{{transform:scaleY(.1)}}}}
@keyframes gp-flick{{50%{{opacity:.35}}}}
@keyframes gp-bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-7px)}}}}
</style>
<div class="gp"><div class="gp-stars"></div><div class="gp-scan"></div>
 <div class="gp-hud"><span>GOPILOT // MISSION CONSOLE</span><span class="gp-sp"></span>
  <span>T+{mm:02d}:{ss:02d}</span><span>QUESTS {n_done}/{len(tools)}</span>{f"<span>{tok / 1000:,.0f}K TOK</span>" if tok else ""}
  {f'<span class="gp-pill" style="color:#c9a2ff">REPLAY ×{run.speed:.0f}</span>' if run.mode == "replay" else ""}
  <span class="gp-pill" style="color:{state_c}">{"● " if not run.done else ""}{state}</span></div>
 <div class="gp-body"><div class="gp-bot"><div style="{bob}">{_ROBOT_SVG}</div></div>
  <div style="flex:1;min-width:0"><div class="gp-mis">&gt; MISSION: {_html.escape(run.prompt)}</div>
   {"".join(rows)}
   <div class="gp-xp"><div style="width:{xp:.0f}%"></div></div>
   {comms}</div></div>
 {banner}{answer}</div>"""


class _NoDisplay:
    def update(self, *_):
        pass


class GoPilot:
    """A minimal client for the GoPilot API (Amazon Bedrock AgentCore runtime), with a recorded-run replay."""

    def __init__(self, agent_arn=None, region=None, aws_access_key_id=None, aws_secret_access_key=None,
                 user_id="aysh-813-review"):
        self.agent_arn, self.region, self.user_id = agent_arn, region, user_id
        self._keys = (aws_access_key_id, aws_secret_access_key)
        self._runtime = None

    def ask(self, prompt, mission=None, record=None):
        """Fly one mission. Live with credentials (recording it to results/<mission> when GOPILOT_RECORD=1),
        otherwise replay the recording of that mission."""
        prompt = " ".join(prompt.split())
        run = Run(prompt, MODE)
        rec_dir = REPO / "results" / mission if mission else None
        record = os.environ.get("GOPILOT_RECORD") == "1" if record is None else record
        handle = display(HTML(run.to_html()), display_id=True) or _NoDisplay()   # None outside a notebook
        try:
            if MODE == "live":
                self._live(run, handle, rec_dir if (record and rec_dir) else None)
            else:
                self._replay(run, handle, rec_dir)
        except Exception as e:
            run.error = f"{type(e).__name__}: {e}"
        finally:
            run.t1 = run.t1 or time.time()
            if "Yowza Something Wrong Happened" in run.raw and not run.error:
                run.error = "GoPilot reported an internal error. Run the cell again."
            handle.update(HTML(run.to_html()))
        return run

    def _live(self, run, handle, rec_dir):
        if self._runtime is None:
            self._runtime = boto3.client(
                "bedrock-agentcore", region_name=self.region,
                aws_access_key_id=self._keys[0], aws_secret_access_key=self._keys[1],
                config=Config(read_timeout=900, connect_timeout=30, retries={"max_attempts": 0}))
        run.session_id = f"aysh813-{uuid.uuid4().hex}"                    # AgentCore wants >= 33 chars
        payload = {"prompt": run.prompt, "session_id": run.session_id, "user_id": self.user_id, "config_version": "v1.0"}
        response = self._runtime.invoke_agent_runtime(
            agentRuntimeArn=self.agent_arn, runtimeSessionId=run.session_id,
            runtimeUserId=self.user_id, payload=json.dumps(payload).encode())
        events, last_draw, last_len = [], 0.0, -1
        for line in response["response"].iter_lines(chunk_size=32):       # small chunks: render as it arrives
            if line:
                chunk = _decode(line.decode("utf-8"))
                run.raw += chunk
                events.append((time.time() - run.t0, chunk))
            now = time.time()
            if now - last_draw > 1.0 or (len(run.raw) != last_len and now - last_draw > 0.5):
                handle.update(HTML(run.to_html()))
                last_draw, last_len = now, len(run.raw)
        run.t1 = time.time()
        if rec_dir is not None:
            _save_recording(run, events, rec_dir)

    def _replay(self, run, handle, rec_dir):
        stream = rec_dir / "stream.jsonl" if rec_dir else None
        if stream is None or not stream.exists():
            run.missing, run.error = True, "No recording of this mission yet. Fill creds.env to fly it live."
            return
        events = [json.loads(l) for l in stream.read_text().splitlines() if l.strip()]
        total = max(events[-1]["t"], 1.0)
        run.speed, run.base_dir = max(1.0, total / 20.0), rec_dir           # every replay takes about 20 s
        start, last_draw = time.time(), 0.0
        for ev in events:
            wait = ev["t"] / run.speed - (time.time() - start)
            if wait > 0:
                time.sleep(wait)
            run.raw += ev["d"]
            if time.time() - last_draw > 0.5:
                handle.update(HTML(run.to_html()))
                last_draw = time.time()
        run.t1 = run.t0 + total / run.speed


def _save_recording(run, events, rec_dir):
    """Keep a live run for replay: the stream with every signed link swapped for a local file, and the files."""
    import requests
    files_dir = rec_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    local = {}
    for name, url in run.files.items():
        data = requests.get(url, timeout=300).content
        if len(data) <= 25_000_000:                     # layers only, never whole scenes
            (files_dir / name).write_bytes(data)
            local[url] = f"files/{name}"
    clean = lambda text: _LINK.sub(lambda m: f"[{m.group(1)}]({local.get(m.group(2), 'files/' + m.group(1))})", text)
    chunks = [(t, clean(c)) for t, c in events]
    if any("X-Amz" in c or "amazonaws.com" in c for _, c in chunks):   # a link split across chunks: merge the answer
        k = next(i for i, (_, c) in enumerate(chunks) if "<final>" in c)
        chunks = chunks[:k] + [(chunks[-1][0], clean("".join(c for _, c in events[k:])))]
    assert not any("X-Amz" in c for _, c in chunks), "a signed link survived; recording not saved"
    with open(rec_dir / "stream.jsonl", "w") as f:
        for t, c in chunks:
            f.write(json.dumps({"t": round(t, 2), "d": c}, ensure_ascii=False) + "\n")
    (rec_dir / "meta.json").write_text(json.dumps({
        "prompt": run.prompt, "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(run.t0)),
        "seconds": round(run.t1 - run.t0, 1), "tools": [n for n, _ in run.tools], "tokens": run.tokens,
        "files": sorted(p.name for p in files_dir.iterdir())}, indent=1))


gopilot = GoPilot(GOPILOT_AGENT_ARN, GOPILOT_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
display(HTML(f'<div style="font-family:monospace;color:#00a77d">{_ROBOT_SVG} GoPilot is on the launch pad '
             f'({"live" if MODE == "live" else "replaying recorded missions"}). Ready.</div>'))'''

PY_MAPS = r'''# @title 🗺️ Map tools: the postcard and the interactive map { display-mode: "form" }
import base64
import io
import math
from xml.etree import ElementTree as ET

import folium
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import requests
from IPython.display import Image as _Image
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as _MplPolygon
from PIL import Image
from matplotlib import colormaps
from rasterio.warp import Resampling, calculate_default_transform, reproject, transform_bounds, transform_geom

ESRI_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
ESRI_EXPORT = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
_RASTER_EXT, _VECTOR_EXT = (".tif", ".tiff"), (".geojson", ".json")
_PALETTE = ["#ff3b30", "#ffcc4d", "#59ff9c", "#3aa0ff", "#ff5a9e"]
_R = 6378137.0


def _merc(lon, lat):
    lat = max(min(lat, 85.0), -85.0)
    return _R * math.radians(lon), _R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def _xml(sld):
    s = re.sub(r"<\?xml[^>]*\?>", "", sld)
    s = re.sub(r'\s[\w:]*(xmlns|schemaLocation)(:\w+)?="[^"]*"', "", s)
    return ET.fromstring(re.sub(r"(</?)[\w.-]+:", r"\1", s))


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _hex_rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _sld_colormap(sld):
    try:
        root = _xml(sld)
    except ET.ParseError:
        return None
    for el in root.iter():
        if _local(el.tag) == "ColorMap":
            entries = [(float(e.get("quantity")), (*_hex_rgb(e.get("color")), int(255 * float(e.get("opacity", 1)))))
                       for e in el if _local(e.tag) == "ColorMapEntry" and e.get("color")]
            if entries:
                return el.get("type", "ramp"), sorted(entries)
    return None


def _sld_vector(sld):
    out = {"column": None, "classes": {}, "fill": None, "stroke": None}
    if not sld:
        return out
    try:
        root = _xml(sld)
    except ET.ParseError:
        return out
    for rule in (e for e in root.iter() if _local(e.tag) == "Rule"):
        params = {p.get("name"): (p.text or "").strip() for p in rule.iter() if _local(p.tag) in ("SvgParameter", "CssParameter")}
        prop = next((p.text for p in rule.iter() if _local(p.tag) == "PropertyName"), None)
        lit = next((p.text for p in rule.iter() if _local(p.tag) == "Literal"), None)
        if prop is not None and lit is not None and params.get("fill"):
            out["column"] = prop
            out["classes"][str(lit)] = params["fill"]
        elif params.get("fill"):
            out["fill"] = out["fill"] or params["fill"]
        out["stroke"] = out["stroke"] or params.get("stroke")
    return out


def _bands(src):
    names = [(d or "").upper() for d in src.descriptions]
    if all(b in names for b in ("B04", "B03", "B02")):
        return [names.index(b) + 1 for b in ("B04", "B03", "B02")]
    if src.count == 13:
        return [4, 3, 2]
    return [1, 2, 3] if src.count in (3, 4) else [1]


def _raster(data, meta, max_px=1024):
    """GeoTIFF bytes -> (RGBA array in web mercator, (left, bottom, right, top) metres, styled?)."""
    cmap = _sld_colormap(meta["sld"]) if (meta or {}).get("sld") else None
    with rasterio.MemoryFile(data) as mf, mf.open() as src:
        bands = [1] if cmap else _bands(src)
        dst = "EPSG:3857"
        _, w, h = calculate_default_transform(src.crs, dst, src.width, src.height, *src.bounds)
        s = max(w, h) / max_px
        if s > 1:
            w, h = max(1, int(w / s)), max(1, int(h / s))
        tr, w, h = calculate_default_transform(src.crs, dst, src.width, src.height, *src.bounds, dst_width=w, dst_height=h)
        arr = np.full((len(bands), h, w), np.nan, np.float32)
        for k, b in enumerate(bands):
            reproject(rasterio.band(src, b), arr[k], src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
                      dst_transform=tr, dst_crs=dst, dst_nodata=np.nan,
                      resampling=Resampling.nearest if cmap else Resampling.bilinear)
    ext = (tr.c, tr.f + tr.e * h, tr.c + tr.a * w, tr.f)
    ok = np.all(np.isfinite(arr), 0)
    rgba = np.zeros((h, w, 4), np.uint8)
    if cmap:
        kind, entries = cmap
        v, qs = arr[0], np.array([q for q, _ in entries])
        cols = np.array([c for _, c in entries], float)
        if kind == "values":
            idx = np.abs(v[..., None] - qs).argmin(-1)
            hit = ok & np.isclose(v, qs[idx])
            rgba[hit] = cols[idx[hit]].astype(np.uint8)
        elif kind == "intervals":
            idx = np.clip(np.searchsorted(qs, v, side="left"), 0, len(qs) - 1)
            rgba[ok] = cols[idx[ok]].astype(np.uint8)
        else:
            for c in range(4):
                rgba[..., c] = np.where(ok, np.interp(np.nan_to_num(v), qs, cols[:, c]), 0).astype(np.uint8)
    elif len(bands) == 3:
        ok &= np.any(arr > 0, 0)
        for c in range(3):
            lo, hi = np.nanpercentile(arr[c][ok], [2, 98]) if ok.any() else (0, 1)
            rgba[..., c] = (np.clip((arr[c] - lo) / max(hi - lo, 1e-9), 0, 1) * 255).astype(np.uint8)
        rgba[..., 3] = ok * 255
    else:
        v = arr[0]
        if ok.any():
            lo, hi = np.nanpercentile(v[ok], [2, 98])
            rgba[...] = (colormaps["magma"](np.clip((v - lo) / max(hi - lo, 1e-9), 0, 1)) * 255).astype(np.uint8)
        rgba[..., 3] = ok * 220
    return rgba, ext, bool(cmap)


def _to_wgs84(gj):
    name = str(((gj.get("crs") or {}).get("properties") or {}).get("name", ""))
    if not name or "CRS84" in name or name.endswith(":4326"):
        return gj
    epsg = re.search(r"(\d{4,5})$", name)
    src = f"EPSG:{epsg.group(1)}" if epsg else name
    feats = [{**f, "geometry": transform_geom(src, "EPSG:4326", f["geometry"])} for f in gj.get("features", []) if f.get("geometry")]
    return {"type": "FeatureCollection", "features": feats}


def _rings(geom):
    t, c = geom.get("type"), geom.get("coordinates", [])
    if t == "Polygon":
        return [c[0]]
    if t == "MultiPolygon":
        return [p[0] for p in c]
    if t == "Point":
        return [[c]]
    if t in ("MultiPoint", "LineString"):
        return [c]
    return []


def _load(run, max_px):
    """Every result layer, downloaded once: [(name, kind, payload, meta)]."""
    layers = []
    for name, url in run.files.items():
        meta, low = run.file_meta.get(name, {}), name.lower()
        try:
            if url.startswith("http"):
                data = requests.get(url, timeout=120).content
            else:                                   # a replay: the layer is a file of the recording
                data = (run.base_dir / url).read_bytes()
            if low.endswith(_RASTER_EXT):
                layers.append((name, "raster", _raster(data, meta, max_px), meta))
            elif low.endswith(_VECTOR_EXT):
                layers.append((name, "vector", _to_wgs84(json.loads(data)), meta))
        except Exception as e:
            print(f"⚠️ {name}: not drawn ({type(e).__name__})")
    return layers


def _extent(layers):
    xs, ys = [], []
    for _, kind, p, _ in layers:
        if kind == "raster":
            l, b, r, t = p[1]; xs += [l, r]; ys += [b, t]
        else:
            for f in p.get("features", []):
                for ring in _rings(f.get("geometry") or {}):
                    for lon, lat, *_ in ring:
                        x, y = _merc(lon, lat); xs.append(x); ys.append(y)
    if not xs:
        return None
    pad = max(max(xs) - min(xs), max(ys) - min(ys), 600) * 0.12
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def _basemap(ext, px=1400):
    l, b, r, t = ext
    w = px if (r - l) >= (t - b) else int(px * (r - l) / (t - b))
    h = int(w * (t - b) / (r - l))
    try:
        res = requests.get(ESRI_EXPORT, timeout=60, params={
            "bbox": f"{l},{b},{r},{t}", "bboxSR": 3857, "imageSR": 3857, "size": f"{w},{h}", "format": "jpg", "f": "image"})
        return np.asarray(Image.open(io.BytesIO(res.content)).convert("RGB"))
    except Exception:
        return None


def postcard(run, layers, title):
    """A static picture of the result: shows on any screen, also where interactive maps do not."""
    ext = _extent(layers)
    if ext is None:
        return None
    l, b, r, t = ext
    fig, ax = plt.subplots(figsize=(10, 10 * (t - b) / (r - l)) if (t - b) <= (r - l) else (10 * (r - l) / (t - b), 10), dpi=110)
    fig.patch.set_facecolor("#070b1a")
    base = _basemap(ext)
    if base is not None:
        ax.imshow(base, extent=(l, r, b, t), zorder=0)
    legend, k = [], 0
    for name, kind, p, meta in layers:
        if kind == "raster":
            rgba, (rl, rb, rr, rt), styled = p
            ax.imshow(rgba, extent=(rl, rr, rb, rt), alpha=0.75 if styled else 1.0, zorder=1, interpolation="nearest")
        else:
            style = _sld_vector(meta.get("sld"))
            color = style["fill"] or _PALETTE[k % len(_PALETTE)]; k += 1
            polys = []
            for f in p.get("features", []):
                for ring in _rings(f.get("geometry") or {}):
                    pts = [_merc(lon, lat) for lon, lat, *_ in ring]
                    if len(pts) >= 3:
                        polys.append(_MplPolygon(pts, closed=True))
                    elif pts:
                        ax.plot(*zip(*pts), "o", color=color, ms=4, zorder=3)
            if polys:
                ax.add_collection(PatchCollection(polys, facecolor=color, edgecolor="white", linewidth=0.8, alpha=0.65, zorder=2))
            legend.append((name, color, len(p.get("features", []))))
    ax.set_xlim(l, r); ax.set_ylim(b, t); ax.set_axis_off()
    ax.set_title(title, color="#ffcc4d", fontsize=14, family="monospace", loc="left", pad=10)
    txt = "   ".join(f"■ {n.rsplit('-', 1)[0]} ({c} features)" for n, _, c in legend) or "   ".join(n for n, *_ in layers)
    fig.text(0.01, 0.01, txt[:150], color="#cfe9ff", fontsize=9, family="monospace")
    fig.text(0.99, 0.01, "Imagery © Esri, Maxar · Contains modified Copernicus Sentinel data", color="#5b7aa6", fontsize=7, ha="right")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return _Image(buf.getvalue())


def interactive_map(layers):
    m = folium.Map(location=[25, 45], zoom_start=5, tiles=None, control_scale=True)
    folium.TileLayer(ESRI_TILES, attr="Esri, Maxar, Earthstar Geographics", name="Satellite").add_to(m)
    k = 0
    for name, kind, p, meta in layers:
        if kind == "raster":
            rgba, (l, b, r, t), styled = p
            (w0, s0), (e0, n0) = [((x / _R) * 180 / math.pi, math.degrees(2 * math.atan(math.exp(y / _R)) - math.pi / 2)) for x, y in ((l, b), (r, t))]
            buf, fmt = io.BytesIO(), "PNG" if styled else "WEBP"
            Image.fromarray(rgba, "RGBA").save(buf, fmt, **({} if styled else {"quality": 80}))
            url = f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()
            folium.raster_layers.ImageOverlay(url, bounds=[[s0, w0], [n0, e0]], name=name, opacity=0.7 if styled else 1.0).add_to(m)
        else:
            style = _sld_vector(meta.get("sld"))
            color = style["fill"] or _PALETTE[k % len(_PALETTE)]; k += 1
            props = (p.get("features") or [{}])[0].get("properties") or {}
            fields = [f for f, v in props.items() if not isinstance(v, (dict, list))][:6]
            paint = lambda f, c=color, s=style: {"fillColor": s["classes"].get(str((f.get("properties") or {}).get(s["column"])), c)
                                                 if s["column"] else c, "color": "#ffffff", "weight": 1.2, "fillOpacity": 0.6}
            folium.GeoJson(p, name=name, style_function=paint,
                           tooltip=folium.GeoJsonTooltip(fields=fields) if fields else None).add_to(m)
    ext = _extent(layers)
    if ext:
        l, b, r, t = ext
        to_ll = lambda x, y: (math.degrees(2 * math.atan(math.exp(y / _R)) - math.pi / 2), math.degrees(x / _R))
        m.fit_bounds([to_ll(l, b), to_ll(r, t)])
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def show(run, title=None, max_px=1024):
    """The mission result: a postcard that shows everywhere, then the interactive map."""
    if run.error or not run.files:
        print("🛰️ No layers to show:", run.error or "GoPilot's answer has no map files this time.")
        return
    layers = _load(run, max_px)
    counts = [f"{n}: {len(p.get('features', []))} features" for n, kind, p, _ in layers if kind == "vector"]
    card = postcard(run, layers, title or "MISSION RESULT")
    if card is not None:
        display(card)
    if counts:
        print("📍 " + " · ".join(counts))
    display(interactive_map(layers))


print("🗺️ Map tools ready.")'''

PY_M1 = r'''mission_1 = gopilot.ask("""
    Check the UTGA gas treatment facility at Tabankourt, Algeria (28.64°N, 7.62°E) for methane plumes on
    3 January 2024. Keep the job small: a 4 × 4 km box centred on that point, the Sentinel-2 L1C scene of
    3 January 2024 as the target, and two clean (under 10 % cloud) Sentinel-2 L1C references from the
    60 days before it. Run MethaneMapper and present the plume polygons with their size.
""", mission="mission_1_methane_tabankourt")'''

PY_M1_SHOW = r'''show(mission_1, "TABANKOURT, ALGERIA · 3 JAN 2024 · METHANE")'''

MD_PHYSICS = r"""### 🔬 Why a model? The raw physics, on our sample input
The textbook signal by hand: the change in B12/B11 between 29 Dec 2023 and 3 Jan 2024, on the 4 × 4 km sample in
`data/sample_input/`. Surface changes, like the dry riverbed's edges, light up as brightly as gas would.
Telling the two apart is what MethaneMapper learned from 25,000 simulated plumes.
"""

PY_PHYSICS = r"""import numpy as np
import rasterio
import matplotlib.pyplot as plt

sample = json.loads((REPO / "data" / "sample_input" / "scenes.json").read_text())


def _read(role):
    with rasterio.open(REPO / "data" / "sample_input" / sample["scenes"][role]["file"]) as r:
        return r.read().astype(float)                  # bands B02 B03 B04 B11 B12


tgt, ref = _read("target"), _read("reference")
ratio = lambda a: a[4] / np.maximum(a[3], 1)          # B12 / B11
frac = 1 - ratio(tgt) / np.maximum(ratio(ref), 1e-6)  # > 0 where B12 darkened, as methane would make it
frac -= np.median(frac)
rgb = np.clip(tgt[[2, 1, 0]].transpose(1, 2, 0) / np.percentile(tgt[[2, 1, 0]], 99), 0, 1)

fig, ax = plt.subplots(1, 2, figsize=(11, 5.2), facecolor="#070b1a")
ax[0].imshow(rgb); ax[0].set_title("Sentinel-2, 3 Jan 2024", color="#cfe9ff", family="monospace")
im = ax[1].imshow(frac, cmap="magma", vmin=0, vmax=np.percentile(frac, 99.7))
ax[1].set_title("raw B12/B11 drop vs 29 Dec 2023", color="#ffcc4d", family="monospace")
for a in ax:
    a.axis("off")
plt.tight_layout(); plt.show()"""

PY_PALMS = r'''mission_2 = gopilot.ask("""
    Count the date palms in this 300 × 300 m block of the Al-Ahsa oasis, Saudi Arabia:
    bbox [49.6105, 25.4205, 49.6135, 25.4235]. Use one Mapbox satellite image of exactly that bbox
    at zoom 19, run the KSA palm detector with its default settings, and present the palm layer.
""", mission="mission_2_palms_alahsa")
show(mission_2, "AL-AHSA OASIS · DATE PALMS")'''

PY_SOLAR = r'''mission_3 = gopilot.ask("""
    Outline the solar panels in this 400 × 400 m block of the Mohammed bin Rashid Al Maktoum Solar Park,
    Dubai: bbox [55.3630, 24.7520, 55.3670, 24.7560]. Use one Mapbox satellite image of exactly that bbox
    at zoom 19, run the solar-panel model, and present the panel polygons.
""", mission="mission_3_solar_dubai")
show(mission_3, "MBR SOLAR PARK, DUBAI · SOLAR PANELS")'''

PY_FIELDS = r'''mission_4 = gopilot.ask("""
    Delineate the farm fields in this 6 × 6 km box near Wadi Ad-Dawasir, Saudi Arabia:
    bbox [44.700, 20.420, 44.760, 20.480]. Use one clear (under 5 % cloud) Sentinel-2 L2A scene from
    February 2025 as a B04-B03-B02 RGB at 10 m, run the field delineation model at 5 m, and present the fields.
""", mission="mission_4_fields_wadi_addawasir")
show(mission_4, "WADI AD-DAWASIR · FARM FIELDS")'''

# --------------------------------------------------------------------------------------------- assemble
CELLS = [
    ("md", MD_HERO), ("md", MD_PROBLEM), ("md", MD_GOPILOT), ("md", MD_MODEL),
    ("md", MD_SETUP), ("py", PY_SETUP), ("py", PY_CONSOLE), ("py", PY_MAPS),
    ("md", MD_MISSION), ("py", PY_M1), ("md", MD_RESULT), ("py", PY_M1_SHOW), ("md", MD_PHYSICS), ("py", PY_PHYSICS),
    ("md", MD_BEYOND), ("md", MD_PALMS), ("py", PY_PALMS), ("md", MD_SOLAR), ("py", PY_SOLAR),
    ("md", MD_FIELDS), ("py", PY_FIELDS), ("md", MD_NOTES),
]
ATTACH = {"gopilot_overview.png": ROOT / "docs" / "img" / "gopilot_overview.png",
          "methane_model.png": ROOT / "docs" / "img" / "methane_model.png"}


def build(path=OUT):
    cells = []
    for n, (kind, src) in enumerate(CELLS):
        if kind == "md":
            cell = {"cell_type": "markdown", "id": f"md{n:02d}", "metadata": {}, "source": _lines(_md_spacing(src))}
            att = {name: {"image/png": base64.b64encode(p.read_bytes()).decode()}
                   for name, p in ATTACH.items() if f"attachment:{name}" in src}
            if att:
                cell["attachments"] = att
        else:
            cell = {"cell_type": "code", "id": f"py{n:02d}", "metadata": {"cellView": "form"} if src.startswith("# @title") else {},
                    "execution_count": None, "outputs": [], "source": _lines(src)}
        cells.append(cell)
    nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
          "metadata": {"colab": {"provenance": [], "toc_visible": True},
                       "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}}}
    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    return path


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size / 1024:.0f} KB, {len(CELLS)} cells)")
