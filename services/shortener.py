import aiohttp
import logging
from urllib.parse import quote


class ShortenerService:

    def __init__(self, api_key: str, base_url: str = "https://adsfly.in/api"):
        self.api_key = api_key
        self.base_url = base_url

    async def shorten_link(self, url: str) -> str:
        if not self.api_key:
            return url

        try:
            api_url = (
                f"{self.base_url}"
                f"?api={self.api_key}"
                f"&url={quote(url, safe='')}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=20) as response:
                    text = await response.text()

                    try:
                        data = await response.json()
                    except Exception:
                        logging.warning("Shortener raw response: %s", text)
                        return url

                    for key in ["shortenedUrl", "shorturl", "short_url", "short", "url"]:
                        if data.get(key):
                            return data[key]

                    if data.get("status") == "success" and data.get("result"):
                        return data["result"]

                    logging.warning("Shortener response: %s", data)
                    return url

        except Exception as e:
            logging.warning("Shortener error: %s", e)
            return url