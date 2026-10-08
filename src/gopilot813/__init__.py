"""GoPilot × Challenge 813: everything the notebook needs, behind one import.

    from gopilot813 import gopilot, show, physics

    run = gopilot.ask("Check the gas plant at ... for methane on ...", mission="my_mission")
    show(run, "TITLE")
"""

import subprocess
import sys

from . import config

if config.IN_COLAB:                    # Colab already has numpy, matplotlib, folium and markdown
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "boto3==1.43.37", "rasterio==1.4.3"], check=True)

from IPython.display import HTML, display  # noqa: E402

from .config import MODE, REPO  # noqa: E402
from .console import GoPilot, Run, _ROBOT_SVG  # noqa: E402
from .maps import interactive_map, postcard, show  # noqa: E402
from .physics import physics  # noqa: E402

gopilot = GoPilot(config.GOPILOT_AGENT_ARN, config.GOPILOT_REGION, config.AWS_ACCESS_KEY_ID, config.AWS_SECRET_ACCESS_KEY)

display(HTML(f'<div style="font-family:monospace;color:#00a77d">{_ROBOT_SVG} GoPilot is on the launch pad. '
             f'{config.BANNER}</div>'))

__all__ = ["gopilot", "show", "physics", "postcard", "interactive_map", "GoPilot", "Run", "MODE", "REPO"]
