import logging
import secrets

import aiohttp


class ShortenerService:
    def __init__(self, api_key: str, base_url: str = "https://adsfly.in/api", alias: str = ""):
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "https://adsfly.in/api").strip()
        self.alias = (alias or "").strip()

    async def shorten_link(self, url: str) -> str:
        if not self.api_key:
            logging.warning("SHORTENER_API_KEY is empty; returning direct bot link")
            return url

        params = {"api": self.api_key, "url": url}
        if self.alias:
            # Static aliases can be used only once by most services, so make each one unique.
            params["alias"] = f"{self.alias}-{secrets.token_hex(3)}"

        timeout = aiohttp.ClientTimeout(total=25)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.base_url, params=params) as response:
                    raw = (await response.text()).strip()
                    if response.status != 200:
                        logging.warning("Shortener HTTP %s: %s", response.status, raw)
                        return url

                    # Some shortener APIs return the URL as plain text.
                    if raw.startswith("http://") or raw.startswith("https://"):
                        return raw

                    try:
                        data = json_loads_safe(raw)
                    except ValueError:
                        logging.warning("Shortener unrecognized response: %s", raw)
                        return url

                    result = find_url(data)
                    if result:
                        return result
                    logging.warning("Shortener response did not contain a URL: %s", data)
                    return url
        except Exception as exc:
            logging.exception("Shortener error: %s", exc)
            return url


def json_loads_safe(raw):
    import json
    return json.loads(raw)


def find_url(data):
    if isinstance(data, str):
        return data if data.startswith(("http://", "https://")) else None
    if isinstance(data, dict):
        for key in ("shortenedUrl", "shorturl", "short_url", "short", "short_link", "url"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
        for key in ("result", "data"):
            value = find_url(data.get(key))
            if value:
                return value
    if isinstance(data, list):
        for item in data:
            value = find_url(item)
            if value:
                return value
    return None
