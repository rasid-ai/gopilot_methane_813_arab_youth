"""Fetch the sample input: a 4 x 4 km clip of the UTGA Tabankourt gas facility, Algeria, from public
Sentinel-2 L2A Cloud-Optimised GeoTIFFs (Element84 Earth Search, AWS Open Data). No account needed.

    python data/sample_input/fetch_sample.py

Writes one GeoTIFF per date (bands B02 B03 B04 B11 B12 at 20 m) and scenes.json. GoPilot itself works on
the Level-1C versions of the same acquisitions; Level-2A is used here because its files are public.
"""
import json
from pathlib import Path

import numpy as np
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

HERE = Path(__file__).parent
SITE = {"name": "UTGA gas treatment facility, Tabankourt, Algeria", "lon": 7.62, "lat": 28.64}
BBOX = [7.5995, 28.622, 7.6405, 28.658]                     # about 4 x 4 km around the site
SCENES = {"target": "S2B_32RLS_20240103_0_L2A",             # the plume date, 0 % cloud
          "reference": "S2A_32RLS_20231229_0_L2A"}          # a clean date 5 days before
ASSETS = {"B02": "blue", "B03": "green", "B04": "red", "B11": "swir16", "B12": "swir22"}
STAC = "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/"


def clip(item_id):
    item = requests.get(STAC + item_id, timeout=60).json()
    bands, profile = [], None
    for name, key in ASSETS.items():
        with rasterio.open(item["assets"][key]["href"]) as src:
            win = from_bounds(*transform_bounds("EPSG:4326", src.crs, *BBOX), transform=src.transform)
            scale = src.res[0] / 20.0                       # resample every band to 20 m
            h, w = int(round(win.height * scale)), int(round(win.width * scale))
            bands.append(src.read(1, window=win, out_shape=(h, w), resampling=Resampling.bilinear))
            if profile is None or name == "B11":
                t = src.window_transform(win)
                profile = dict(driver="GTiff", crs=src.crs, width=w, height=h, count=len(ASSETS), dtype="uint16",
                               transform=t * t.scale(win.width / w, win.height / h), compress="deflate")
    h, w = min(b.shape[0] for b in bands), min(b.shape[1] for b in bands)
    out = HERE / f"{item_id}_tabankourt_4km.tif"
    profile.update(height=h, width=w)
    with rasterio.open(out, "w", **profile) as dst:
        for i, (name, b) in enumerate(zip(ASSETS, bands), 1):
            dst.write(b[:h, :w].astype("uint16"), i)
            dst.set_band_description(i, name)
        dst.update_tags(date=item["properties"]["datetime"][:10], scene_id=item_id, source="Element84 Earth Search, sentinel-2-l2a")
    return out, item["properties"]["datetime"][:10], item["properties"].get("eo:cloud_cover")


if __name__ == "__main__":
    meta = {"site": SITE, "bbox": BBOX, "resolution_m": 20, "bands": list(ASSETS), "scenes": {}}
    for role, item_id in SCENES.items():
        path, day, cloud = clip(item_id)
        meta["scenes"][role] = {"scene_id": item_id, "l1c_scene_id": item_id.replace("_L2A", "_L1C"), "date": day,
                                "cloud_cover": cloud, "file": path.name}
        print(f"{role:9s} {item_id}  {day}  cloud {cloud}%  -> {path.name} ({path.stat().st_size // 1024} KB)")
    (HERE / "scenes.json").write_text(json.dumps(meta, indent=2))
