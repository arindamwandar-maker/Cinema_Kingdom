import logging
from urllib.parse import quote

import aiohttp


class ShortenerService:
    def __init__(self, api_key: str, base_url: str = "https://shrinkearn.com/api"):
        self.api_key = api_key
        self.base_url = base_url

    async def shorten_link(self, url: str) -> str:
        if not self.api_key:
            return url
        api_url = f"{self.base_url}?api={self.api_key}&url={quote(url, safe='')}"
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        logging.warning("Shortener HTTP status: %s", response.status)
                        return url
                    try:
                        data = await response.json()
                    except Exception:
                        logging.warning("Shortener non-json response: %s", await response.text())
                        return url
                    for key in ("shortenedUrl", "shorturl", "short_url", "url", "short"):
                        if data.get(key):
                            return data[key]
                    logging.warning("Unknown shortener response: %s", data)
                    return url
        except Exception as exc:
            logging.exception("Shortener error: %s", exc)
            return url
