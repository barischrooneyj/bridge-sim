"""Run FEM simulations and generate responses."""
from __future__ import annotations

import os
from timeit import default_timer as timer
from typing import Callable, Dict, List, TypeVar, Optional

from lib.fem.params import ExptParams, SimParams
from lib.fem.responses import SimResponses
from lib.model.bridge import Bridge
from lib.model.response import ResponseType
from util import print_d, print_i, safe_str, shorten_path

# Print debug information for this file.
D: str = "fem.run"
# D: bool = False

Parsed = TypeVar("Parsed")


class FEMRunner:
    """An interface to run simulations with an external FE program .

    NOTE: For running simulations and loading responses you should instead use
    the higher-level 'load_fem_responses' function, or 'load_expt_responses'
    for parallelization.

    Args:
        supported_response_types: Callable[[Bridge], List[ResponseType]], the
            supported response types for a given bridge.

    """

    def __init__(
        self,
        c: "Config",
        name: str,
        exe_path: str,
        supported_response_types: Callable[[Bridge], List[ResponseType]],
        build: Callable[[Config, ExptParams, FEMRunner], ExptParams],
        run: Callable[[Config, ExptParams, FEMRunner, int], ExptParams],
        parse: Callable[[Config, ExptParams, FEMRunner], Parsed],
        convert: Callable[
            [Config, Parsed], Dict[int, Dict[ResponseType, List[Response]]]
        ],
    ):
        self.c = c
        self.name = name
        self.exe_path = exe_path
        self.supported_response_types = supported_response_types
        self._build = build
        self._run = run
        self._parse = parse
        self._convert = convert

    def run(
        self,
        expt_params: ExptParams,
        return_parsed: bool = False,
        return_converted: bool = False,
    ):
        """Run simulations and save responses using this FEMRunner.

        TODO: Change ExptParams to SimParams.

        Args:
            expt_params: ExptParams, parameters for a number of simulations.
            return_parsed: bool, for testing, return parsed responses.
            return_converted: bool, for testing, return converted responses.

        """

        supported_response_types = self.supported_response_types(self.c.bridge)
        # Check that all FEMParams contain supported response types.
        for fem_params in expt_params.sim_params:
            for response_type in fem_params.response_types:
                if response_type not in supported_response_types:
                    raise ValueError(f"{response_type} not supported by {self.name}")

        # Building.
        start = timer()
        expt_params = self._build(c=self.c, expt_params=expt_params, fem_runner=self,)
        print_i(
            f"FEMRunner: built {self.name} model file(s) in"
            + f" {timer() - start:.2f}s"
        )

        # Running.
        for sim_ind, _ in enumerate(expt_params.sim_params):
            start = timer()
            expt_params = self._run(self.c, expt_params, self, sim_ind)
            print_i(
                f"FEMRunner: ran {self.name}"
                + f" {sim_ind + 1}/{len(expt_params.sim_params)}"
                + f" simulation in {timer() - start:.2f}s"
            )

        # Parsing.
        start = timer()
        parsed_expt_responses = self._parse(self.c, expt_params, self)
        print_i(f"FEMRunner: parsed all responses in" + f" {timer() - start:.2f}s")
        if return_parsed:
            return parsed_expt_responses
        print(parsed_expt_responses[0].keys())

        # Converting.
        start = timer()
        converted_expt_responses = self._convert(
            c=self.c,
            expt_params=expt_params,
            parsed_expt_responses=parsed_expt_responses,
        )
        print_i(
            f"FEMRunner: converted all responses to [Response] in"
            + f" {timer() - start:.2f}s"
        )
        if return_converted:
            return converted_expt_responses
        print(converted_expt_responses[0].keys())

        # Saving.
        for sim_ind in converted_expt_responses:
            print_d(D, f"sim_ind = {sim_ind}")
            for response_type, responses in converted_expt_responses[sim_ind].items():
                print_d(D, f"response_type in converted = {response_type}")
                print(len(responses))
                fem_responses = SimResponses(
                    c=self.c,
                    sim_params=expt_params.sim_params[sim_ind],
                    sim_runner=self,
                    response_type=response_type,
                    responses=responses,
                    build=False,
                )

                start = timer()
                fem_responses.save()
                print_i(
                    f"FEMRunner: saved simulation {sim_ind + 1} SimResponses"
                    + f" in ([Response]) in {timer() - start:.2f}s,"
                    + f"({response_type})"
                )

    def sim_raw_path(
        self,
        sim_params: SimParams,
        ext: str,
        append: str = "",
        dirname: Optional[str] = None,
    ) -> str:
        """A file path for a FE model file or raw simulation responses.

        The file path is based on a Bridge, SimParams and this SimRunner.

        NOTE: you probably don't want this function. Instead you may be
        interested in 'load_fem_responses' or 'fem_responses_path'.

        Args:
            sim_params: SimParams, parameters for a FEM simulation.
            ext: str, a file extension without the dot.
            append: str, appended before the file extension.
            dirname: Optional[str], directory name, default is 'self.name'.

        """
        param_str = sim_params.id_str()
        append = append if len(append) == 0 else f"-{append}"
        filename = f"{self.c.bridge.id_str()}-params={param_str}{append}"
        if len(sim_params.refinement_radii) > 0:
            filename += "-refined"
        if dirname is None:
            dirname = self.name
        dirname = safe_str(dirname)
        return shorten_path(
            self.c, safe_str(self.c.get_data_path(dirname, filename)) + f".{ext}"
        )

    def sim_out_path(
        self,
        sim_params: SimParams,
        ext: str,
        dirname: Optional[str] = None,
        append: str = "",
        response_types: List[ResponseType] = [],
    ) -> str:
        """Like 'sim_raw_path', however response types are overridden.

        Intended for output files from FE simulations where we don't care what
        other response types were recorded.

        Args:
            sim_params: SimParams, parameters for a FEM simulation.
            ext: str, a file extension without the dot.
            append: str, appended before the file extension.
            dirname: Optional[str], directory name, default is 'self.name' +
                "-responses".
            response_types: List[ResponseType], override the response types
                in the SimParams.

        """
        original_response_types = sim_params.response_types
        sim_params.response_types = response_types
        if dirname is None:
            dirname = self.name + "-responses"
        result = self.sim_raw_path(
            sim_params=sim_params, ext=ext, dirname=dirname, append=append
        )
        sim_params.response_types = original_response_types
        return result