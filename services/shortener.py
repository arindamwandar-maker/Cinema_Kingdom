import json
import logging
import secrets

import aiohttp


class ShortenerService:
    def __init__(
        self,
        api_key: str,
        base_url: str = 'https://api.gplinks.com/api',
        alias: str = '',
        response_format: str = 'json',
    ):
        self.api_key = (api_key or '').strip()
        self.base_url = (base_url or 'https://api.gplinks.com/api').strip()
        self.alias = (alias or '').strip()
        self.response_format = (response_format or 'json').strip().lower()

    async def shorten_link(self, destination_url: str) -> str:
        """Return a GPLinks short URL, or the original Telegram deep link on failure."""
        if not self.api_key or not self.base_url:
            return destination_url

        # A fixed alias cannot be reused for every movie. Add a small unique suffix.
        alias_value = ''
        if self.alias:
            alias_value = f"{self.alias.rstrip('-_')}-{secrets.token_hex(3)}"

        attempts = []
        if alias_value:
            attempts.append(alias_value)
        attempts.append('')

        timeout = aiohttp.ClientTimeout(total=30)

        for alias in attempts:
            params = {
                'api': self.api_key,
                'url': destination_url,
            }
            if alias:
                params['alias'] = alias
            if self.response_format == 'text':
                params['format'] = 'text'

            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        self.base_url,
                        params=params,
                        allow_redirects=True,
                        headers={'User-Agent': 'CinemaKingdomBot/1.0'},
                    ) as response:
                        raw = (await response.text()).strip()

                        if response.status != 200:
                            logging.warning(
                                'GPLinks HTTP %s response=%s',
                                response.status,
                                raw[:300],
                            )
                            continue

                        # Text response mode returns the URL directly.
                        if raw.startswith(('https://', 'http://')):
                            return raw

                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError:
                            logging.warning('GPLinks returned invalid response: %s', raw[:300])
                            continue

                        if str(data.get('status', '')).lower() == 'error':
                            logging.warning('GPLinks error: %s', data.get('message', data))
                            continue

                        value = data.get('shortenedUrl')
                        if isinstance(value, str) and value.startswith(('https://', 'http://')):
                            return value

                        for key in ('shorturl', 'short_url', 'short', 'short_link', 'url', 'result'):
                            value = data.get(key)
                            if isinstance(value, str) and value.startswith(('https://', 'http://')):
                                return value

                        logging.warning('GPLinks unknown JSON response: %s', data)
            except Exception as exc:
                logging.warning('GPLinks request failed: %s', exc)

        logging.warning('GPLinks unavailable; using direct Telegram link')
        return destination_url
