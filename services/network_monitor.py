"""Network monitoring utility to detect and log all HTTP/HTTPS requests."""
import logging
import urllib.request
import urllib.error
from typing import Any
import ssl

logger = logging.getLogger(__name__)

# Store original functions
_original_urlopen = urllib.request.urlopen
_original_Request = urllib.request.Request

def monitored_urlopen(url_or_request, data=None, timeout=None, *args, **kwargs):
    """Monitored version of urllib.request.urlopen that logs all requests."""
    if isinstance(url_or_request, str):
        url = url_or_request
    else:
        url = url_or_request.full_url

    logger.error("=" * 80)
    logger.error(f"⚠️  NETWORK REQUEST DETECTED!")
    logger.error(f"URL: {url}")
    logger.error(f"Data: {data}")
    logger.error(f"Timeout: {timeout}")
    logger.error("=" * 80)

    # Log stack trace to see who made the call
    import traceback
    logger.error("Call stack:")
    for line in traceback.format_stack()[:-1]:
        logger.error(line.strip())
    logger.error("=" * 80)

    # Still call the original to see what happens
    try:
        return _original_urlopen(url_or_request, data, timeout, *args, **kwargs)
    except Exception as e:
        logger.error(f"Network request failed: {type(e).__name__}: {e}")
        raise

def install_network_monitor():
    """Install the network monitor to intercept all urllib requests."""
    logger.info("=" * 80)
    logger.info("INSTALLING NETWORK MONITOR")
    logger.info("All HTTP/HTTPS requests will be logged")
    logger.info("=" * 80)

    # Replace urllib.request.urlopen
    urllib.request.urlopen = monitored_urlopen

    # Try to patch requests library if available
    try:
        import requests
        original_request = requests.request

        def monitored_request(method, url, **kwargs):
            logger.error("=" * 80)
            logger.error(f"⚠️  REQUESTS LIBRARY CALL DETECTED!")
            logger.error(f"Method: {method}")
            logger.error(f"URL: {url}")
            logger.error(f"Kwargs: {kwargs}")
            logger.error("=" * 80)

            import traceback
            logger.error("Call stack:")
            for line in traceback.format_stack()[:-1]:
                logger.error(line.strip())
            logger.error("=" * 80)

            return original_request(method, url, **kwargs)

        requests.request = monitored_request
        logger.info("✅ requests library patched for monitoring")
    except ImportError:
        logger.info("requests library not available, skipping")

    # Try to patch httpx if available
    try:
        import httpx
        logger.info("httpx library detected (used by huggingface_hub)")
        original_httpx_request = httpx.request

        def monitored_httpx_request(method, url, **kwargs):
            logger.error("=" * 80)
            logger.error(f"⚠️  HTTPX LIBRARY CALL DETECTED!")
            logger.error(f"Method: {method}")
            logger.error(f"URL: {url}")
            logger.error(f"Kwargs: {kwargs}")
            logger.error("=" * 80)

            import traceback
            logger.error("Call stack:")
            for line in traceback.format_stack()[:-1]:
                logger.error(line.strip())
            logger.error("=" * 80)

            return original_httpx_request(method, url, **kwargs)

        httpx.request = monitored_httpx_request
        logger.info("✅ httpx library patched for monitoring")
    except ImportError:
        logger.info("httpx library not available, skipping")

    logger.info("Network monitor installation complete")
