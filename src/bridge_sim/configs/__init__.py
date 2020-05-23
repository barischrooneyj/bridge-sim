import os
from typing import Callable, Optional

import findup

from bridge_sim.model import Config, Bridge
from lib.fem.run.opensees import os_runner
from bridge_sim.util import project_dir


def opensees_default(
    bridge: Callable[[], Bridge], os_exe: Optional[str] = None, **kwargs
) -> Config:
    """A Config using OpenSees for a given Bridge.

    Args:
        bridge: function to return a new bridge.
        os_exe: absolute path to OpenSees binary.
        kwargs: passed on to Config constructor.
    """
    return Config(
        bridge=bridge,
        sim_runner=os_runner(os_exe),
        vehicle_data_path=os.path.join(project_dir(), "data/traffic/traffic.csv"),
        vehicle_pdf=[
            (2.4, 5),
            (5.6, 45),
            (7.5, 30),
            (9, 15),
            (11.5, 4),
            (12.2, 0.5),
            (43, 0),
        ],
        vehicle_pdf_col="length",
        **kwargs,
    )
