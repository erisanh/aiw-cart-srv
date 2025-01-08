"""
This module contains Pytest fixtures and configuration for testing the FastAPI application
with an asynchronous Redis client. It sets up an event loop, provides testing keys, and
initializes the required TimeSeries in Redis for each test.

Author:
    dev09@allyai.ai
"""

import asyncio
from typing import Generator

import aioredis
import pytest
# Import the required components from the main application
from app.main import Keys, app, config, initialize_redis, make_keys
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

# A test-specific prefix for Redis keys to avoid clashing with production data
TEST_PREFIX = "test:is-bitcoin-lit"

@pytest.fixture(scope="module")
def redis() -> Generator:
    """
    Provide a Redis client for the test module.

    This fixture yields an aioredis client configured with the URL from `config.redis_url`.
    It uses `decode_responses=True` so that returned data are strings instead of bytes.

    Args:
        None

    Returns:
        Generator: A generator that yields an aioredis client instance, then cleans up.
    
    Example:
        >>> async def test_something(redis):
        ...     value = await redis.set("testkey", "testvalue")
        ...     assert value == "OK"
    """
    # Create a Redis client using the global config
    yield aioredis.from_url(config.redis_url, decode_responses=True)
    # After yielding, Pytest automatically handles the teardown.

@pytest.fixture(scope="session")
def event_loop(request):
    """
    Create an instance of the default event loop for all test cases in this session.

    This fixture sets up a custom event loop for async tests, ensuring that
    asynchronous operations (like Redis commands or FastAPI calls) run under
    the correct loop.

    Args:
        request (FixtureRequest): Provides information about the requesting test context.

    Yields:
        asyncio.AbstractEventLoop: A newly created event loop for the entire test session.

    Example:
        >>> def test_my_async_code(event_loop):
        ...     # run async code using event_loop.run_until_complete(...)
    """
    # Obtain a new event loop
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    # Close the loop after tests finish
    loop.close()

@pytest.fixture
async def keys(redis: aioredis.Redis):
    """
    Provide a test-specific Keys instance to generate Redis keys with a test prefix.

    This fixture overrides the `make_keys` dependency in the FastAPI app so that
    any references to `Keys` within the application code use our test prefix. It
    ensures test data is separated from production or other testing data.

    Args:
        redis (aioredis.Redis): The Redis client fixture.

    Yields:
        Keys: A Keys instance that produces keys prefixed by TEST_PREFIX.

    Post-Yield:
        Cleans up any keys created during the test run, removing them from Redis.

    Example:
        >>> async def test_persist_data(client, keys):
        ...     # 'keys' now has prefix 'test:is-bitcoin-lit'
        ...     ...
    """
    def make_test_keys():
        return Keys(TEST_PREFIX)

    # Override the app's dependency for generating Keys instances
    app.dependency_overrides[make_keys] = make_test_keys

    # Create the test-specific Keys instance
    test_keys = make_test_keys()

    yield test_keys

    # Cleanup any test keys that the test run created
    # Use Redis KEYS command to find all matching keys (TEST_PREFIX*) and delete them
    generated_keys = await redis.keys(f"{TEST_PREFIX}*")
    if generated_keys:
        await redis.delete(*generated_keys)

@pytest.fixture(scope="function")
async def client(keys):
    """
    Provide an AsyncClient for sending requests to the FastAPI application.

    This fixture uses `LifespanManager` to handle FastAPI's lifespan events (startup/shutdown)
    and an `AsyncClient` from `httpx` to simulate HTTP requests. It depends on the `keys`
    fixture to ensure the test prefix is set before the client is used.

    Args:
        keys (Keys): The test-specific Keys instance, ensuring test data is separated.

    Yields:
        AsyncClient: A test client for making HTTP requests to the FastAPI app's `/` routes.

    Example:
        >>> async def test_refresh_endpoint(client):
        ...     response = await client.post("/refresh")
        ...     assert response.status_code == 200
    """
    # Create an AsyncClient with the FastAPI app, using base_url for local testing
    async with AsyncClient(app=app, base_url="http://test") as test_client, LifespanManager(app):
        yield test_client
    # Test teardown automatically handles closure of the client and the lifespan context.

@pytest.fixture(scope="function", autouse=True)
@pytest.mark.asyncio
async def setup_redis(request, keys):
    """
    Ensure Redis TimeSeries structures are initialized before each test function.

    This fixture automatically runs for every test function (due to `autouse=True`) and
    initializes the required TimeSeries (sentiment, price) by calling `initialize_redis`.
    This means each test has guaranteed structures before it runs, reducing flakiness.

    Args:
        request (FixtureRequest): Metadata about the current test being run.
        keys (Keys): The test-specific Keys instance for generating prefixed TimeSeries keys.

    Returns:
        None

    Example:
        >>> async def test_time_series_data(client):
        ...     # The TimeSeries keys have already been created
        ...     response = await client.get("/is-bitcoin-lit")
        ...     assert response.status_code == 200
    """
    # Call initialize_redis to create the sentiment and price TimeSeries
    await initialize_redis(keys)
