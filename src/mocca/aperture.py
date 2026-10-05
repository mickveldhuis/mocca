import numpy as np
from pytransform3d import transformations as pt

from mocca.metadata import TelescopeInfo
from mocca.transformations import rot_x, rot_z, transform, vec3, vec4
from mocca.utils import sample_unit_disk


def create_aperture(
    aperture_type: str, rate: int, telescope_info: TelescopeInfo
) -> Aperture:
    """Factory method for creating an Aperture instance."""
    match aperture_type:
        case "telescope":
            return TelescopeAperture(telescope_info, rate=rate)
        case "guider":
            return GuiderAperture(telescope_info, rate=rate)
        case "finder":
            return FinderAperture(telescope_info, rate=rate)
        case _:
            raise ValueError("Unknown aperture type")


class Aperture:
    """Class representing the telescope aperture."""

    def __init__(
        self, info: TelescopeInfo, radius: float, sec_radius: float = 0, rate: int = 3
    ) -> None:
        """
        Construct a telescope aperture.

        :param radius: aperture radius in meters
        :param sec_radius: radius of secondary mirror in meters
        :param rate: aperture sample rate (in terms of the number of radial circles around the center)
        :param info: metadata object with the telescope's geometrical properties
        """
        self.radius = radius
        self.sec_radius = sec_radius
        self.sample_rate = rate

        self.info = info

        self._id = None

    def transformation(self, ha: float, dec: float) -> np.ndarray:
        """
        Calculate the transformation matrix from
        the aperture to the dome frame.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: aperture-to-dome transformation matrix
        """
        H = transform(0.0, 0.0, 0.0)  # unit transformation matrix

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

    def sample(self, ha: float, dec: float) -> np.ndarray:
        """
        Compute the position of a vector in
        the aperture's frame.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: the aperture sampled in the dome frame
        """
        inner_blocked_radius = self.sec_radius / self.radius
        unit_disk = sample_unit_disk(self.sample_rate, r_min=inner_blocked_radius)
        disk = self.radius * unit_disk

        # Transform these samples to the aperture frame
        n_samples = disk.shape[1]

        x = -disk[0]
        y = np.zeros(n_samples)
        z = disk[1]
        ones = np.ones(n_samples)
        points = np.column_stack((x, y, z, ones))

        pose_matrix = self.transformation(ha, dec)

        product = pt.transform(pose_matrix, points)

        return product[:, :3]

    def identifier(self) -> str:
        """Return aperture identifier."""
        return self._id


class TelescopeAperture(Aperture):
    """Primary aperture."""

    def __init__(self, info: TelescopeInfo, rate: int = 4) -> None:
        super().__init__(
            info,
            info.aperture_radius,
            sec_radius=info.aperture_sec_radius,
            rate=rate,
        )

        self._id = "telescope"

    def transformation(self, ha: float, dec: float) -> np.ndarray:
        L_1 = self.info.height
        L_2 = self.info.ha_axis_offset
        L_3 = self.info.dec_axis_offset
        lat = self.info.latitude

        H_01 = transform(0, 0, L_1)
        H_12 = rot_x(90 - lat) @ rot_z(-ha) @ transform(0, 0, L_2)
        H_23 = rot_x(dec) @ transform(-L_3, 0, 0)

        H = H_01 @ H_12 @ H_23

        return H


class GuiderAperture(Aperture):
    """Autoguider aperture."""

    def __init__(self, info: TelescopeInfo, rate: int = 3) -> None:
        super().__init__(
            info,
            info.guider_radius,
            sec_radius=info.guider_sec_radius,
            rate=rate,
        )

        self._id = "guider"

    def transformation(self, ha: float, dec: float) -> np.ndarray:
        # Get the telescope aperture pose
        H_telescope = super().transformation(ha, dec)

        # Get aperture geometry
        L_4 = self.info.guider_offset
        angle = self.info.guider_angle

        # Transform telescope aperture to guider aperture
        H_34 = transform(L_4 * np.cos(angle), 0, L_4 * np.sin(angle))

        H = H_telescope @ H_34

        return H


class FinderAperture(Aperture):
    """Finderscope aperture."""

    def __init__(self, info: TelescopeInfo, rate: int = 3) -> None:
        super().__init__(info, info.finder_radius, rate=rate)

        self._id = "finder"

    def transformation(self, ha: float, dec: float) -> np.ndarray:
        # Get the telescope aperture pose
        H_telescope = super().transformation(ha, dec)

        # Get aperture geometry
        L_4 = self.info.guider_offset
        L_5 = self.info.finder_offset

        guider_angle = self.info.guider_angle
        finder_angle = self.info.finder_angle

        # Transform telescope aperture to guider aperture & guider to finder
        H_34 = transform(L_4 * np.cos(guider_angle), 0, L_4 * np.sin(guider_angle))
        H_45 = transform(-L_5 * np.cos(finder_angle), 0, L_5 * np.sin(finder_angle))

        H = H_telescope @ H_34 @ H_45

        return H
