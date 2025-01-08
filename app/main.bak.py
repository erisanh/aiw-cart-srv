"""
REF: https://redis.io/learn/develop/python/fastapi

This module provides a FastAPI application integrated with Redis.
It performs operations such as adding Bitcoin sentiment and price data
to Redis TimeSeries, calculating hourly averages, and caching results.

Author:
    dev09@allyai.ai
"""

import functools
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Tuple, Union

import aioredis
import httpx
from aioredis.exceptions import ResponseError
from fastapi import BackgroundTasks, Depends, FastAPI
from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Global Constants
# ---------------------------------------------------------------------------

DEFAULT_KEY_PREFIX = "is-bitcoin-lit"  # Prefix for Redis keys to keep them organized
SENTIMENT_API_URL = "https://api.senticrypt.com/v1/bitcoin.json"  # External API for BTC sentiment data
TWO_MINUTES = 60 + 60  # Cache expiry time in seconds
HOURLY_BUCKET = "3600000"  # Milliseconds in one hour, used for Redis TimeSeries aggregation

# A type alias for BTC sentiment data, which is a list of dictionaries.
BitcoinSentiments = List[Dict[str, Union[str, float]]]

# ---------------------------------------------------------------------------
# Configuration and App Initialization
# ---------------------------------------------------------------------------

class Config(BaseSettings):
    """
    Configuration for connecting to Redis.

    Attributes:
        redis_url (str): The URL for the Redis instance.
            Defaults to 'redis://redis:6379', expecting Docker-based setup.
    
    Example:
        >>> config = Config()
        >>> config.redis_url
        'redis://redis:6379'
    """
    redis_url: str = "redis://redis:6379"

# Set up the logger
log = logging.getLogger(__name__)

# Instantiate the configuration and FastAPI app
config = Config()
app = FastAPI(title="FastAPI Redis Tutorial")

# Create a Redis client with decode_responses=True to get strings instead of bytes
redis = aioredis.from_url(config.redis_url, decode_responses=True)

# ---------------------------------------------------------------------------
# Decorator for Prefixed Keys
# ---------------------------------------------------------------------------

def prefixed_key(f):
    """
    A decorator that prefixes the return value of a function with `self.prefix`.

    This is used in the `Keys` class to maintain a consistent prefix for
    Redis keys, ensuring all keys can be easily organized or filtered.

    Args:
        f (function): The function to decorate; must be a method of `Keys`.

    Returns:
        function: A new function that returns `self.prefix + ":" + original_return`.

    Example:
        >>> class Dummy:
        ...     prefix = 'test'
        ...     @prefixed_key
        ...     def some_key(self):
        ...         return 'my-key'
        ...
        >>> d = Dummy()
        >>> d.some_key()
        'test:my-key'
    
    Author:
        dev09@allyai.ai
    """
    def prefixed_method(*args, **kwargs):
        # For debugging, show the function arguments
        print("args:", args)
        print("kwargs:", kwargs)

        # `self` is the first argument in instance methods
        self = args[0]

        # Call the original function to obtain the unprefixed key
        key = f(*args, **kwargs)

        # Return the key prefixed with `self.prefix`
        return f"{self.prefix}:{key}"

    return prefixed_method

# ---------------------------------------------------------------------------
# Keys Class
# ---------------------------------------------------------------------------

class Keys:
    """
    A utility class to generate well-structured Redis keys.

    This class ensures that we keep consistent naming for different
    data we store in Redis, like time series for sentiment, price, or cache.

    Attributes:
        prefix (str): The common prefix attached to any key generated.

    Example:
        >>> keys = Keys(prefix='myapp')
        >>> keys.timeseries_sentiment_key()
        'myapp:sentiment:mean:30s'
    
    Author:
        dev09@allyai.ai
    """

    def __init__(self, prefix: str = DEFAULT_KEY_PREFIX):
        """
        Initialize a Keys object with a prefix.

        Args:
            prefix (str): The prefix for all Redis keys.
                          Defaults to DEFAULT_KEY_PREFIX.
        """
        self.prefix = prefix

    @prefixed_key
    def timeseries_sentiment_key(self) -> str:
        """
        The Redis key for storing 30-second snapshots of BTC sentiment data.

        Returns:
            str: The final Redis key, e.g. 'is-bitcoin-lit:sentiment:mean:30s'

        Example:
            >>> keys = Keys()
            >>> keys.timeseries_sentiment_key()
            'is-bitcoin-lit:sentiment:mean:30s'
        """
        return "sentiment:mean:30s"

    @prefixed_key
    def timeseries_price_key(self) -> str:
        """
        The Redis key for storing 30-second snapshots of BTC price data.

        Returns:
            str: The final Redis key, e.g. 'is-bitcoin-lit:price:mean:30s'
        
        Example:
            >>> keys = Keys()
            >>> keys.timeseries_price_key()
            'is-bitcoin-lit:price:mean:30s'
        """
        return "price:mean:30s"

    @prefixed_key
    def cache_key(self) -> str:
        """
        The Redis key used for caching short-term calculations.

        Returns:
            str: The final Redis key, e.g. 'is-bitcoin-lit:cache'
        
        Example:
            >>> keys = Keys()
            >>> keys.cache_key()
            'is-bitcoin-lit:cache'
        """
        return "cache"

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

async def add_many_to_timeseries(
    key_pairs: Iterable[Tuple[str, str]], data: BitcoinSentiments
):
    """
    Add multiple data points to one or more Redis TimeSeries keys in batch.

    This function prepares a partial command for `TS.MADD` (Redis command to
    add multiple data points across one or more TimeSeries keys) and accumulates
    each data point before finally sending it to Redis.

    Args:
        key_pairs (Iterable[Tuple[str, str]]): An iterable of tuples like (redis_key, dict_key).
            - The first item is the Redis TimeSeries key to insert into.
            - The second item is the key in each data dictionary that holds the numeric value.
        data (BitcoinSentiments): A list of dictionaries, each containing 'timestamp'
            and keys like 'btc_price' or 'mean'.

    Returns:
        list or int: The result from Redis `TS.MADD` command. Usually, it returns the
                     number of successful insertions.

    Example:
        >>> key_pairs = [
        ...     ('is-bitcoin-lit:price:mean:30s', 'btc_price'),
        ...     ('is-bitcoin-lit:sentiment:mean:30s', 'mean')
        ... ]
        >>> data = [
        ...     {'timestamp': '1690000000', 'btc_price': 30000, 'mean': 0.5}
        ... ]
        >>> await add_many_to_timeseries(key_pairs, data)
        [1, 1]
    
    Author:
        dev09@allyai.ai
    """
    # We will progressively build the TS.MADD command as a partial function
    partial_command = functools.partial(redis.execute_command, "TS.MADD")

    # Iterate over each data point
    for datapoint in data:
        # For each (redis_key, dict_key) pair, we add one more piece to the partial command
        for timeseries_key, sample_key in key_pairs:
            # Convert 'timestamp' in data to an integer in milliseconds
            timestamp_ms = int(float(datapoint["timestamp"]) * 1000)
            # Grab the value from the data dictionary
            value = datapoint[sample_key]

            # Extend the partial command with these details
            partial_command = functools.partial(
                partial_command,
                timeseries_key,
                timestamp_ms,
                value,
            )

    # Execute the built-up TS.MADD command in one shot
    return await partial_command()

def make_keys():
    """
    Creates a Keys instance to generate prefixed Redis keys.

    Returns:
        Keys: An instance with the default prefix (is-bitcoin-lit).

    Example:
        >>> keys = make_keys()
        >>> keys.prefix
        'is-bitcoin-lit'
    
    Author:
        dev09@allyai.ai
    """
    return Keys()

async def persist(keys: Keys, data: BitcoinSentiments):
    """
    Persist both BTC sentiment and price data into Redis TimeSeries.

    Args:
        keys (Keys): An instance for generating the correct Redis keys.
        data (BitcoinSentiments): List of dicts with 'timestamp', 'btc_price', 'mean', etc.

    Returns:
        None

    Example:
        >>> keys = Keys()
        >>> data = [{'timestamp': '1690000000', 'btc_price': 31000, 'mean': 0.55}]
        >>> await persist(keys, data)
    
    Author:
        dev09@allyai.ai
    """
    # Acquire the sentiment and price keys
    ts_sentiment_key = keys.timeseries_sentiment_key()
    ts_price_key = keys.timeseries_price_key()

    # Create a list of (redis_key, dict_key) for TS.MADD
    key_pairs = ((ts_price_key, "btc_price"), (ts_sentiment_key, "mean"))

    # Insert all data points into Redis
    await add_many_to_timeseries(key_pairs, data)

async def get_latest_timestamp(ts_key: str):
    """
    Retrieve the latest data point from a Redis TimeSeries.

    Args:
        ts_key (str): The Redis TimeSeries key.

    Returns:
        list: A list containing [timestamp, value]. If key doesn't exist, may return None.

    Example:
        >>> await get_latest_timestamp("is-bitcoin-lit:sentiment:mean:30s")
        [1690000000000, 0.55]
    
    Author:
        dev09@allyai.ai
    """
    # TS.GET <ts_key> -> [timestamp, value] or None
    response = await redis.execute_command("TS.GET", ts_key)
    return response

async def get_hourly_average(ts_key: str, top_of_the_hour: int):
    """
    Fetch and average data points in a Redis TimeSeries by hourly buckets.

    Args:
        ts_key (str): Redis TimeSeries key to query.
        top_of_the_hour (int): Starting timestamp (in ms) for the range.

    Returns:
        list: Each element is [timestamp, average_value].

    Example:
        >>> await get_hourly_average("is-bitcoin-lit:price:mean:30s", 1690000000000)
        [
            [1690000000000, 31000.0],
            [1690003600000, 31200.0]
        ]
    
    Author:
        dev09@allyai.ai
    """
    # TS.RANGE to get data from top_of_the_hour to now, aggregated by avg
    result = await redis.execute_command(
        "TS.RANGE",
        ts_key,
        top_of_the_hour,
        "+",
        "AGGREGATION",
        "avg",
        HOURLY_BUCKET
    )
    return result

def datetime_parser(dct):
    """
    Convert string fields that end with '+00:00' into datetime objects.

    Args:
        dct (dict): A dictionary potentially containing datetime strings.

    Returns:
        dict: The same dictionary, but with converted datetime fields.

    Example:
        >>> dct = {'time': '2023-07-21T12:00:00+00:00'}
        >>> datetime_parser(dct)
        {'time': datetime.datetime(2023, 7, 21, 12, 0, tzinfo=datetime.timezone.utc)}
    
    Author:
        dev09@allyai.ai
    """
    for k, v in dct.items():
        if isinstance(v, str) and v.endswith("+00:00"):
            try:
                # Convert string to datetime if it ends with +00:00
                dct[k] = datetime.fromisoformat(v)
            except:
                pass
    return dct

async def get_cache(keys: Keys):
    """
    Retrieve cached data from Redis using the `cache_key`.

    Args:
        keys (Keys): Provides the cache key.

    Returns:
        dict or None: The cached data if exists, else None.

    Example:
        >>> keys = Keys()
        >>> cache_data = await get_cache(keys)
        >>> if cache_data:
        ...     print("Cache found:", cache_data)
    
    Author:
        dev09@allyai.ai
    """
    # Get the cache key from Keys
    current_hour_cache_key = keys.cache_key()

    # Attempt to retrieve data from Redis
    current_hour_stats = await redis.get(current_hour_cache_key)

    # If data exists, parse it as JSON. If not, return None
    if current_hour_stats:
        return json.loads(current_hour_stats, object_hook=datetime_parser)

async def set_cache(data, keys: Keys):
    """
    Store data in Redis cache with a 2-minute expiry.

    Args:
        data (dict): The data to cache.
        keys (Keys): Provides the cache key.

    Returns:
        None

    Example:
        >>> data = {'sentiment_direction': 'rising'}
        >>> keys = Keys()
        >>> await set_cache(data, keys)
    
    Author:
        dev09@allyai.ai
    """
    def serialize_dates(v):
        """
        Helper to convert datetime objects to ISO-formatted strings.

        Args:
            v (any): The value to serialize.

        Returns:
            str or any: If v is datetime, returns isoformat, else v unchanged.
        """
        return v.isoformat() if isinstance(v, datetime) else v

    # Convert data (potentially with datetime) to JSON
    serialized_data = json.dumps(data, default=serialize_dates)

    # Set the data in Redis with a 2-minute expiry
    await redis.set(keys.cache_key(), serialized_data, ex=TWO_MINUTES)

def get_direction(last_three_hours, key: str):
    """
    Determine if a metric is 'rising', 'falling', or 'flat'
    based on the first vs. last entries in `last_three_hours`.

    Args:
        last_three_hours (list): Each item is a dict with {key: value} for sentiment or price.
        key (str): The metric key to evaluate, e.g. 'sentiment' or 'price'.

    Returns:
        str: 'rising' | 'falling' | 'flat'

    Example:
        >>> sample_data = [
        ...     {'sentiment': 0.75}, 
        ...     {'sentiment': 0.80}
        ... ]
        >>> get_direction(sample_data, 'sentiment')
        'rising'
    
    Author:
        dev09@allyai.ai
    """
    first_val = last_three_hours[0][key]
    last_val = last_three_hours[-1][key]

    if first_val < last_val:
        return "rising"
    elif first_val > last_val:
        return "falling"
    else:
        return "flat"

def now():
    """
    Return the current UTC datetime for mocking in tests.

    Returns:
        datetime: Current UTC datetime.

    Example:
        >>> current_time = now()
        >>> current_time.isoformat()
        '2023-07-21T12:34:56.789012'
    
    Author:
        dev09@allyai.ai
    """
    return datetime.utcnow()

async def calculate_three_hours_of_data(keys: Keys) -> Dict[str, Union[List[Dict], str]]:
    """
    Calculate data for the last three hours: hourly averages, sentiment direction, and price direction.

    Args:
        keys (Keys): Object providing TimeSeries keys.

    Returns:
        dict: 
            {
                "hourly_average_of_averages": [...],
                "sentiment_direction": ...,
                "price_direction": ...
            }

    Example:
        >>> keys = Keys()
        >>> result = await calculate_three_hours_of_data(keys)
        >>> result['sentiment_direction']
        'rising'
    
    Author:
        dev09@allyai.ai
    """
    sentiment_key = keys.timeseries_sentiment_key()
    price_key = keys.timeseries_price_key()

    # Get the latest data from sentiment key -> [timestamp, value]
    latest_data = await get_latest_timestamp(sentiment_key)

    # If no data is found, handle gracefully, e.g., return empty info
    if not latest_data:
        return {
            "hourly_average_of_averages": [],
            "sentiment_direction": "flat",
            "price_direction": "flat",
        }

    # Calculate a 3-hour-ago timestamp in milliseconds
    # (optionally, you can switch to 2 hours or a different timeframe)
    three_hours_ago_ms = latest_data[0] - (1000 * 60 * 60 * 2)
    print(three_hours_ago_ms)  # Debugging

    # Query hourly averages from both time series
    sentiment = await get_hourly_average(sentiment_key, three_hours_ago_ms)
    price = await get_hourly_average(price_key, three_hours_ago_ms)

    # Combine the price/sentiment data into a single list
    last_three_hours = []
    for price_data, sentiment_data in zip(price, sentiment):
        price_timestamp, price_val = price_data
        sentiment_timestamp, sentiment_val = sentiment_data

        last_three_hours.append({
            "price": price_val,
            "sentiment": sentiment_val,
            "time": datetime.fromtimestamp(price_timestamp / 1000, tz=timezone.utc)
        })

    # Determine directions
    sentiment_dir = get_direction(last_three_hours, "sentiment")
    price_dir = get_direction(last_three_hours, "price")

    return {
        "hourly_average_of_averages": last_three_hours,
        "sentiment_direction": sentiment_dir,
        "price_direction": price_dir,
    }

# ---------------------------------------------------------------------------
# FastAPI Endpoints
# ---------------------------------------------------------------------------

@app.post("/refresh")
async def refresh(background_tasks: BackgroundTasks, keys: Keys = Depends(make_keys)):
    """
    Fetch the latest BTC sentiment data and update Redis TimeSeries.

    This endpoint:
      1. Retrieves data from an external API.
      2. Persists it to Redis (both price and sentiment).
      3. Calculates the last three hours of data.
      4. Caches it asynchronously.

    Args:
        background_tasks (BackgroundTasks): Helper to run tasks in the background.
        keys (Keys): Provides Redis keys, including time series and cache.

    Returns:
        dict: {"message": "Refresh initiated successfully."}

    Example:
        >>> # POST request to /refresh
        >>> # Response: {"message": "Refresh initiated successfully."}
    
    Author:
        dev09@allyai.ai
    """
    async with httpx.AsyncClient() as client:
        # Fetch data from external API
        response = await client.get(SENTIMENT_API_URL)
        data_json = response.json()

    # Persist the data to Redis
    await persist(keys, data_json)

    # Calculate fresh data from the last 3 hours
    data = await calculate_three_hours_of_data(keys)

    # Store it in the cache asynchronously
    background_tasks.add_task(set_cache, data, keys)

    return {"message": "Refresh initiated successfully."}

@app.get("/is-bitcoin-lit")
async def bitcoin(background_tasks: BackgroundTasks, keys: Keys = Depends(make_keys)):
    """
    Retrieve the latest BTC sentiment and price data.

    1. Check Redis cache for any stored data.
    2. If none, calculate fresh data and cache it.

    Args:
        background_tasks (BackgroundTasks): For asynchronous caching task.
        keys (Keys): Provides Redis key references.

    Returns:
        dict: Contains "hourly_average_of_averages", "sentiment_direction", and "price_direction".

    Example:
        >>> # GET request to /is-bitcoin-lit
        >>> # Response might look like:
        >>> {
        ...   "hourly_average_of_averages": [...],
        ...   "sentiment_direction": "rising",
        ...   "price_direction": "falling"
        ... }
    
    Author:
        dev09@allyai.ai
    """
    # Try retrieving cache
    data = await get_cache(keys)

    # If cache is empty, compute new data
    if not data:
        data = await calculate_three_hours_of_data(keys)
        background_tasks.add_task(set_cache, data, keys)

    return data

# ---------------------------------------------------------------------------
# Redis Initialization for TimeSeries
# ---------------------------------------------------------------------------

async def make_timeseries(key: str):
    """
    Create a Redis TimeSeries with a 'first' duplicate policy.

    'first' policy means if you insert a data point with the same timestamp,
    it ignores the new value. This avoids duplicates at the same timestamp.

    Args:
        key (str): The Redis TimeSeries key to create.

    Returns:
        None

    Example:
        >>> await make_timeseries("is-bitcoin-lit:price:mean:30s")
    
    Author:
        dev09@allyai.ai
    """
    try:
        # TS.CREATE <key> DUPLICATE_POLICY first
        await redis.execute_command(
            "TS.CREATE",
            key,
            "DUPLICATE_POLICY",
            "first",
        )
    except ResponseError as e:
        # If it already exists, log and move on
        log.info("Could not create timeseries %s, error: %s", key, e)

async def initialize_redis(keys: Keys):
    """
    Create needed TimeSeries in Redis for sentiment and price data.

    If they already exist, log the info and move forward.

    Args:
        keys (Keys): Provides the correct time series keys.

    Returns:
        None

    Example:
        >>> k = Keys()
        >>> await initialize_redis(k)
    
    Author:
        dev09@allyai.ai
    """
    # Make sentiment time series
    await make_timeseries(keys.timeseries_sentiment_key())
    # Make price time series
    await make_timeseries(keys.timeseries_price_key())

# ---------------------------------------------------------------------------
# FastAPI Startup Event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """
    On startup, create or ensure existence of needed Redis TimeSeries keys.

    FastAPI calls this event automatically at app startup, ensuring our Redis
    environment is ready before handling any requests.

    Example:
        >>> # No direct calls. It's handled by FastAPI on startup.
    
    Author:
        dev09@allyai.ai
    """
    # Create a Keys instance
    keys = Keys()
    # Ensure the TimeSeries keys exist
    await initialize_redis(keys)
