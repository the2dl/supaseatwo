import logging
import time
import httpx
from json.decoder import JSONDecodeError
from postgrest.exceptions import APIError

def with_retries(func, initial_backoff=1.0, max_backoff=120.0, fixed_backoff=30.0):
    total_wait_time = 0
    retries = 0
    while True:
        try:
            return func()
        except (
            httpx.RequestError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
            httpx.RemoteProtocolError,
            httpx.HTTPStatusError,
            JSONDecodeError,
            APIError
        ) as e:
            if total_wait_time < max_backoff:
                wait_time = initial_backoff * (2 ** retries)
                wait_time = min(wait_time, max_backoff - total_wait_time)
            else:
                wait_time = fixed_backoff
            logging.error(f"Error: {e}, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            total_wait_time += wait_time
            retries += 1
        except Exception as e:
            logging.error(f"Unexpected error: {e}, retrying in {fixed_backoff} seconds...")
            time.sleep(fixed_backoff)
