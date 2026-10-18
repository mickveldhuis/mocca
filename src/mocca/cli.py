import argparse

import numpy as np


class RangeAction(argparse.Action):
    """
    Accept 1, 2, or 3 arguments for a range specification.

    1 value:  np.arange(0, end)
    2 values: np.arange(start, stop)
    3 values: np.arange(start, stop, step)

    Optionally accepts a validator to verify whether the range is valid.
    """

    def __init__(self, option_strings, dest, validators=None, **kwargs):
        """Initialise with an optional (exclusive) range validator"""
        super().__init__(option_strings, dest, nargs="+", **kwargs)
        self.validators = validators

    def __call__(self, parser, namespace, values, option_string=None):
        # Extract clean option name for error messages
        n = len(values)

        if n == 0:
            parser.error(f"{option_string} expects at least one value")
        if n > 3:
            parser.error(f"{option_string} expects at most 3 values, got {n}")

        # Convert all arguments to float
        try:
            numeric_values = [float(v) for v in values]
        except ValueError:
            parser.error(
                f"invalid {option_string} values: {values}, expects floating-point values"
            )

        # Apply a validator to each argument if provided
        if self.validators:
            for index, (val, validator) in enumerate(
                zip(numeric_values, self.validators)
            ):
                if validator is not None:
                    try:
                        numeric_values[index] = validator(str(val))
                    except argparse.ArgumentTypeError as e:
                        parser.error(f"invalid {option_string} value {index + 1}: {e}")

        # Build range based on number of arguments
        match n:
            case 1:
                (end,) = numeric_values
                if end <= 0:
                    parser.error(
                        f"invalid {option_string} range: expects a value larger than zero"
                    )
                range_array = np.arange(end)
            case 2:
                start, stop = numeric_values
                if stop <= start:
                    parser.error(
                        f"invalid {option_string} range [{start}, {stop}): "
                        f"stop must exceed start"
                    )
                range_array = np.arange(start, stop)
            case 3:
                start, stop, step = numeric_values
                if step <= 0.0 or stop <= start:
                    parser.error(
                        f"invalid {option_string} range [{start}, {stop}) with step size {step}"
                    )
                range_array = np.arange(start, stop, step)

        setattr(namespace, self.dest, range_array)


def azimuth_type(value):
    az = float(value)
    if az < 0.0 or az > 360.0:
        raise argparse.ArgumentTypeError(
            "invalid azimuth: expecting a value on the following interval [0, 360) deg"
        )

    return az


def hour_angle_type(value):
    ha = float(value)
    if ha < 0.0 or ha >= 24.0:
        raise argparse.ArgumentTypeError(
            "invalid hour angle: expecting a value on the following interval [0, 24) h"
        )

    # Convert to degrees for further processing
    return 15.0 * ha


def declination_type(value):
    dec = float(value)
    if dec < -90.0 or dec > 90.0:
        raise argparse.ArgumentTypeError(
            "invalid declination: expecting a value on the following interval [-90, 90] deg"
        )

    return dec


def positive_integer_type(value):
    val = int(value)
    if val <= 0:
        raise argparse.ArgumentTypeError("invalid value: expecting a positive integer")

    return val


def parse_cli_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Compute the fractional obstruction of a telescope by a hemispherical dome. The telescope should be affixed to an equatorial mount.",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--az",
        metavar="AZIMUTH",
        type=azimuth_type,
        default=0.0,
        help="dome azimuth: 0 to 360 deg",
    )
    group.add_argument(
        "--az-range",
        metavar="N",
        action=RangeAction,
        help="dome azimuth range: END | START:STOP | START:STOP:STEP",
    )
    parser.add_argument(
        "--ha",
        metavar="HOUR ANGLE",
        type=hour_angle_type,
        default=0.0,
        help="telescope hour angle: 0 to 24 h",
    )
    parser.add_argument(
        "--dec",
        metavar="DECLINATION",
        type=declination_type,
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
        type=positive_integer_type,
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
        metavar="PATH",
        help="configuration file with the telescope and dome configuration",
    )

    return parser.parse_args()
