# Aperture Obstruction Calculator (MOCCA)

## About

MOCCA (which stands for **M**ick's aperture **O**bstruction **C**al**C**ul**A**tor) allows you to compute the percentage obstruction of the aperture of a telescope aperture, on an equatorial mount, by a hemispherical dome using basic ray tracing techniques. Particularly designed for the [Gratama telescope](https://www.rug.nl/research/kapteyn/sterrenwacht/gratama?lang=en) and dome of the [Blaauw Observatory](https://www.rug.nl/research/kapteyn/sterrenwacht/). However, by changing the properties in `config.ini` it could be adapted to any telescope on an equatorial mount.

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
