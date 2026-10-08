"""Result layers: a static postcard that shows on any screen, and an interactive map."""

import base64
import json
import re
import io
import math
from xml.etree import ElementTree as ET

import folium
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import requests
from IPython.display import Image as _Image
from IPython.display import display
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
        return [c[0]] if c and c[0] else []
    if t == "MultiPolygon":
        return [p[0] for p in c if p and p[0]]
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
                gj = _to_wgs84(json.loads(data))
                # A model can emit a degenerate polygon with no coordinates; it has nothing to draw.
                gj["features"] = [f for f in gj.get("features", []) if _rings(f.get("geometry") or {})]
                layers.append((name, "vector", gj, meta))
        except Exception as e:
            print(f"⚠️ {name}: not drawn ({type(e).__name__})")
    return layers


def _extent(layers, min_span=3000.0):
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
    # At least min_span metres across: a 50 m plume needs its facility around it, and the basemap
    # service has no imagery finer than that in many deserts.
    pad = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.12
    l, b, r, t = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    cx, cy, half = (l + r) / 2, (b + t) / 2, min_span / 2
    return min(l, cx - half), min(b, cy - half), max(r, cx + half), max(t, cy + half)


def _basemap(ext, px=1400):
    l, b, r, t = ext
    w = px if (r - l) >= (t - b) else int(px * (r - l) / (t - b))
    h = int(w * (t - b) / (r - l))
    for scale in (1.0, 0.5):                    # the export service sometimes refuses the larger size
        try:
            res = requests.get(ESRI_EXPORT, timeout=60, params={
                "bbox": f"{l},{b},{r},{t}", "bboxSR": 3857, "imageSR": 3857,
                "size": f"{int(w * scale)},{int(h * scale)}", "format": "jpg", "f": "image"})
            if res.ok and res.headers.get("content-type", "").startswith("image"):
                return np.asarray(Image.open(io.BytesIO(res.content)).convert("RGB"))
        except Exception:
            pass
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
                # A feature too small to see at this scale gets a locator ring, so a 50 m plume still stands out.
                span = max(r - l, t - b)
                for poly in polys:
                    xy = poly.get_xy()
                    if max(np.ptp(xy[:, 0]), np.ptp(xy[:, 1])) < 0.06 * span and len(polys) <= 20:
                        ax.add_patch(plt.Circle(xy.mean(0), 0.05 * span, fill=False, ec="#ffcc4d", lw=2.2, zorder=4))
            legend.append((name, color, len(p.get("features", []))))
    ax.set_xlim(l, r); ax.set_ylim(b, t); ax.set_axis_off()
    ax.set_title(title, color="#ffcc4d", fontsize=14, family="monospace", loc="left", pad=10)
    txt = "   ".join(f"■ {n.rsplit('-', 1)[0]} ({c} features)" for n, _, c in legend) or "   ".join(n for n, *_ in layers)
    fig.text(0.01, 0.01, txt[:150], color="#cfe9ff", fontsize=9, family="monospace")
    fig.text(0.99, 0.01, "Imagery © Esri, Maxar · Contains modified Copernicus Sentinel data", color="#5b7aa6", fontsize=7, ha="right")
    buf = io.BytesIO()                          # JPEG: a photo basemap is 2 MB as PNG, a few hundred KB as JPEG
    fig.savefig(buf, format="jpg", bbox_inches="tight", facecolor=fig.get_facecolor(), pil_kwargs={"quality": 85})
    plt.close(fig)
    return _Image(buf.getvalue(), format="jpeg")


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

