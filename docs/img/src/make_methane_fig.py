import numpy as np
X0, X1, L0, L1 = 80, 730, 1500, 2500
Y1, Y0 = 175, 420
x = lambda l: X0 + (l - L0) * (X1 - X0) / (L1 - L0)
y = lambda t: Y0 - (t - 0.55) * (Y0 - Y1) / 0.45
lam = np.arange(L0, L1 + 1, 2.0)
g = lambda c, w: np.exp(-((lam - c) / w) ** 2)
comb = 0.78 + 0.22 * np.cos(2 * np.pi * (lam - 2200) / 22)
T = 1 - 0.07 * g(1666, 9) - 0.04 * g(1640, 25) - 0.33 * g(2330, 75) * comb - 0.10 * g(2230, 40) * comb
path = "M" + " L".join("%.1f,%.1f" % (x(l), y(t)) for l, t in zip(lam, T))
ticks = "".join('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>' % (x(l), Y0 + 14, x(l), Y0 + 40) for l in np.arange(1505, 2496, 8.5))
xt = "".join('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#5b7aa6"/><text x="%.1f" y="%d" fill="#9fb8d6" font-size="15" text-anchor="middle">%d</text>'
             % (x(l), Y0, x(l), Y0 + 6, x(l), Y0 + 62, l) for l in range(1500, 2501, 250))
b11 = (x(1565), x(1655)); b12 = (x(2100), x(2280))
steps = [("#3aa0ff", "PHYSICS", "radiative transfer from ESA band responses and HITRAN: 57 lookup tables"),
         ("#ff5a9e", "SIMULATE", "25,000 plumes inserted into real Sentinel-2 scenes, 500 to 50,000 kg/h"),
         ("#59ff9c", "LEARN", "CompUNet reads the target date against clean reference dates"),
         ("#ffcc4d", "DETECT", "plume mask and size; 75%+ of confirmed real plumes recovered")]
steps_svg = ""
for i, (c, t, d) in enumerate(steps):
    steps_svg += ('<g transform="translate(820,%d)"><rect width="720" height="78" rx="14" fill="#0f2240" stroke="%s" stroke-width="2"/>'
                  '<circle cx="40" cy="39" r="22" fill="%s"/><text x="40" y="47" fill="#070b1a" font-size="22" font-weight="bold" text-anchor="middle" class="mono">%d</text>'
                  '<text x="80" y="34" fill="%s" font-size="19" font-weight="bold" class="mono">%s</text>'
                  '<text x="80" y="60" fill="#cfe9ff" font-size="16">%s</text></g>') % (140 + i * 92, c, c, i + 1, c, t, d)
V = dict(X0=X0, X1=X1, Y0=Y0, Y1=Y1, path=path, ticks=ticks, xt=xt, steps=steps_svg,
         b11x=b11[0], b11w=b11[1] - b11[0], b12x=b12[0], b12w=b12[1] - b12[0],
         b11c=(b11[0] + b11[1]) / 2, b12c=(b12[0] + b12[1]) / 2, wvx=x(1800), wvw=x(1950) - x(1800), wvc=x(1875),
         ch4x=x(2330) + 8, ch4y=y(0.60), mid=(X0 + X1) / 2, top=Y1 - 20, h=Y0 - Y1 + 20)
html = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:#070b1a} text{font-family:"DejaVu Sans",Arial,sans-serif} .mono{font-family:"DejaVu Sans Mono",monospace}
</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="720" viewBox="0 0 1600 720">
 <defs><radialGradient id="bg" cx="40%%" cy="40%%" r="80%%"><stop offset="0" stop-color="#12234a"/><stop offset="1" stop-color="#060914"/></radialGradient>
 <filter id="glow" x="-20%%" y="-20%%" width="140%%" height="140%%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
 <rect width="1600" height="720" rx="28" fill="url(#bg)"/>
 <text x="56" y="62" fill="#7CFFCB" font-size="20" letter-spacing="6" class="mono">METHANEMAPPER · HOW IT SEES METHANE</text>
 <text x="%(X0)d" y="112" fill="#cfe9ff" font-size="22" font-weight="bold">Methane darkens the shortwave infrared</text>
 <rect x="%(b11x).1f" y="%(top)d" width="%(b11w).1f" height="%(h)d" fill="#3aa0ff" opacity=".22"/>
 <rect x="%(b12x).1f" y="%(top)d" width="%(b12w).1f" height="%(h)d" fill="#3aa0ff" opacity=".22"/>
 <text x="%(b11c).1f" y="%(Y0)d" dy="-12" fill="#3aa0ff" font-size="18" font-weight="bold" text-anchor="middle" class="mono">B11</text>
 <text x="%(b12c).1f" y="%(Y0)d" dy="-12" fill="#3aa0ff" font-size="18" font-weight="bold" text-anchor="middle" class="mono">B12</text>
 <rect x="%(wvx).1f" y="%(top)d" width="%(wvw).1f" height="%(h)d" fill="#ffffff" opacity=".05"/>
 <text x="%(wvc).1f" y="%(Y0)d" dy="-12" fill="#5b7aa6" font-size="13" text-anchor="middle">water vapour</text>
 <line x1="%(X0)d" y1="%(Y0)d" x2="%(X1)d" y2="%(Y0)d" stroke="#2a4a7b" stroke-width="2"/>
 %(xt)s
 <text x="%(mid).1f" y="%(Y0)d" dy="90" fill="#9fb8d6" font-size="15" text-anchor="middle">wavelength (nm)</text>
 <path d="%(path)s" fill="none" stroke="#ffcc4d" stroke-width="3" filter="url(#glow)"/>
 <text x="%(ch4x).1f" y="%(ch4y).1f" fill="#ffcc4d" font-size="17" font-weight="bold">CH₄ absorbs</text>
 <text x="%(X0)d" y="%(Y0)d" dx="8" dy="-48" fill="#ffcc4d" font-size="14" opacity=".85">curve: light reaching the satellite through a plume</text>
 <g stroke="#ff5a9e" stroke-width="1.6" opacity=".9">%(ticks)s</g>
 <text x="%(X0)d" y="%(Y0)d" dy="128" fill="#3aa0ff" font-size="17"><tspan font-weight="bold">Sentinel-2 today:</tspan> 2 broad bands. B12 darkens against B11.</text>
 <text x="%(X0)d" y="%(Y0)d" dy="156" fill="#ff5a9e" font-size="17"><tspan font-weight="bold">Hyperspectral (Satellite 813, EnMAP):</tspan> hundreds of narrow</text>
 <text x="%(X0)d" y="%(Y0)d" dy="180" fill="#ff5a9e" font-size="17">bands that trace the absorption itself, as the pink ticks show.</text>
 <text x="%(X1)d" y="%(Y0)d" dy="232" fill="#5b7aa6" font-size="12" text-anchor="end">illustrative spectrum</text>
 <text x="820" y="112" fill="#cfe9ff" font-size="22" font-weight="bold">Trained on physics, not on scarce labels</text>
 %(steps)s
 <g transform="translate(820,520)">
   <rect width="720" height="150" rx="16" fill="#1d1a08" stroke="#ffcc4d" stroke-width="2.5"/>
   <text x="24" y="40" fill="#ffcc4d" font-size="19" font-weight="bold" class="mono">WHY METHANE, WHY THIS CHALLENGE</text>
   <text x="24" y="74" fill="#f6ecc8" font-size="17">MethaneMapper already runs on Sentinel-2: free, global, every 5 days.</text>
   <text x="24" y="102" fill="#f6ecc8" font-size="17">The same approach moves to hyperspectral data, including</text>
   <text x="24" y="130" fill="#f6ecc8" font-size="17"><tspan fill="#ffcc4d" font-weight="bold">Satellite 813</tspan>: smaller leaks, and fewer false alarms.</text>
 </g>
</svg></body></html>""" % V
open("src/methane_model.html", "w").write(html)
print("written")
