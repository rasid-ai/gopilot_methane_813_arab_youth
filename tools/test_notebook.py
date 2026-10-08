"""Test the notebook's own code, offline, in a temporary copy of the repo.

    python tools/test_notebook.py

1. LIVE: a simulated GoPilot stream (its real wire format, links "signed" like S3's) is flown with
   GOPILOT_RECORD=1, so it records itself to results/. The recording must hold no signed link.
2. REPLAY: with no credentials, the same mission replays from that recording, and its layers map from local files.
3. A mission with no recording shows "NO RECORDING" instead of failing; the physics cell runs on the sample input.
"""

import contextlib
import functools
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_notebook as B  # noqa: E402

LON, LAT = 7.62, 28.64
RAMP = ('<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" version="1.0.0">'
        '<UserLayer><sld:UserStyle><sld:FeatureTypeStyle><sld:Rule><sld:RasterSymbolizer><sld:ColorMap type="ramp">'
        '<sld:ColorMapEntry quantity="0" color="#000004" opacity="0"/><sld:ColorMapEntry quantity="0.1" color="#b63679"/>'
        '<sld:ColorMapEntry quantity="0.2" color="#fcfdbf"/></sld:ColorMap></sld:RasterSymbolizer></sld:Rule>'
        '</sld:FeatureTypeStyle></sld:UserStyle></UserLayer></StyledLayerDescriptor>')
POLY = ('<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:se="http://www.opengis.net/se" version="1.1.0">'
        '<NamedLayer><UserStyle><se:FeatureTypeStyle><se:Rule><se:PolygonSymbolizer><se:Fill>'
        '<se:SvgParameter name="fill">#02462C</se:SvgParameter></se:Fill><se:Stroke>'
        '<se:SvgParameter name="stroke">#232323</se:SvgParameter></se:Stroke></se:PolygonSymbolizer></se:Rule>'
        '</se:FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>')


def make_layers(d):
    t = from_origin(LON - 0.02, LAT + 0.02, 0.0001, 0.0001)
    idx = np.random.default_rng(0).normal(0, 0.02, (400, 400)).astype("float32")
    idx[150:220, 180:260] += 0.15
    with rasterio.open(d / "utga_mbmp_20240103.tif", "w", driver="GTiff", height=400, width=400, count=1,
                       dtype="float32", crs="EPSG:4326", transform=t) as f:
        f.write(idx, 1)
    plume = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"class": "Class1", "area_m2": 52000},
             "geometry": {"type": "Polygon", "coordinates": [[[LON, LAT], [LON + 0.01, LAT + 0.002], [LON + 0.01, LAT - 0.004],
                                                             [LON, LAT - 0.003], [LON, LAT]]]}}]}
    (d / "utga_methane_20240103.geojson").write_text(json.dumps(plume))


def stream(port):
    sig = "?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAEXAMPLE%2F20240103&X-Amz-Signature=deadbeef"
    names = ["utga_mbmp_20240103.tif", "utga_methane_20240103.geojson"]
    links = "".join(f"\n- [{n}](http://127.0.0.1:{port}/{n}{sig})" for n in names)
    meta = {names[0]: {"visualization": True, "sld": RAMP}, names[1]: {"visualization": True, "sld": POLY}}
    chunks = ["<think>\n", "Locating the UTGA facility at Tabankourt.", "\n</think>\n",
              '<tool id="0" status="processing">geocode</tool>\n', '<tool id="0" status="done">geocode</tool>\n',
              '<tool id="1" status="processing">detect_methane_plumes_goserver</tool>\n', '<beat>"alive"</beat>\n',
              '<tool id="1" status="done">detect_methane_plumes_goserver</tool>\n',
              f"<final>\n**One plume** near the facility.\n\n### ⬇️ Download\n{links}</final>",
              "\n<total_tokens>51000</total_tokens>\n", f"\n```file-meta\n{json.dumps(meta)}\n```"]
    return [("data: " + json.dumps(c)).encode() for c in chunks]


class Body:
    def __init__(self, lines):
        self.lines = lines

    def iter_lines(self, chunk_size=32):
        for line in self.lines:
            yield line


def run_cells(cells, g):
    for src in cells:
        code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("%"))
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            exec(compile(code, "<cell>", "exec"), g)


def main():
    work = Path(tempfile.mkdtemp(prefix="gp813_repo_"))
    repo = work / "repo"
    shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".git", "results"))
    (repo / "results").mkdir()
    serve_dir = work / "served"
    serve_dir.mkdir()
    make_layers(serve_dir)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(serve_dir)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    checks = []
    check = lambda name, ok, detail="": checks.append((name, bool(ok), detail))
    os.chdir(repo)

    # 1. live, recording
    import boto3
    real = boto3.client
    boto3.client = lambda *a, **k: type("RT", (), {"invoke_agent_runtime": lambda self, **kw: {"response": Body(stream(port))}})()
    os.environ.update(AWS_ACCESS_KEY_ID="AKIATEST", AWS_SECRET_ACCESS_KEY="x", GOPILOT_RECORD="1",
                      GOPILOT_AGENT_ARN="arn:aws:bedrock-agentcore:eu-central-1:111122223333:runtime/test-abc")
    g = {}
    try:
        run_cells([B.PY_SETUP, B.PY_CONSOLE, B.PY_MAPS, B.PY_M1], g)
    finally:
        boto3.client = real
    live = g["mission_1"]
    rec = repo / "results" / "mission_1_methane_tabankourt"
    check("live: mode was live", g["MODE"] == "live")
    check("live: mission completed", live.done and not live.error, live.error)
    check("live: recording written", (rec / "stream.jsonl").exists() and (rec / "meta.json").exists())
    text = (rec / "stream.jsonl").read_text()
    check("recording holds no signed link", "X-Amz" not in text and "127.0.0.1" not in text)
    check("recording keeps its layers", sorted(p.name for p in (rec / "files").iterdir()) ==
          ["utga_mbmp_20240103.tif", "utga_methane_20240103.geojson"])

    # 2. replay, no credentials
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "GOPILOT_AGENT_ARN", "GOPILOT_RECORD"):
        os.environ.pop(k, None)
    g = {}
    run_cells([B.PY_SETUP, B.PY_CONSOLE, B.PY_MAPS, B.PY_M1], g)
    rep = g["mission_1"]
    html = rep.to_html()
    check("replay: mode is replay (creds.env placeholders ignored)", g["MODE"] == "replay")
    check("replay: same quests and answer", rep.tools == live.tools and "One plume" in rep.final_md)
    check("replay: console says REPLAY and COMPLETE", "REPLAY ×" in html and "MISSION COMPLETE" in html)
    layers = g["_load"](rep, 512)
    check("replay: layers load from local files", sorted(k for _, k, _, _ in layers) == ["raster", "vector"])
    card = g["postcard"](rep, layers, "TABANKOURT")
    check("replay: postcard renders", card is not None and len(card.data) > 10_000)
    mhtml = g["interactive_map"](layers).get_root().render()
    check("replay: map embeds layers, no links", "data:image/" in mhtml and "127.0.0.1" not in mhtml and "#02462C" in mhtml)

    # 3. a mission never recorded, and the physics cell
    run_cells([B.PY_PALMS], g)
    check("missing recording: no crash, shows NO RECORDING", g["mission_2"].missing and "NO RECORDING" in g["mission_2"].to_html())
    import matplotlib
    matplotlib.use("Agg")
    run_cells([B.PY_PHYSICS], g)
    check("physics cell: frac computed on the sample input", np.isfinite(g["frac"]).mean() > 0.95, g["frac"].shape)

    srv.shutdown()
    w = max(len(c[0]) for c in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{w}}  {'' if ok else detail}")
    print(f"\n{sum(ok for _, ok, _ in checks)}/{len(checks)} passed · temp repo: {repo}")
    return all(ok for _, ok, _ in checks)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
