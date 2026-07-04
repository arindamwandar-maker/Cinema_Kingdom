import logging
from urllib.parse import quote

import aiohttp


class ShortenerService:
    def __init__(self, api_key: str, base_url: str = "https://adsfly.in/api", alias: str = ""):
        self.api_key = api_key
        self.base_url = base_url or "https://adsfly.in/api"
        self.alias = alias or ""

    async def shorten_link(self, url: str) -> str:
        if not self.api_key:
            return url

        # AdsFly/ShrinkEarn style API:
        # https://adsfly.in/api?api=API_KEY&url=DESTINATION&alias=CustomAlias
        api_url = f"{self.base_url}?api={quote(self.api_key, safe='')}&url={quote(url, safe='')}"
        if self.alias:
            api_url += f"&alias={quote(self.alias, safe='')}"

        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url) as response:
                    body = await response.text()
                    if response.status != 200:
                        logging.warning("Shortener HTTP status: %s | %s", response.status, body)
                        return url
                    try:
                        data = await response.json(content_type=None)
                    except Exception:
                        text = body.strip()
                        if text.startswith("http"):
                            return text
                        logging.warning("Shortener non-json response: %s", body)
                        return url

                    for key in ("shortenedUrl", "shorturl", "short_url", "shortened_url", "url", "short", "result"):
                        if isinstance(data, dict) and data.get(key):
                            return data[key]
                    if isinstance(data, dict) and data.get("status") in ("success", "ok") and data.get("message", "").startswith("http"):
                        return data["message"]

                    logging.warning("Unknown shortener response: %s", data)
                    return url
        except Exception as exc:
            logging.exception("Shortener error: %s", exc)
            return url
