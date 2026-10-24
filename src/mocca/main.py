import importlib
import logging
import sys
from pathlib import Path

import numpy as np

from mocca.aperture import Aperture, create_aperture
from mocca.cli import parse_cli_arguments
from mocca.obstruction import batch_calculate_obstruction, calculate_obstruction
from mocca.types import DomeInfo, TelescopeInfo
from mocca.visualise import plot_aperture_obstruction, plot_batch_obstruction

logger = logging.getLogger("MOCCA")


MOCCA_CONFIG = "mocca.toml"


def create_configuration_file() -> Path:
    """Create a MOCCA configuration file in the current working directory."""
    user_config = Path.cwd() / MOCCA_CONFIG

    if not user_config.exists():
        logger.warning(
            "%s not found in the current working directory; creating one at: %s",
            MOCCA_CONFIG,
            user_config,
        )

        default_config = Path(__file__).parent / MOCCA_CONFIG
        default_config.copy(user_config)

    return user_config


def load_configuration_file(config_filename: str | None) -> Path:
    """
    Load the MOCCA configuration TOML file. Fall back to mocca.toml
    in the current working directory, if it exists.
    """
    if config_filename:
        user_config = Path(config_filename).resolve()

        if not user_config.exists():
            raise FileNotFoundError(
                f"the provided MOCCA configuration file {user_config} does not exist"
            )

        return user_config

    # If the user didn't specify a configuration file, look in the current
    # working directory, and create one if it doesn't exist.
    user_config = Path.cwd() / MOCCA_CONFIG

    return user_config


def process_single_azimuth(
    ha: float,
    dec: float,
    az: float,
    aperture: Aperture,
    dome: DomeInfo,
    visualise: bool = False,
):
    """
    Calculate the obstruction for a single dome orientation and telescope pointing, and optionally plot the results.

    :param ha: telescope hour angle (deg)
    :param dec: telescope declination (deg)
    :param az: dome orientation angle (deg)
    :param aperture: aperture configuration
    :param dome: dome properties
    :param visualise: enable plotting the aperture obstruction
    """
    blockage, blocked_rays = calculate_obstruction(ha, dec, az, aperture, dome)

    if blockage is not None:
        logger.info("%s aperture obstruction = %.3f", aperture.identifier, blockage)
    else:
        raise RuntimeError("The fractional obstruction could not be computed")

    if visualise:
        plot_aperture_obstruction(aperture, blocked_rays, az)


def process_batch(
    ha: float,
    dec: float,
    az_values: np.ndarray,
    aperture: Aperture,
    dome: DomeInfo,
    output_path: Path | None,
    visualise: bool = False,
):
    """
    Calculate the obstruction for a multiple dome orientation given as single telescope pointing.

    :param ha: telescope hour angle (deg)
    :param dec: telescope declination (deg)
    :param az_values: list of dome orientations (deg)
    :param aperture: aperture configuration
    :param dome: dome properties
    """
    batch_result = batch_calculate_obstruction(ha, dec, az_values, aperture, dome)

    # Display the fraction of obstructed rays for each sampled dome orientation
    is_obstructed = np.isclose(batch_result.ratios, 1.0)

    n_azimuths = batch_result.ratios.size
    n_obstructed = is_obstructed.sum()

    logger.info(
        "%s aperture obstructed for %i / %i sampled dome positions",
        aperture.identifier,
        n_obstructed,
        n_azimuths,
    )

    batch_result.to_hdf5(file=output_path)

    if visualise:
        # FIXME: currently the batch calculation produces a cube of shape (1, 1, N),
        # but this won't hold in the future when we allow processing multiple (ha, dec)
        # pairs simultaneously.
        plot_batch_obstruction(batch_result.ratios[0, 0, :], batch_result.az)


def main():
    # Configure the logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
    )

    # Parse CLI arguments
    args = parse_cli_arguments()

    version = importlib.metadata.version("mocca")
    logger.info("running MOCCA version %s", version)

    if args.init_config:
        create_configuration_file()

    # Load the telescope-dome configuration from the provided TOML file
    config_path = load_configuration_file(args.config)

    try:
        logger.info(
            "loading telescope and dome parameters from %s", config_path.resolve()
        )
        telescope_info = TelescopeInfo.from_file(config_path)
        dome_info = DomeInfo.from_file(config_path)
    except FileNotFoundError:
        logger.error("the configuration file could not be found!")
        sys.exit()

    # Compute and (optionally) visualise the obstruction
    aperture = create_aperture(args.aperture, args.rate, telescope_info)

    match args.command:
        case "calc":
            process_single_azimuth(
                args.ha,
                args.dec,
                args.az,
                aperture,
                dome_info,
                visualise=args.inspect,
            )
        case "scan":
            process_batch(
                args.ha,
                args.dec,
                args.az_range,
                aperture,
                dome_info,
                args.output,
                visualise=args.inspect,
            )
        case "batch":
            process_batch(
                args.ha_range,
                args.dec_range,
                args.az_range,
                aperture,
                dome_info,
                args.output,
                visualise=False,
            )
        case _:
            raise ValueError("unknown mocca command")
