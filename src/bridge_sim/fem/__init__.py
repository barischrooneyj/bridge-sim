from typing import List, Optional

from bridge_sim.model import PierSettlement, PointLoad, ResponseType
from lib.config import Config as LibConfig
from lib.fem.params import SimParams as LibSimParams
from lib.fem.responses import load_fem_responses as lib_load_fem_responses


def responses(
    config: LibConfig,
    response_type: ResponseType,
    point_loads: List[PointLoad] = [],
    pier_settle: Optional[PierSettlement] = None,
):
    """Responses from a single linear simulation.

    The simulation is only run if necessary (results not on disk).

    :param config: Global configuration object.
    :param response_type: Sensor response type to return.
    :param point_loads: Point loads to apply in simulation.
    :param pier_settle: A pier settlement to apply.
    :return: Sensor responses from the simulation.
    """
    return lib_load_fem_responses(
        c=config,
        sim_params=LibSimParams(ploads=point_loads, displacement_ctrl=pier_settle),
        response_type=response_type,
    )
