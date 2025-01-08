"""
This module tests the FastAPI endpoints related to Bitcoin sentiment and price data
using mocked external API responses and Pytest fixtures. It ensures that the /refresh
and /is-bitcoin-lit endpoints behave correctly when external data is fetched.

Author:
    dev09@allyai.ai
"""

import datetime
import json
import os.path
from unittest import mock

import pytest
# Import the FastAPI app from the main module
from app.main import app
from fastapi.testclient import TestClient

# Constants for test endpoints
REFRESH_URL = "/refresh"
URL = "/is-bitcoin-lit"

# A tuple of fields we expect in the JSON response
EXPECTED_FIELDS = (
    "hourly_average_of_averages",
    "sentiment_direction",
    "price_direction",
)

# Path to a JSON fixture file (mocked sentiment API response)
JSON_FIXTURE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "fixtures",
    "sentiment_response.json",
)

@pytest.fixture
def mock_bitcoin_api():
    """
    A fixture that mocks external dependencies: time (now) and HTTP calls for the sentiment API.

    This fixture:
      - Mocks the `now()` function from app.main to consistently return a fixed datetime.
      - Mocks `httpx.AsyncClient.get` to return a fake response from our JSON fixture.
      - Yields the mock so it can be inspected in tests if needed.

    Yields:
        mock_get (Mock): A mock object that stands in for the real `httpx.AsyncClient.get`.
    
    Example:
        >>> def test_something(mock_bitcoin_api):
        ...     # Now, `httpx.AsyncClient.get` calls return the JSON fixture data
        ...     # and `app.main.now()` returns a fixed datetime.
    """
    with mock.patch("app.main.now") as mock_utcnow:
        # Override the now() function to return a fixed datetime
        mock_utcnow.return_value = datetime.datetime(
            2021,
            7,
            7,
            10,
            30,
            0,
            0,  # Hard-coded: 2021-07-07 10:30:00 UTC
        )

        # Mock out httpx.AsyncClient.get
        with mock.patch("httpx.AsyncClient.get") as mock_get:
            # Mock out a Response object to control the JSON returned
            with mock.patch("httpx.Response") as mock_response:
                # Prepare a MagicMock to override the .json() method on our fake response
                m = mock.MagicMock()
                # Load data from the local JSON fixture file
                with open(JSON_FIXTURE) as f:
                    fixture_data = json.loads(f.read())
                    m.return_value = fixture_data

                # Assign the MagicMock's return_value to .json
                mock_response.json = m

                # When `mock_get` is called, it returns our mocked response
                mock_get.return_value = mock_response

                # Yield the mock so tests can inspect or override if needed
                yield mock_get

# Create a synchronous TestClient bound to our FastAPI app
# Note: If using async tests, you might rely on an async fixture instead.
client = TestClient(app)

@pytest.mark.asyncio
async def test_api(mock_bitcoin_api: mock.MagicMock, client):
    """
    Test the Bitcoin sentiment API endpoints with mocked external API data.

    This test checks that:
      1. The /refresh endpoint can be called asynchronously.
      2. The /is-bitcoin-lit endpoint retrieves data, including fields that we expect.
      3. The response contains the fields in EXPECTED_FIELDS.
    
    Args:
        mock_bitcoin_api (mock.MagicMock): Provided by the `mock_bitcoin_api` fixture.
        client (AsyncClient): Provided by the `client` fixture (async version).
    
    Example:
        >>> # Pytest will run this test and use the provided fixtures.
        >>> # No direct calls from your side are needed.
    """
    # Call the /refresh endpoint to fetch and persist data (mocked)
    refresh_response = await client.post(REFRESH_URL)
    # Check that we get a valid response
    assert refresh_response.status_code == 200, "Refresh endpoint did not return 200 OK."

    # Now call the /is-bitcoin-lit endpoint to retrieve the computed data
    result_response = await client.get(URL)
    assert result_response.status_code == 200, "/is-bitcoin-lit endpoint did not return 200 OK."

    # Parse the JSON response
    summary = result_response.json()

    # Ensure each expected field is present
    for field in EXPECTED_FIELDS:
        assert field in summary, f"Missing field: {field} in response"
