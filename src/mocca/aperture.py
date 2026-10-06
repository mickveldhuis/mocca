import numpy as np
from pytransform3d import transformations as pt

from mocca.metadata import TelescopeInfo
from mocca.mount import CompositeMount, EquatorialMount, Transformable
from mocca.transformations import translation, vec3, vec4
from mocca.utils import sample_unit_disk


def create_aperture(
    aperture_type: str, rate: int, telescope_info: TelescopeInfo
) -> Aperture:
    """Factory method for creating an Aperture instance."""
    mount = EquatorialMount.from_telescope_info(telescope_info)

    match aperture_type:
        case "telescope":
            return Aperture(
                mount,
                telescope_info.aperture_radius,
                sec_radius=telescope_info.aperture_sec_radius,
                rate=rate,
            )
        case "guider":
            guider_mount = CompositeMount(
                mount, telescope_info.guider_offset, telescope_info.guider_angle
            )
            return Aperture(
                guider_mount,
                telescope_info.guider_radius,
                sec_radius=telescope_info.guider_sec_radius,
                rate=rate,
            )
        case "finder":
            # H_34 = translation(L_4 * np.cos(guider_angle), 0, L_4 * np.sin(guider_angle))
            # H_45 = translation(-L_5 * np.cos(finder_angle), 0, L_5 * np.sin(finder_angle))
            guider_mount = CompositeMount(
                mount, telescope_info.guider_offset, telescope_info.guider_angle
            )
            finder_mount = CompositeMount(
                guider_mount, telescope_info.finder_offset, telescope_info.finder_angle
            )
            return Aperture(
                finder_mount,
                telescope_info.finder_radius,
                sec_radius=0.0,
                rate=rate,
            )
        case _:
            raise ValueError("Unknown aperture type")


class Aperture:
    """Class representing the telescope aperture."""

    def __init__(
        self, mount: Transformable, radius: float, sec_radius: float = 0, rate: int = 3
    ) -> None:
        """
        Construct a telescope aperture.

        :param radius: aperture radius in meters
        :param sec_radius: radius of secondary mirror in meters
        :param rate: aperture sample rate (in terms of the number of radial circles around the center)
        :param info: metadata object with the telescope's geometrical properties
        """
        self.mount = mount
        self.radius = radius
        self.sec_radius = sec_radius
        self.sample_rate = rate

    def transformation(self, ha: float, dec: float) -> np.ndarray:
        """
        Calculate the transformation matrix from the aperture
        to the dome frame using the appropriate mount.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: aperture-to-dome transformation matrix
        """
        return self.mount.transformation(ha, dec)

    def direction(self, ha: float, dec: float) -> np.ndarray:
        """
        Return the pointing direction of the aperture
        in the frame of the dome.

        :param ha: hour angle in degrees
        :param dec: declination in degrees
        :returns: pointing vector in the dome frame
        """
        H_ap = self.transformation(ha, dec)
        H_unit = translation(0, 1, 0)

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
