import configparser

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Metadata:
    """This clas represents the metadata required for computing the telescope-dome geometry."""

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

    dome_radius: float  # dome radius in meters
    dome_extent: float  # extent of the cylindrical dome wall in meters
    dome_slit_width: float  # slit width in meters

    latitude: float  # observatory latitude in degrees

    @classmethod
    def from_ini(cls, path: Path):
        config = configparser.ConfigParser()
        config.read(path)

        # Telescope:
        L_1 = config["mount"].getfloat("length_1")  # distance floor-HA axis
        L_2 = config["mount"].getfloat("length_2")  # distance HA axis-Dec axis
        L_3 = config["mount"].getfloat("length_3")  # distance Dec axis-tube center
        L_4 = config["guider"].getfloat(
            "offset"
        )  # distance primary tube center-guider center
        L_5 = config["finder"].getfloat(
            "offset"
        )  # distance guider center-finder center

        guider_angle = np.radians(config["guider"].getfloat("angle"))
        finder_angle = np.radians(config["finder"].getfloat("angle"))

        aperture_radius = config["telescope"].getfloat("diameter") / 2
        aperture_sec_radius = config["telescope"].getfloat("sec_diameter") / 2

        guider_radius = config["guider"].getfloat("diameter") / 2
        guider_sec_radius = config["guider"].getfloat("sec_diameter") / 2

        finder_radius = config["finder"].getfloat("diameter") / 2

        # Dome:
        radius = config["dome"].getfloat("diameter") / 2  # radius
        extent = config["dome"].getfloat("extent")  # extent of cylindrical dome wall
        slit_width = config["dome"].getfloat("slit_width")  # Slit width

        # Observatory:
        latitude = config["observatory"].getfloat("latitude")  # degrees

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
            radius,
            extent,
            slit_width,
            latitude,
        )
