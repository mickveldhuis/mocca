from abc import abstractmethod
from typing import Protocol, runtime_checkable

import numpy as np

from mocca.transformations import rot_x, rot_z, transform, vec3, vec4


@runtime_checkable
class Transformable(Protocol):
    """Protocol for defining classes that contain mount transformation."""

    @abstractmethod
    def transformation(self, ha: float, dec: float) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def direction(self, ha: float, dec: float) -> np.ndarray:
        raise NotImplementedError


class EquatorialMount(Transformable):
    def __init__(self, base_mount):
        pass

    def transformation(self, ha: float, dec: float) -> np.ndarray:
        """
        Calculate the transformation matrix from
        the aperture to the dome frame.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: aperture-to-dome transformation matrix
        """
        L_1 = self.info.height
        L_2 = self.info.ha_axis_offset
        L_3 = self.info.dec_axis_offset
        lat = self.info.latitude

        H_01 = transform(0, 0, L_1)
        H_12 = rot_x(90 - lat) @ rot_z(-ha) @ transform(0, 0, L_2)
        H_23 = rot_x(dec) @ transform(-L_3, 0, 0)

        H = H_01 @ H_12 @ H_23

        return H

    def direction(self, ha: float, dec: float) -> np.ndarray:
        """
        Return the pointing direction of the aperture
        in the frame of the dome.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: pointing vector in the dome frame
        """
        H_ap = self.transformation(ha, dec)
        H_unit = transform(0, 1, 0)

        H_diff = H_ap @ H_unit - H_ap

        aperture_origin = vec4(0, 0, 0)
        direction = H_diff @ aperture_origin

        return vec3(direction)


class CompositeMount(Transformable):
    def __init__(self, base_transform: Transformable):
        pass
