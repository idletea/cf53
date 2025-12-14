from pathlib import Path

import pytest


@pytest.fixture
def build_zones_dir(tmp_path):
    tmp_path = Path(tmp_path)

    def inner(files: dict[str | Path, str]) -> Path:
        for relative_path, content in files.items():
            relative_path = tmp_path / Path(relative_path)
            with relative_path.open("w+") as fp:
                fp.write(content)

        return tmp_path

    return inner
