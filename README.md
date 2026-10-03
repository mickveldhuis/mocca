# Aperture Obstruction Calculator (MOCCA)

## About

MOCCA (which stands for **M**ick's aperture **O**bstruction **C**al**C**ul**A**tor) allows you to compute the percentage obstruction of the aperture of a telescope aperture, on an equatorial mount, by a hemispherical dome using basic ray tracing techniques.

This tool was created as part of undergraduate research and let to an upgrade of the dome control software used by the [Blaauw Observatory](https://www.rug.nl/research/kapteyn/sterrenwacht/), which is mainly used for outreach and as a training facility for students of the Faculty of Science and Engineering at the University of Groningen.

## Usage

This project uses [`uv`](https://github.com/astral-sh/uv), so make sure it's installed before continuing.

Clone the repository, navigate to the project folder, and install the dependencies:

```bash
uv sync
```

This will create a virtual environment in which `mocca` is available as an executable. Alternatively, you can run the tool as follows:

```bash
uv run mocca
```

Add `--help` or `-h` to show the available CLI options.

## Documentation

The methods are described in detail in Chapters 3 and 4 of [*M. Veldhuis (2021), Remodeling Dome Control: Applications for the Blaauw Observatory*](https://fse.studenttheses.ub.rug.nl/id/eprint/25172) and usage of the tool is described in this repository's [documentation](docs/).
