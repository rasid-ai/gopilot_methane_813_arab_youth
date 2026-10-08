"""The mission console: talks to GoPilot (live or replayed) and draws what it does, retro style."""

import html as _html
import os
import json
import re
import time
import uuid

import boto3
import markdown as _markdown
from botocore.config import Config
from IPython.display import HTML, display

from .config import MODE, REPO

_TOOL = re.compile(r'<tool id="(\d+)" status="(\w+)">(.*?)</tool>', re.S)
_TOKENS = re.compile(r"<(input|output|cache_read|cache_write|total)_tokens>(\d+)</\1_tokens>")
_FINAL = re.compile(r"<final>(.*?)(?:</final>|$)", re.S)
_THINK = re.compile(r"<think(?:_final)?>(.*?)(?:</think(?:_final)?>|(?=<tool|<final>)|$)", re.S)
_META = re.compile(r"```file-meta\s*(\{.*?\})\s*```", re.S)
_SIGNED = re.compile(r"https?://[^\s\"'<>)\]]+X-Amz-[^\s\"'<>)\]]*")   # any presigned URL, anywhere
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
            try:
                _save_recording(run, events, rec_dir)
            except Exception as e:                  # a recording problem must never cost the mission its result
                print(f"⚠️ Recording not saved: {type(e).__name__}: {e}")

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
    if files_dir.exists():                      # a re-recording replaces the old one whole
        for old in files_dir.iterdir():
            old.unlink()
    files_dir.mkdir(parents=True, exist_ok=True)
    local = {}
    for name, url in run.files.items():
        data = requests.get(url, timeout=300).content
        if len(data) <= 25_000_000:                     # layers only, never whole scenes
            (files_dir / name).write_bytes(data)
            local[url] = f"files/{name}"
    def clean(text):
        # Markdown download links become the local file; any other signed URL (file-meta's usage ledger,
        # say) becomes its file name, or a marker. No signature leaves this function.
        text = _LINK.sub(lambda m: f"[{m.group(1)}]({local.get(m.group(2), 'files/' + m.group(1))})", text)
        def unsign(m):
            name = m.group(0).split("?", 1)[0].rsplit("/", 1)[-1]
            return f"files/{name}" if (files_dir / name).exists() else "signed-link-removed"
        return _SIGNED.sub(unsign, text)

    chunks = [(t, clean(c)) for t, c in events]
    if any("X-Amz" in c for _, c in chunks):    # a signed URL split across chunks: merge from the answer on
        k = next((i for i, (_, c) in enumerate(chunks) if "<final>" in c), 0)
        chunks = chunks[:k] + [(chunks[-1][0], clean("".join(c for _, c in events[k:])))]
    assert not any("X-Amz" in c for _, c in chunks), "a signed link survived"
    with open(rec_dir / "stream.jsonl", "w") as f:
        for t, c in chunks:
            f.write(json.dumps({"t": round(t, 2), "d": c}, ensure_ascii=False) + "\n")
    (rec_dir / "meta.json").write_text(json.dumps({
        "prompt": run.prompt, "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(run.t0)),
        "seconds": round(run.t1 - run.t0, 1), "tools": [n for n, _ in run.tools], "tokens": run.tokens,
        "files": sorted(p.name for p in files_dir.iterdir())}, indent=1))
