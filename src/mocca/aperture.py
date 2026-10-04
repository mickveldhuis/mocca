import sys

import numpy as np
from pytransform3d import transformations as pt

from mocca.metadata import Metadata
from mocca.transformations import rot_x, rot_z, transform, vec3, vec4
from mocca.visualise import plot_aperture_obstruction


def create_aperture(aperture_type: str, rate: int, metadata: Metadata):
    """Factory method for creating an Aperture instance."""
    match aperture_type:
        case "telescope":
            return TelescopeAperture(metadata, rate=rate)
        case "guider":
            return GuiderAperture(metadata, rate=rate)
        case "finder":
            return FinderAperture(metadata, rate=rate)
        case _:
            sys.exit(1)


class Aperture:
    """Class representing the telescope aperture.

    Public methods
    --------------

    obstruction (float): return the % obstruction of the aperture by the dome
    get_name (str): return an aperture "name"/identifier
    """

    def __init__(
        self, metadata: Metadata, radius: float, sec_radius: float = 0, rate: int = 3
    ):
        """ "The Aperture class constructor.

        Parameters
        ----------

        radius (float): aperture radius in meters
        sec_radius (float): radius of secondary obstruction in meters
        rate (int): aperture sample rate (in terms of no. radial circles around the center)
        metadata (Metadata):
        """
        self.radius = radius
        self.sec_radius = sec_radius
        self.sample_rate = rate

        self._name = None

        self.meta = metadata

    def _transform(self, ha: float, dec: float):
        """ "Get the transformation matrix to the aperture.

        Parameters
        ----------

        ha (float): hour angle in degrees
        dec (float): declination in degrees
        """
        L_1 = self.meta.height
        L_2 = self.meta.ha_axis_offset
        L_3 = self.meta.dec_axis_offset
        lat = self.meta.latitude

        H_01 = transform(0, 0, L_1)
        H_12 = rot_x(90 - lat) @ rot_z(-ha) @ transform(0, 0, L_2)
        H_23 = rot_x(dec) @ transform(-L_3, 0, 0)

        H = H_01 @ H_12 @ H_23

        return H

    def _sample_disk(self, r_min: float = 0):
        """
        Equidistant disk sampling based on:
        http://www.holoborodko.com/pavel/2015/07/23/generating-equidistant-points-on-unit-disk/

        Parameters
        ----------

        r_min (float): ratio of the circle that is obstructed at the center
        """
        if not 0 <= r_min < 1:
            raise ValueError("r_min should be between 0 and 1...")

        dr = 1 / self.sample_rate

        x = np.empty(0)
        y = np.empty(0)

        rs = np.linspace(r_min, 1, self.sample_rate)
        k = np.ceil(r_min * (self.sample_rate + 1))

        if not r_min:
            x = np.concatenate([x, [0]])
            y = np.concatenate([y, [0]])

            rs = np.linspace(dr, 1, self.sample_rate)
            k = 1

        for r in rs:
            n = int(np.round(np.pi / np.arcsin(1 / (2 * k))))

            theta = np.linspace(0, 2 * np.pi, n + 1)

            x_r = r * np.cos(theta)
            y_r = r * np.sin(theta)

            x = np.concatenate([x, x_r])
            y = np.concatenate([y, y_r])

            k += 1

        xy = self.radius * np.column_stack([x, y])

        return xy

    def direction(self, ha: float, dec: float):
        """
        Return the pointing direction of the aperture
        in the frame of the dome.

        Parameters
        ----------

        ha (float): hour angle in degrees
        dec (float): declination in degrees
        """
        H_ap = self._transform(ha, dec)
        H_unit = transform(0, 1, 0)

        H_diff = H_ap @ H_unit - H_ap

        direction = H_diff @ vec4(0, 0, 0)

        return vec3(direction)

    def sample(self, ha: float, dec: float):
        """
        Compute the position of a vector in
        the aperture's frame.

        Parameters
        ----------

        ha (float): hour angle in degrees
        dec (float): declination in degrees
        x (float ndarray): x coordinate of a point in the aperture
        z (float ndarray): z coordinate of a point in the aperture
        """
        # Sample points in a disk; resembling the aperture
        ap_xz = self._sample_disk(r_min=self.sec_radius / self.radius)
        ap_x, ap_z = ap_xz.T

        # Transfor those points to the aperture frame
        x = -ap_x
        y = np.zeros(ap_x.size)
        z = ap_z
        ones = np.ones(ap_x.size)
        points = np.column_stack((x, y, z, ones))

        pose_matrix = self._transform(ha, dec)

        product = pt.transform(pose_matrix, points)

        return product[:, :3]

    def visualise(self, blocked_rays: np.ndarray, dome_az: float):
        # Resample points in a disk resembling the aperture
        ap_xz = self._sample_disk(r_min=self.sec_radius / self.radius)
        ap_x, ap_z = ap_xz.T

        plot_aperture_obstruction(ap_x, ap_z, blocked_rays, self.radius, dome_az)

    def get_name(self):
        """Return aperture identifier."""
        return self._name


class TelescopeAperture(Aperture):
    """Primary aperture."""

    def __init__(self, metadata: Metadata, rate: int = 4):
        super().__init__(
            metadata,
            metadata.aperture_radius,
            sec_radius=metadata.aperture_sec_radius,
            rate=rate,
        )

        self._name = "telescope"


class GuiderAperture(Aperture):
    """Autoguider aperture."""

    def __init__(self, metadata: Metadata, rate: int = 3):
        super().__init__(
            metadata,
            metadata.guider_radius,
            sec_radius=metadata.guider_sec_radius,
            rate=rate,
        )

        self._name = "guider"

    def _transform(self, ha: float, dec: float):
        # Get aperture geometry
        L_4 = self.meta.guider_offset
        angle = self.meta.guider_angle

        # Transform telescope aperture to guider aperture
        H_34 = transform(L_4 * np.cos(angle), 0, L_4 * np.sin(angle))

        # Get the telescope aperture pose
        H_telescope = super()._transform(ha, dec)

        H = H_telescope @ H_34

        return H


class FinderAperture(Aperture):
    """Finderscope aperture."""

    def __init__(self, metadata: Metadata, rate: int = 3):
        super().__init__(metadata, metadata.finder_radius, rate=rate)

        self._name = "finder"

    def _transform(self, ha: float, dec: float):
        # Get aperture geometry
        L_4 = self.meta.guider_offset
        L_5 = self.meta.finder_offset

        guider_angle = self.meta.guider_angle
        finder_angle = self.meta.guider_angle

        # Transform telescope aperture to guider aperture & guider to finder
        H_34 = transform(L_4 * np.cos(guider_angle), 0, L_4 * np.sin(guider_angle))
        H_45 = transform(-L_5 * np.cos(finder_angle), 0, L_5 * np.sin(finder_angle))

        # Get the telescope aperture pose
        H_telescope = super()._transform(ha, dec)

        H = H_telescope @ H_34 @ H_45

        return H
