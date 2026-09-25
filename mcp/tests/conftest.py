import json
from pathlib import Path

import pytest


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    with open(FIXTURES / name) as f:
        return json.load(f)


@pytest.fixture
def options_fixture():
    return load_fixture("options.json")


@pytest.fixture
def search_fixture():
    return load_fixture("search_cis1200.json")


@pytest.fixture
def course_fixture():
    return load_fixture("course_cis1200.json")


@pytest.fixture
def math_fixture():
    return load_fixture("course_math1400.json")
