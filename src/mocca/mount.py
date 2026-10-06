from abc import abstractmethod
from typing import Protocol, Self, runtime_checkable

import numpy as np

from mocca.metadata import TelescopeInfo
from mocca.transformations import rot_x, rot_z, translation


@runtime_checkable
class Transformable(Protocol):
    """Protocol for defining classes that contain mount transformation."""

    @abstractmethod
    def transformation(self, ha: float, dec: float) -> np.ndarray:
        """
        Calculate the transformation matrix from
        the aperture to the dome frame.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: aperture-to-dome transformation matrix
        """
        raise NotImplementedError


class EquatorialMount(Transformable):
    def __init__(
        self,
        height: float,
        ha_axis_offset: float,
        dec_axis_offset: float,
        latitude: float,
    ) -> None:
        self.height = height
        self.ha_axis_offset = ha_axis_offset
        self.dec_axis_offset = dec_axis_offset
        self.latitude = latitude

    def transformation(self, ha: float, dec: float) -> np.ndarray:
        """
        Calculate the transformation matrix from
        the aperture to the dome frame.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: aperture-to-dome transformation matrix
        """
        H_01 = translation(0, 0, self.height)
        H_12 = (
            rot_x(90 - self.latitude)
            @ rot_z(-ha)
            @ translation(0, 0, self.ha_axis_offset)
        )
        H_23 = rot_x(dec) @ translation(-self.dec_axis_offset, 0, 0)

        H = H_01 @ H_12 @ H_23

        return H

    @classmethod
    def from_telescope_info(cls, info: TelescopeInfo) -> Self:
        """Create an EquatorialMount from a TelescopeInfo object."""
        return EquatorialMount(
            info.height, info.ha_axis_offset, info.dec_axis_offset, info.latitude
        )


class CompositeMount(Transformable):
    def __init__(self, base: Transformable, offset: float, angle: float):
        self.base_mount = base
        self.offset = offset
        self.angle = angle

    def transformation(self, ha: float, dec: float) -> np.ndarray:
        """
        Calculate the transformation matrix from
        the aperture to the dome frame.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: aperture-to-dome transformation matrix
        """
        H_base = self.base_mount.transformation(ha, dec)
        H_offset = translation(
            self.offset * np.cos(self.angle), 0, self.offset * np.sin(self.angle)
        )

        return H_base @ H_offset
