import pytest


from semantic_release.settings import Config


@pytest.fixture
def default_config():
    yield Config.from_files()
