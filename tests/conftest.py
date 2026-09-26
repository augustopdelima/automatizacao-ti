"""Fixtures compartilhadas dos testes."""

import pytest

from fakes import FakeRepository


@pytest.fixture
def repo():
    """Repositório fake em memória com as equipes padrão."""
    return FakeRepository()