import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
from joblib import dump, load
from obstruction.aperture import FinderAperture, GuiderAperture, TelescopeAperture

parser = argparse.ArgumentParser(
    allow_abbrev=True,
    description="Produce a grid of the obstruction % of the telescope/finder/guider by the dome for all possible HAs, Decs, and dome azimuth angles",
)

parser.add_argument(
    "-a",
    "--aperture",
    action="store",
    type=str,
    default="telescope",
    help="select aperture: telescope, finder, guider | default: telescope",
)
parser.add_argument(
    "-r",
    "--rate",
    action="store",
    type=int,
    default=3,
    help="no. rays (for decent results >3; preferably 4-10) | default: 3",
)

args = parser.parse_args()


# sample HA from 0 h to 24 h & Dec from -90 to 90 deg
ha = np.linspace(0, 359, 360)
dec = np.linspace(-90, 90, 181)

# Create a temporary joblib data file for each azimuth
az_range = np.arange(0, 360, 1)

# Select the appropriate aperture
if args.aperture == "guider":
    APERTURE = GuiderAperture(rate=args.rate)
elif args.aperture == "finder":
    APERTURE = FinderAperture(rate=args.rate)
else:
    APERTURE = TelescopeAperture(rate=args.rate)

# Verify whether the appropriate file structure exists/otherwise create required folders
req_path = Path.cwd() / "data" / APERTURE.get_name() / "obstructed"

try:
    req_path.mkdir(parents=True, exist_ok=False)
except FileExistsError:
    pass
else:
    print("Created the data/.../obstructed folder(s)...")


def get_azimuth_path(az):
    fn = f"az_{int(az)}.joblib"

    return req_path / fn


def generate_obstruction_grid(az):
    """Store the % obstruction for a single azimuth.

    Parameters
    ----------
    az: the azimuth in degrees
    """
    p = np.zeros((ha.size, dec.size))  # % obstruction grid

    for i in range(ha.size):
        for j in range(dec.size):
            percentage = APERTURE.obstruction(ha[i], dec[j], az)

            p[i, j] = percentage

    # print('Finished az = {:>3.0f} degrees at {}'.format(az, datetime.now(tz=datetime.UTC).strftime('%H:%M')))

    with get_azimuth_path(az).open(mode="wb") as azimuth_file:
        dump(p, azimuth_file)


def combine():
    """
    Load the obstruction grids (1 per azimuth angle) and stitch
    them together and store them as npy files.
    """
    obstr_cube = []

    for az in az_range:
        with get_azimuth_path(az).open(mode="rb") as azimuth_file:
            data = load(azimuth_file)
            obstr_cube.append(data)

    obstr_cube = np.array(obstr_cube)

    date_signature = datetime.now(tz=datetime.UTC).strftime("%d_%h_%Y")
    fn = f"obstruction_cube_{args.aperture}_{date_signature}.npy"
    file_path = Path.cwd() / "data" / fn

    with file_path.open(mode="wb") as obstr_file:
        np.save(obstr_file, obstr_cube)

    print(f'Obstruction cube is stored in "{file_path}"')


if __name__ == "__main__":
    print(
        "Start [{}] run at {:}".format(
            APERTURE.get_name(), datetime.now(tz=datetime.UTC).strftime("%H:%M")
        )
    )
    # results = Parallel(n_jobs=-1)(delayed(generate_obstruction_grid)(i) for i in az_range)

    for az in az_range:
        print(f"Process azimuth {az:.3f} deg")
        start_time = datetime.now(tz=datetime.UTC)
        generate_obstruction_grid(az)
        duration = (datetime.now(tz=datetime.UTC) - start_time).total_seconds()
        print(f"Finish; duration = {duration:.3f}")

        break

    print(
        "Finished [{}] run at {:}; now stitching together the files...".format(
            APERTURE.get_name(), datetime.now(tz=datetime.UTC).strftime("%H:%M")
        )
    )

    combine()
