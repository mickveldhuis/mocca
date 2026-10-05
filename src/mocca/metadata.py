import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import numpy as np


@dataclass
class TelescopeInfo:
    """This clas represents the telescope's geometry."""

    height: float  # distance floor-HA axis (L_1)
    ha_axis_offset: float  # distance HA axis-Dec axis (L_2)
    dec_axis_offset: float  # distance Dec axis-tube center (L_3)
    guider_offset: float  # distance primary tube center-guider center (L_4)
    finder_offset: float  # distance guider center-finder center (L_5)
    guider_angle: float
    finder_angle: float

    aperture_radius: float
    aperture_sec_radius: float
    guider_radius: float
    guider_sec_radius: float
    finder_radius: float

    latitude: float  # observatory latitude in degrees

    @classmethod
    def from_file(cls, path: Path) -> Self:
        with path.open("rb") as config_file:
            config = tomllib.load(config_file)

            L_1 = config["mount"].get("length_1")  # distance floor-HA axis
            L_2 = config["mount"].get("length_2")  # distance HA axis-Dec axis
            L_3 = config["mount"].get("length_3")  # distance Dec axis-tube center
            L_4 = config["guider"].get(
                "offset"
            )  # distance primary tube center-guider center
            L_5 = config["finder"].get("offset")  # distance guider center-finder center

            guider_angle = np.radians(config["guider"].get("angle"))
            finder_angle = np.radians(config["finder"].get("angle"))

            aperture_radius = config["telescope"].get("diameter") / 2
            aperture_sec_radius = config["telescope"].get("sec_diameter") / 2

            guider_radius = config["guider"].get("diameter") / 2
            guider_sec_radius = config["guider"].get("sec_diameter") / 2

            finder_radius = config["finder"].get("diameter") / 2

            latitude = config[
                "observatory"
            ].get(
                "latitude"
            )  # Observatory latitude in degrees, as expected by the transformations defined in transformations.py

            return cls(
                L_1,
                L_2,
                L_3,
                L_4,
                L_5,
                guider_angle,
                finder_angle,
                aperture_radius,
                aperture_sec_radius,
                guider_radius,
                guider_sec_radius,
                finder_radius,
                latitude,
            )


@dataclass
class DomeInfo:
    """This class describes the geometry of a hemispherical dome."""

    dome_radius: float  # dome radius in meters
    dome_extent: float  # extent of the cylindrical dome wall in meters
    dome_slit_width: float  # slit width in meters

    @classmethod
    def from_file(cls, path: Path) -> Self:
        with path.open("rb") as config_file:
            config = tomllib.load(config_file)

            radius = config["dome"].get("diameter") / 2  # radius
            extent = config["dome"].get("extent")  # extent of cylindrical dome wall
            slit_width = config["dome"].get("slit_width")  # Slit width

            return cls(radius, extent, slit_width)
