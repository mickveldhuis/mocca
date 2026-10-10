import argparse
import logging
from pathlib import Path

from mocca.aperture import create_aperture
from mocca.obstruction import calculate_obstruction
from mocca.types import DomeInfo, TelescopeInfo
from mocca.visualise import plot_aperture_obstruction

logger = logging.getLogger("MOCCA")


MOCCA_CONFIG = "mocca.toml"


def load_or_create_config(config_filename: str | None) -> Path:
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

    if not user_config.exists():
        logger.warning(
            "%s not found in the current working directory; creating one at: %s",
            MOCCA_CONFIG,
            user_config,
        )

        default_config = Path(__file__).parent / MOCCA_CONFIG
        default_config.copy(user_config)

        # Check again whether the copying is succesful
        if not user_config.exists():
            raise OSError(f"could not copy {default_config} to {user_config}")

    return user_config


def parse_cli_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Compute the fractional obstruction of a telescope by a hemispherical dome. The telescope should be affixed to an equatorial mount.",
    )

    def azimuth(value):
        az = float(value)
        if az < 0.0 or az >= 360:
            raise argparse.ArgumentTypeError(
                "invalid azimuth: expecting a value on the following interval [0, 360) deg"
            )

        return az

    def hour_angle(value):
        ha = float(value)
        if ha < 0.0 or ha >= 24:
            raise argparse.ArgumentTypeError(
                "invalid hour angle: expecting a value on the following interval [0, 24) h"
            )

        return ha

    def declination(value):
        dec = float(value)
        if dec < -90 or dec > 90:
            raise argparse.ArgumentTypeError(
                "invalid declination: expecting a value on the following interval [-90, 90] deg"
            )

        return dec

    def positive_integer(value):
        val = int(value)
        if val < 0:
            raise argparse.ArgumentTypeError(
                "invalid value: expecting a positive integer"
            )

        return val

    parser.add_argument(
        "--az", type=azimuth, default=0.0, help="dome azimuth: 0 to 360 deg"
    )
    parser.add_argument(
        "--ha", type=hour_angle, default=0.0, help="telescope hour angle: 0 to 24 h"
    )
    parser.add_argument(
        "--dec",
        type=declination,
        default=0.0,
        help="telescope declination -90 to 90 deg",
    )
    parser.add_argument(
        "-a",
        "--aperture",
        type=str,
        choices=["telescope", "guider", "finder"],
        default="telescope",
        help="telescope aperture for which to calculate the obstruction",
    )
    parser.add_argument(
        "-r",
        "--rate",
        type=positive_integer,
        default=4,
        help="number of radial circles of rays",
    )
    parser.add_argument(
        "-v",
        "--visualise",
        action="store_true",
        help="visualise the blocked rays inside of the circular aperture",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="configuration file with the telescope and dome configuration",
    )

    return parser.parse_args()


def main():
    # Configure the logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
    )

    # Parse CLI arguments
    args = parse_cli_arguments()

    # Load the telescope-dome configuration from the provided TOML file
    config_path = load_or_create_config(args.config)

    logger.info("loading telescope and dome parameters from %s", config_path.resolve())
    telescope_info = TelescopeInfo.from_file(config_path)
    dome_info = DomeInfo.from_file(config_path)

    # Compute and (optionally) visualise the obstruction
    aperture = create_aperture(args.aperture, args.rate, telescope_info)

    ha_deg = args.ha * 15
    blockage, blocked_rays = calculate_obstruction(
        args.az, ha_deg, args.dec, aperture, dome_info
    )

    if blockage is not None:
        logger.info("%s aperture obstruction = %.3f", args.aperture, blockage)
    else:
        raise RuntimeError("The fractional obstruction could not be computed")

    if args.visualise:
        plot_aperture_obstruction(aperture, blocked_rays, args.az)
