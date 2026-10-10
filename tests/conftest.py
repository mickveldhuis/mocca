from importlib.util import find_spec
from pathlib import Path

import pytest

from mocca.main import MOCCA_CONFIG
from mocca.types import DomeInfo, TelescopeInfo


@pytest.fixture(scope="module")
def config_path():
    mocca_src = Path(find_spec("mocca").origin).parent
    config_path = mocca_src / MOCCA_CONFIG

    if not config_path.exists():
        pytest.skip(f"MOCCA configuration file not found at {config_path.resolve()}")

    return config_path


@pytest.fixture(scope="module")
def telescope_info(config_path):
    mocca_src = Path(find_spec("mocca").origin).parent
    config_path = mocca_src / MOCCA_CONFIG

    if not config_path.exists():
        pytest.skip(f"MOCCA configuration file not found at {config_path.resolve()}")

    return TelescopeInfo.from_file(config_path)


@pytest.fixture(scope="module")
def dome_info(config_path):
    return DomeInfo.from_file(config_path)
