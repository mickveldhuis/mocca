from abc import abstractmethod
from typing import Protocol, Self, runtime_checkable

import numpy as np

from mocca.metadata import TelescopeInfo
from mocca.transformations import rot_x, rot_y, rot_z, translation


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
        """
        Create an Equatorial base mount for calculating the transformation
        matrix from the dome frame to the telescope's optical axis.

        :param height: distance from the floor to the HA axis
        :param ha_axis_offset: distance from the HA axis to the intersection with the Dec axis
        :param dec_axis_offset: distance from HA-Dec axis intersection to the optical axis
        """
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
        H_01 = translation(0.0, 0.0, self.height)
        H_12 = (
            rot_x(90.0 - self.latitude)
            @ rot_z(-ha)
            @ translation(0.0, 0.0, self.ha_axis_offset)
        )
        H_23 = rot_x(dec) @ translation(-self.dec_axis_offset, 0.0, 0.0)

        H = H_01 @ H_12 @ H_23

        return H

    @classmethod
    def from_telescope_info(cls, info: TelescopeInfo) -> Self:
        """Create an EquatorialMount from a TelescopeInfo object."""
        return EquatorialMount(
            info.height, info.ha_axis_offset, info.dec_axis_offset, info.latitude
        )

    def __repr__(self):
        return f"EquatorialMount(height={self.height}, ha_axis_offset={self.ha_axis_offset}, dec_axis_offset={self.dec_axis_offset}, latitude={self.latitude})"


class CompositeMount(Transformable):
    def __init__(self, base: Transformable, offset: float, angle: float):
        """
        Create a mount for an aperture with an offset respect to a base mount, e.g.
        to model a finderscope on top of the telescope on an equatorial mount.

        :param base: base mount
        :param offset: radial offset in the xz-plane
        :param angle: angle (deg) of the rotation about the y-axis
        """
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

        H_offset = rot_y(self.angle) @ translation(0.0, 0.0, self.offset)

        return H_base @ H_offset

    def __repr__(self):
        return f"CompositeMount(base={self.base_mount}, offset={self.offset}, angle={self.angle})"
