import sys

import numpy as np
from pytransform3d import transformations as pt

from mocca.metadata import Metadata
from mocca.raytracting import find_intersection, get_ray_intersection
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

        # Add a vectorized instance of the _is_ray_blocked function
        self._is_blocked = np.vectorize(
            self._is_ray_blocked, signature="(d),(),(),()->()"
        )

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

    def _sample_aperture(self, ha: float, dec: float, x: np.ndarray, z: np.ndarray):
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
        y = np.zeros(x.size)
        dummy = np.ones(x.size)
        points = np.column_stack((x, y, z, dummy))

        pose_matrix = self._transform(ha, dec)

        product = pt.transform(pose_matrix, points)

        return product[:, :3]

    def _aperture_direction(self, ha: float, dec: float):
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

    def _is_ray_blocked(self, point: np.ndarray, ha: float, dec: float, dome_az: float):
        """
        Checks whether an individual ray is blocked.

        Parameters
        ----------

        point (3-vector): ray origin
        ha (float): hour angle in degrees
        dec (float): declination in degrees
        dome_az (float): dome azimuth (clockwise convention)
        """
        is_blocked = True

        direction = self._aperture_direction(ha, dec)

        dome_radius = self.meta.dome_radius
        dome_extent = self.meta.dome_extent
        dome_slit_width = self.meta.dome_slit_width
        has_intersection, t = find_intersection(
            point, direction, dome_radius, dome_extent
        )

        if has_intersection:
            points = get_ray_intersection(point, direction, t)

            az_corrected = (
                dome_az - 180
            ) % 360  # Correction assuming the azimuth is zero at the South
            rot = rot_z(az_corrected)

            dummy = np.ones(points[0].size)
            pp = np.column_stack((points[0], points[1], points[2], dummy))

            product = pt.transform(rot, pp)

            r = dome_radius * np.sin(np.radians(15))

            x_cond = -dome_slit_width / 2 < product[:, 0] < dome_slit_width / 2
            y_cond = -r < product[:, 1] < dome_radius

            is_ray_in_slit = points[2] > dome_extent and x_cond and y_cond

            if is_ray_in_slit:
                is_blocked = False

        return is_blocked

    def obstruction(
        self, ha: float, dec: float, dome_az: float, plot_result: bool = False
    ):
        """
        Compute the % obstruction of the aperture by the dome.

        Parameters
        ----------

        ha (float): hour angle in degrees
        dec (float): declination in degrees
        dome_az (float): dome azimuth (clockwise convention)
        plot_result (bool): if True, a plot with the sampled aperture and obstructed points will be shown
        """
        ratio = None

        # Sample points in a disk; resembling the aperture
        ap_xz = self._sample_disk(r_min=self.sec_radius / self.radius)

        ap_x, ap_z = ap_xz.T

        # Transfor those points to the aperture frame
        ap_pos = self._sample_aperture(ha, dec, -ap_x, ap_z)

        # Compute the no. rays, emanating from those points, blocked by the dome
        blocked = self._is_blocked(ap_pos, ha, dec, dome_az)

        ratio = blocked[blocked].size / blocked.size

        if plot_result:
            plot_aperture_obstruction(ap_x, ap_z, blocked, self.radius, dome_az)

        return ratio

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
