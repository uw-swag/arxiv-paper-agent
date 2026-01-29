"""Shared fixtures for tests."""

import pytest
import aiohttp


@pytest.fixture
async def aiohttp_session():
    """Create an aiohttp session for tests."""
    session = aiohttp.ClientSession()
    yield session
    await session.close()
