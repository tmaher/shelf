import pytest
from shelf import ShelfFeedGenerator


class TestSFG:
    @pytest.fixture
    def my_sfg(self):
        return ShelfFeedGenerator()

    def test_create(self, my_sfg):
        assert isinstance(my_sfg, ShelfFeedGenerator)
