import json
import logging
from urllib.parse import quote

import aiohttp


class ShortenerService:

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://adsfly.in/api",
        alias: str = ""
    ):
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "https://adsfly.in/api").strip()
        self.alias = (alias or "").strip()

    async def shorten_link(self, destination_url: str) -> str:

        if not self.api_key:
            logging.error("SHORTENER_API_KEY is missing")
            return destination_url

        params = {
            "api": self.api_key,
            "url": destination_url
        }

        # Static alias ব্যবহার না করাই ভালো
        if self.alias:
            params["alias"] = self.alias

        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    allow_redirects=True
                ) as response:

                    raw_text = (await response.text()).strip()

                    logging.info(
                        "AdsFly status=%s response=%s",
                        response.status,
                        raw_text[:500]
                    )

                    if response.status != 200:
                        logging.error(
                            "AdsFly HTTP error %s: %s",
                            response.status,
                            raw_text
                        )
                        return destination_url

                    # AdsFly plain URL return করলে
                    if raw_text.startswith(("https://", "http://")):
                        return raw_text

                    # JSON response হলে
                    try:
                        data = json.loads(raw_text)
                    except json.JSONDecodeError:
                        logging.error(
                            "AdsFly response is neither URL nor valid JSON: %s",
                            raw_text
                        )
                        return destination_url

                    possible_keys = (
                        "shortenedUrl",
                        "shortened_url",
                        "shorturl",
                        "short_url",
                        "short",
                        "short_link",
                        "url",
                        "result"
                    )

                    for key in possible_keys:
                        value = data.get(key)

                        if isinstance(value, str) and value.startswith(
                            ("https://", "http://")
                        ):
                            return value

                        if isinstance(value, dict):
                            for nested_key in possible_keys:
                                nested_value = value.get(nested_key)

                                if (
                                    isinstance(nested_value, str)
                                    and nested_value.startswith(
                                        ("https://", "http://")
                                    )
                                ):
                                    return nested_value

                    logging.error("Unknown AdsFly response: %s", data)
                    return destination_url

        except aiohttp.ClientError as exc:
            logging.exception("AdsFly network error: %s", exc)
            return destination_url

        except Exception as exc:
            logging.exception("AdsFly unexpected error: %s", exc)
            return destination_url
