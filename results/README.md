# Recorded GoPilot missions

One folder per mission, written by a live run with `GOPILOT_RECORD=1`:

| File | What it is |
|---|---|
| `stream.jsonl` | GoPilot's stream, chunk by chunk, with the time each arrived (s). Signed download links are replaced by local `files/…` paths. |
| `files/` | The layers GoPilot returned: plume polygons (GeoJSON), index rasters (GeoTIFF). |
| `meta.json` | The prompt, the date recorded, how long it took, the tools called and the token count. |

Without credentials, the notebook replays these through the same console and maps.
