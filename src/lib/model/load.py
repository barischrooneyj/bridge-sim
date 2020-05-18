"""Loads and vehicles"""
from itertools import chain
from typing import List, Optional, Tuple, Union


import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt

from lib.model.bridge import Bridge, Point
from util import assert_sorted, flatten, round_m, safe_str

# Comment/uncomment to print debug statements for this file.
# D: str = "model.load"
D: bool = False


class PierSettlement:
    """Apply a load to a pier until a vertical translation is reached.

    Args:
        displacement: float, displacement in meters.
        pier: int, index of a pier on a bridge.

    """

    def __init__(self, displacement: float, pier: int):
        self.displacement = displacement
        self.pier = pier

    def id_str(self):
        return safe_str(f"{self.displacement:.3f}-{self.pier}")


class PointLoad:
    """A load concentrated at a point on the deck.

    Args:
        x_frac: float, fraction of x position on bridge in [0 1].
        z_frac: float, fraction of z position on bridge in [0 1].
        kn: float, load intensity in kilo Newton.

    """

    def __init__(self, x_frac: float, z_frac: float, kn: float):
        self.x_frac = x_frac
        self.z_frac = z_frac
        self.kn = kn

    def id_str(self):
        """String uniquely representing this load."""
        return f"({self.x_frac:.4f}, {self.z_frac:.4f}, {self.kn:.3f})"

    def repr(self, bridge: Bridge):
        x = round_m(bridge.x(self.x_frac))
        z = round_m(bridge.z(self.z_frac))
        return f"x={x}, z={z}, kN={self.kn}"

    def point(self, bridge: Bridge) -> Point:
        """A 'Point' on the deck from this 'PointLoad'."""
        return Point(x=bridge.x(self.x_frac), y=0, z=bridge.z(self.z_frac))


class Vehicle:
    """A vehicle's geometry.

    Args:
        kn: Union[float, List[float], List[Tuple[float, float]]], load
            intensity, either for the entire vehicle or per axle, or as a list
            of tuple (per wheel, each tuple is left then right wheel), in kilo
            Newton.
        axle_distances: List[float], distance between axles in meters.
        axle_width: float, width of the vehicle's axles in meters.

    Attrs:

        length: float, length of the vehicle in meters.
        num_axles: int, number of axles.
        total_kn: Callable[[], float], total load intensity in kilo Newton.
        kn_per_axle: Callable[[], [List[float]]], load intensity per axle in
            kilo Newton.
        # wheel_length: float, length of each wheel in meters, default 0.31 m.

    """

    def __init__(
        self,
        kn: Union[float, List[float], List[Tuple[float, float]]],
        axle_distances: List[float],
        axle_width: float,
    ):
        self.axle_distances = axle_distances
        self.axle_width = axle_width
        self.length = sum(self.axle_distances)
        self.num_axles = len(self.axle_distances) + 1
        self.num_wheels = self.num_axles * 2
        self.kn = kn
        # self.wheel_length = 0.31

        def total_kn():
            if isinstance(self.kn, list):
                if isinstance(self.kn[0], tuple):
                    return sum(chain.from_iterable(self.kn))
                return sum(self.kn)
            return self.kn

        def kn_per_axle():
            if isinstance(self.kn, list):
                if isinstance(self.kn[0], tuple):
                    return list(map(sum, self.kn))
                return self.kn
            return [(self.kn / self.num_axles) for _ in range(self.num_axles)]

        def kn_per_wheel():
            if isinstance(self.kn, list):
                if isinstance(self.kn[0], tuple):
                    return self.kn
                return list(map(lambda kn: (kn / 2, kn / 2), self.kn))
            wheel_kn = self.kn / self.num_wheels
            return [(wheel_kn, wheel_kn) for _ in range(self.num_axles)]

        self.total_kn = total_kn
        self.kn_per_axle = kn_per_axle
        self.kn_per_wheel = kn_per_wheel

    def cmap_norm(self, all_vehicles: List["Vehicle"], cmin=0, cmax=1):
        """The colormap and norm for coloring vehicles."""
        from plot import truncate_colormap

        cmap = truncate_colormap(cm.get_cmap("YlGn"), cmin, cmax)
        total_kns = [v.total_kn() for v in all_vehicles] + [self.total_kn()]
        norm = colors.Normalize(vmin=min(total_kns), vmax=max(total_kns))
        return cmap, norm

    def color(self, all_vehicles: List["Vehicle"]):
        """Color of this vehicle scaled based on given vehicles."""
        cmap, norm = self.cmap_norm(all_vehicles)
        if len(all_vehicles) == 0:
            return cmap(0.5)
        return cmap(norm(self.total_kn()))


class MvVehicle(Vehicle):
    """A moving vehicle, has a speed and position on a bridge.

    Position is determined by an initial position in the longitudinal direction
    of the bridge, by an index to a lane on that bridge and by a constant speed.

    NOTE: Arguments that determine initial position, 'lane' and 'init_x_frac',
        are optional and may be set later.

    Args:
        kn: Union[float, List[float], List[Tuple[float, float]]], load
            intensity, either for the entire vehicle or per axle, or as a list
            of tuple (per wheel, each tuple is left then right wheel), in kilo
            Newton.
        axle_distances: List[float], distance between axles in meters.
        axle_width: float, width of the vehicle's axles in meters.
        kmph: float, speed of the vehicle in kmph.
        lane: Optional[int], index of a lane on a bridge.
        init_x_frac: Optional[float], initial position on the lane as a fraction
            of x position of the bridge, may be negative but not greater than 1.
            Regardless of the direction of traffic on the lane, the position at
            0 is just as the vehicle is about to move onto the bridge.

    Attrs:
        mps: float, speed of the vehicle in mps.
        length: float, length of the vehicle in meters.
        num_axles: int, number of axles.

    """

    def __init__(
        self,
        kn: Union[float, List[float], List[Tuple[float, float]]],
        axle_distances: List[float],
        axle_width: float,
        kmph: float,
        lane: Optional["Lane"] = None,
        init_x_frac: float = 0,
    ):
        super().__init__(kn=kn, axle_distances=axle_distances, axle_width=axle_width)
        self.kmph = kmph
        self.mps = self.kmph / 3.6  # Meters per second.
        self.lane = lane
        self.init_x_frac = init_x_frac
        assert self.init_x_frac <= 1

    def wheel_tracks_zs(self, bridge: Bridge, meters: bool) -> Tuple[float, float]:
        """Positions of the vehicle's wheels in transverse direction.

        Args:
            bridge: Bridge, the bridge on which the vehicle is moving.
            meters: bool, whether to return positions in meters (True) or
                fractions (False) of the bridge width in [0 1].

        """
        lane = bridge.lanes[self.lane]
        tracks = [
            lane.z_center - (self.axle_width / 2),
            lane.z_center + (self.axle_width / 2),
        ]
        if meters:
            return tracks
        return list(map(lambda z: bridge.z_frac(z), tracks))

    def x_frac_at(self, time: float, bridge: Bridge) -> List[float]:
        """Fraction of x position of bridge in meters at given time.

        Args:
            time: float, time passed from initial position, in seconds.
            bridge: Bridge, bridge the vehicle is moving on.

        """
        delta_x_frac = (self.mps * time) / bridge.length
        init_x_frac = self.init_x_frac
        if bridge.lanes[self.lane].ltr:
            return init_x_frac + delta_x_frac
        else:
            init_x_frac *= -1  # Make positive, move to right of bridge start.
            init_x_frac += 1  # Move one bridge length to the right.
            return init_x_frac - delta_x_frac

    def x_at(self, time: float, bridge: Bridge):
        """X position of front axle on bridge at given time, in meters.

        Args:
            time: float, time passed from initial position, in seconds.
            bridge: Bridge, bridge the vehicle is moving on.

        """
        return bridge.x(self.x_frac_at(time=time, bridge=bridge))

    def xs_at(self, time: float, bridge: Bridge):
        """X position on bridge for each axle in meters at given time."""
        if not hasattr(self, "_xs_at_time"):
            xs = [self.x_at(time=time, bridge=bridge)]
            # Determine the distance between each pair of axles.
            delta_xs = np.array(self.axle_distances)
            if bridge.lanes[self.lane].ltr:
                delta_xs *= -1
                delta_xs = reversed(delta_xs)
            # Add the distance for each axle, after the front axle.
            for delta_x in delta_xs:
                xs.append(xs[-1] + delta_x)
            self._xs_at_time = np.array(xs)
        delta_x_time = self.x_at(time=time, bridge=bridge) - self._xs_at_time[0]
        return sorted(self._xs_at_time + delta_x_time)

    def x_fracs_at(self, time: float, bridge: Bridge):
        """Fraction of x position of bridge for each axle at given time."""
        return list(map(bridge.x_frac, self.xs_at(time=time, bridge=bridge)))

    def on_bridge(self, time: float, bridge: Bridge) -> bool:
        """Whether a moving load is on a bridge at a given time."""
        x_fracs = list(map(bridge.x_frac, self.xs_at(time=time, bridge=bridge)))
        # Left-most and right-most vehicle positions as fractions.
        xl_frac, xr_frac = min(x_fracs), max(x_fracs)
        return 0 <= xl_frac <= 1 or 0 <= xr_frac <= 1

    def full_lanes(self, time: float, bridge: Bridge) -> float:
        """The amount of bridge lanes travelled by this vehicle."""
        x_fracs = list(map(bridge.x_frac, self.xs_at(time=time, bridge=bridge)))
        # Left-most and right-most vehicle positions as fractions.
        xl_frac, xr_frac = min(x_fracs), max(x_fracs)
        if bridge.lanes[self.lane].ltr:
            return xl_frac
        else:
            return abs(xr_frac - 1)

    def passed_bridge(self, time: float, bridge: Bridge) -> bool:
        """Whether the current vehicle has travelled over the bridge."""
        return self.full_lanes(time=time, bridge=bridge) > 1

    def time_at(self, x, bridge: Bridge):
        """Time the front axle is at the given x position."""
        if not bridge.lanes[self.lane].ltr:
            raise NotImplementedError()
        init_x = bridge.x(self.init_x_frac)
        assert init_x < x
        return float(abs(init_x - x)) / self.mps

    def time_entering_bridge(self, bridge: Bridge):
        """Time the vehicle begins to enter the bridge."""
        init_x = bridge.x(self.init_x_frac)
        assert init_x <= 0
        return float(abs(init_x)) / self.mps

    def time_entered_bridge(self, bridge: Bridge):
        """Time the vehicle has entered the bridge."""
        init_x = bridge.x(self.init_x_frac)
        assert init_x <= 0
        return float(abs(init_x) + self.length) / self.mps

    def time_leaving_bridge(self, bridge: Bridge):
        """Time the vehicle begins to leave the bridge."""
        init_x = bridge.x(self.init_x_frac)
        assert init_x <= 0
        return float(abs(init_x) + bridge.length) / self.mps

    def time_left_bridge(self, bridge: Bridge):
        """Time the vehicle has left the bridge."""
        init_x = bridge.x(self.init_x_frac)
        assert init_x <= 0
        return float(abs(init_x) + bridge.length + self.length) / self.mps

    def to_wheel_track_xs(
        self, c: "Config", wheel_x: float, wheel_track_xs: Optional[List[float]] = None
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """X positions (and weighting) of unit loads for a x position.

        This implements wheel track bucketing!

        """
        wheel_x = round_m(wheel_x)
        if wheel_track_xs is None:
            wheel_track_xs = c.bridge.wheel_track_xs(c)
        unit_load_x_ind = np.searchsorted(wheel_track_xs, wheel_x)
        unit_load_x = lambda: wheel_track_xs[unit_load_x_ind]
        if unit_load_x() > wheel_x:
            unit_load_x_ind -= 1
        assert unit_load_x() <= wheel_x
        # If the unit load is an exact match just return it.
        if np.isclose(wheel_x, unit_load_x()):
            return ((wheel_x, 1), (0, 0))
        # Otherwise, return a combination of two unit loads. In this case the
        # unit load's position is less than the wheel.
        unit_load_x_lo = unit_load_x()
        unit_load_x_hi = wheel_track_xs[unit_load_x_ind + 1]
        assert unit_load_x_hi > wheel_x
        dist_lo = abs(unit_load_x_lo - wheel_x)
        dist_hi = abs(unit_load_x_hi - wheel_x)
        dist = dist_lo + dist_hi
        return ((unit_load_x_lo, dist_hi / dist), (unit_load_x_hi, dist_lo / dist))

    def to_wheel_track_loads_(
        self,
        c: "Config",
        time: float,
        flat: bool = False,
        wheel_track_xs: Optional[List[float]] = None,
    ):
        """Load intensities and positions per axle, per wheel.

        "Bucketed" to fit onto wheel tracks.

        NOTE: In each tuple of two point loads, one tuple per wheel, each point
        load is for a unit load position in the wheel track. Each point load is
        weighted by the distance to the unit load.

        """
        if wheel_track_xs is None:
            wheel_track_xs = c.bridge.wheel_track_xs(c)
        xs = self.xs_at(time=time, bridge=c.bridge)
        kns = self.kn_per_axle()
        result = []
        assert len(xs) == len(kns)
        # For each axle.
        for x, kn in zip(xs, kns):
            # Skip axle if not on the bridge.
            if x < c.bridge.x_min or x > c.bridge.x_max:
                continue
            left, right = [], []
            for (load_x, load_frac) in self.to_wheel_track_xs(
                c=c, wheel_x=x, wheel_track_xs=wheel_track_xs,
            ):
                if load_frac > 0:
                    bucket_kn = kn / 2 * load_frac
                    left.append((load_x, bucket_kn))
                    right.append((load_x, bucket_kn))
            result.append((left, right))
        if flat:
            return flatten(result, PointLoad)
        return result

    def to_wheel_track_loads(
        self, c: "Config", time: float, flat: bool = False
    ) -> List[Tuple[List[PointLoad], List[PointLoad]]]:
        z0, z1 = self.wheel_tracks_zs(bridge=c.bridge, meters=False)
        assert z0 < z1
        result = []
        for axle_loads in self.to_wheel_track_loads_(c=c, time=time):
            left, right = [], []
            left_loads, right_loads = axle_loads
            for load_x, load_kn in left_loads:
                left.append(
                    PointLoad(x_frac=c.bridge.x_frac(load_x), z_frac=z0, kn=load_kn,)
                )
            for load_x, load_kn in right_loads:
                right.append(
                    PointLoad(x_frac=c.bridge.x_frac(load_x), z_frac=z1, kn=load_kn,)
                )
            result.append((left, right))
        if flat:
            return flatten(result, PointLoad)
        return result

    def to_point_load_pw(
        self, time: float, bridge: Bridge, list: bool = False
    ) -> List[Tuple[PointLoad, PointLoad]]:
        """A tuple of point load per axle, one point load per wheel."""
        z0, z1 = self.wheel_tracks_zs(bridge=bridge, meters=False)
        assert z0 < z1
        kn_per_axle = self.kn_per_axle()
        result = []
        # For each axle.
        for x_i, x in enumerate(self.xs_at(time=time, bridge=bridge)):
            # Skip axle if not on the bridge.
            if x < bridge.x_min or x > bridge.x_max:
                continue
            # Two wheel load intensities.
            kn_wheel = kn_per_axle[x_i] / 2
            x_frac = bridge.x_frac(x)
            result.append(
                (
                    PointLoad(x_frac=x_frac, z_frac=z0, kn=kn_wheel),
                    PointLoad(x_frac=x_frac, z_frac=z1, kn=kn_wheel),
                )
            )
        if list:
            return flatten(result, PointLoad)
        return result

    def plot_wheels(self, c: "Config", time: float, label=None, **kwargs):
        wheel_loads = self.to_point_load_pw(time=time, bridge=c.bridge, flat=True)
        for i, load in enumerate(wheel_loads):
            x, z = c.bridge.x(load.x_frac), c.bridge.z(load.z_frac)
            plt.scatter(
                [x],
                [z],
                facecolors="none",
                edgecolors="black",
                label=None if i > 0 else label,
                **kwargs,
            )