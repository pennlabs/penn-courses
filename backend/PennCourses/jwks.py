import threading
import time
import logging
from django.core.cache import cache
from django.conf import settings
import requests

JWKS_URI = settings.JWKS_URI
CACHE_TIMEOUT = 3600  # Cache timeout in seconds (1 hour)
REFRESH_INTERVAL = 1800  # Refresh interval in seconds (30 minutes)

logger = logging.getLogger(__name__)

def fetch_and_cache_jwks():
    try:
        response = requests.get(JWKS_URI)
        response.raise_for_status()
        jwks = response.json()
        cache.set("jwks_data", jwks, timeout=CACHE_TIMEOUT)
        logger.info("[JWK] JWKs updated and cached.")
        return jwks
    except Exception as e:
        logger.error(f"[JWK] Failed to fetch JWKs: {e}")

def start_jwks_refresh():
    def refresh():
        while True:
            fetch_and_cache_jwks()
            time.sleep(REFRESH_INTERVAL)

    thread = threading.Thread(target=refresh, daemon=True)
    thread.start()