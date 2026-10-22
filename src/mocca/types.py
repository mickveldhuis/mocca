import logging
import tomllib
from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

import h5py
import numpy as np

logger = logging.getLogger("MOCCA")


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

            guider_angle = config["guider"].get("angle")
            finder_angle = config["finder"].get("angle")

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

    radius: float  # dome radius in meters
    extent: float  # extent of the cylindrical dome wall in meters
    slit_width: float  # slit width in meters

    @classmethod
    def from_file(cls, path: Path) -> Self:
        with path.open("rb") as config_file:
            config = tomllib.load(config_file)

            radius = config["dome"].get("diameter") / 2  # radius
            extent = config["dome"].get("extent")  # extent of cylindrical dome wall
            slit_width = config["dome"].get("slit_width")  # Slit width

            return cls(radius, extent, slit_width)


# Named tuple to immutably store the result of the obstruction calculation.
ObstructionResult = namedtuple("ObstructionResult", ["ratio", "mask"])


@dataclass
class BatchObstructionResult:
    ratios: np.ndarray
    masks: np.ndarray

    ha: np.ndarray
    dec: np.ndarray
    az: np.ndarray

    def to_hdf5(self, file: Path | None = None) -> None:
        """
        Write an obstruction cube to disk as a HDF5 dataset.

        :param directory: path to the directory in which to store the result
        """
        shape = (self.ha.size, self.dec.size, self.az.size)

        if self.ratios.ndim != 3 or self.ratios.shape != shape:
            raise ValueError(
                f"expecting an array of obstruction fractions of shape {shape}, but got {self.ratios.shape}"
            )

        date_tag = datetime.now(UTC).strftime("%Y%M%d%H%M%S")
        filename = f"{date_tag}_mocca_cube.h5"
        output_path = Path.cwd() / filename if file is None else file

        with h5py.File(output_path, "w") as h5_file:
            h5_file.attrs["timestamp"] = date_tag

            obstruction_ds = h5_file.create_dataset("obstruction", data=self.ratios)
            # TODO: add additional metadata as attributes, e.g. aperture identifier,
            # dome config, number of rays, and other simulation parameters.

            # Setup axes and create dimension scales
            ha_ds = h5_file.create_dataset("ha", data=self.ha)
            ha_ds.make_scale()
            ha_ds.attrs["unit"] = "deg"

            dec_ds = h5_file.create_dataset("dec", data=self.dec)
            dec_ds.make_scale()
            dec_ds.attrs["unit"] = "deg"

            az_ds = h5_file.create_dataset("az", data=self.az)
            az_ds.make_scale()
            az_ds.attrs["unit"] = "deg"

            # Attach dimension scales
            obstruction_ds.dims[0].attach_scale(ha_ds)
            obstruction_ds.dims[1].attach_scale(dec_ds)
            obstruction_ds.dims[2].attach_scale(az_ds)

        logger.info("batch obstruction result written to %s", output_path)
