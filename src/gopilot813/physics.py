"""The textbook methane signal by hand, on the committed sample input: why a trained model is needed."""

import io
import json

import matplotlib.pyplot as plt
import numpy as np
import rasterio

from .config import REPO


def physics():
    """Raw B12/B11 drop between the sample's reference and target dates, next to the true-colour image."""
    sample = json.loads((REPO / "data" / "sample_input" / "scenes.json").read_text())

    def read(role):
        with rasterio.open(REPO / "data" / "sample_input" / sample["scenes"][role]["file"]) as r:
            return r.read().astype(float)               # bands B02 B03 B04 B11 B12

    tgt, ref = read("target"), read("reference")
    ratio = lambda a: a[4] / np.maximum(a[3], 1)       # B12 / B11
    frac = 1 - ratio(tgt) / np.maximum(ratio(ref), 1e-6)   # > 0 where B12 darkened, as methane would make it
    frac -= np.median(frac)
    rgb = np.clip(tgt[[2, 1, 0]].transpose(1, 2, 0) / np.percentile(tgt[[2, 1, 0]], 99), 0, 1)
    fig, ax = plt.subplots(1, 2, figsize=(11, 5.2), facecolor="#070b1a")
    ax[0].imshow(rgb)
    ax[0].set_title(f"Sentinel-2, {sample['scenes']['target']['date']}", color="#cfe9ff", family="monospace")
    ax[1].imshow(frac, cmap="magma", vmin=0, vmax=np.percentile(frac, 99.7))
    ax[1].set_title(f"raw B12/B11 drop vs {sample['scenes']['reference']['date']}", color="#ffcc4d", family="monospace")
    for a in ax:
        a.axis("off")
    plt.tight_layout()
    buf = io.BytesIO()                          # JPEG keeps the saved notebook light
    fig.savefig(buf, format="jpg", facecolor=fig.get_facecolor(), pil_kwargs={"quality": 88})
    plt.close(fig)
    from IPython.display import Image, display
    display(Image(buf.getvalue(), format="jpeg"))
    return frac
