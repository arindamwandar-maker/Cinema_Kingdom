import json
import logging
import secrets
from typing import Any, Optional

import aiohttp


class ShortenerService:

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.gplinks.com/api",
        alias: str = "",
        response_format: str = "json"
    ):
        self.api_key = (api_key or "").strip()
        self.base_url = (
            base_url or "https://api.gplinks.com/api"
        ).strip()
        self.alias = (alias or "").strip()
        self.response_format = (
            response_format or "json"
        ).strip().lower()

    @staticmethod
    def _is_url(value: Any) -> bool:
        return (
            isinstance(value, str)
            and value.strip().startswith(
                ("https://", "http://")
            )
        )

    def _extract_url(
        self,
        data: Any
    ) -> Optional[str]:

        if self._is_url(data):
            return data.strip()

        if not isinstance(data, dict):
            return None

        status = str(
            data.get("status", "")
        ).strip().lower()

        if status == "error":
            logging.warning(
                "GPLinks API error: %s",
                data.get("message", data)
            )
            return None

        possible_keys = (
            "shortenedUrl",
            "shortened_url",
            "shorturl",
            "short_url",
            "short",
            "short_link",
            "url",
            "result",
            "data"
        )

        for key in possible_keys:
            value = data.get(key)

            if self._is_url(value):
                return value.strip()

            if isinstance(value, dict):
                nested_url = self._extract_url(value)

                if nested_url:
                    return nested_url

        return None

    async def shorten_link(
        self,
        destination_url: str
    ) -> str:

        destination_url = (
            destination_url or ""
        ).strip()

        if not destination_url:
            return destination_url

        if not self.api_key:
            logging.warning(
                "SHORTENER_API_KEY missing. "
                "Using direct Telegram link."
            )
            return destination_url

        aliases_to_try = []

        if self.alias:
            alias_prefix = self.alias.rstrip("-_")

            unique_alias = (
                f"{alias_prefix}-"
                f"{secrets.token_hex(4)}"
            )

            aliases_to_try.append(unique_alias)

        aliases_to_try.append("")

        timeout = aiohttp.ClientTimeout(
            total=30
        )

        for alias_value in aliases_to_try:

            params = {
                "api": self.api_key,
                "url": destination_url
            }

            if alias_value:
                params["alias"] = alias_value

            if self.response_format == "text":
                params["format"] = "text"

            try:
                async with aiohttp.ClientSession(
                    timeout=timeout
                ) as session:

                    async with session.get(
                        self.base_url,
                        params=params,
                        allow_redirects=True,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 "
                                "CinemaKingdomBot/2.0"
                            ),
                            "Accept": (
                                "application/json,"
                                "text/plain,*/*"
                            )
                        }
                    ) as response:

                        raw_text = (
                            await response.text()
                        ).strip()

                        logging.info(
                            "GPLinks status=%s response=%s",
                            response.status,
                            raw_text[:500]
                        )

                        if response.status != 200:
                            logging.warning(
                                "GPLinks HTTP error: %s",
                                response.status
                            )
                            continue

                        if self._is_url(raw_text):
                            return raw_text

                        try:
                            parsed_data = json.loads(
                                raw_text
                            )

                        except json.JSONDecodeError:
                            logging.warning(
                                "GPLinks invalid response: %s",
                                raw_text[:500]
                            )
                            continue

                        short_url = self._extract_url(
                            parsed_data
                        )

                        if short_url:
                            return short_url

                        logging.warning(
                            "Unknown GPLinks response: %s",
                            parsed_data
                        )

            except aiohttp.ClientError as exc:
                logging.warning(
                    "GPLinks network error: %s",
                    exc
                )

            except Exception as exc:
                logging.exception(
                    "GPLinks unexpected error: %s",
                    exc
                )

        logging.warning(
            "GPLinks failed. "
            "Using direct Telegram link."
        )

        return destination_url