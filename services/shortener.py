import json
import logging

import aiohttp


class ShortenerService:
    def __init__(self, api_key: str, base_url: str = '', alias: str = ''):
        self.api_key = (api_key or '').strip()
        self.base_url = (base_url or '').strip()
        self.alias = (alias or '').strip()

    async def shorten_link(self, destination_url: str) -> str:
        # Direct-link fallback keeps downloads working if the provider is blocked or disabled.
        if not self.api_key or not self.base_url:
            return destination_url

        params = {'api': self.api_key, 'url': destination_url}
        if self.alias:
            params['alias'] = self.alias

        try:
            timeout = aiohttp.ClientTimeout(total=25)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.base_url, params=params, allow_redirects=True) as response:
                    raw = (await response.text()).strip()
                    if response.status != 200:
                        logging.warning('Shortener HTTP %s; using direct link', response.status)
                        return destination_url
                    if raw.startswith(('https://', 'http://')):
                        return raw
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        logging.warning('Shortener returned an unknown response; using direct link')
                        return destination_url

                    keys = ('shortenedUrl', 'shortened_url', 'shorturl', 'short_url', 'short', 'short_link', 'url', 'result')
                    for key in keys:
                        value = data.get(key)
                        if isinstance(value, str) and value.startswith(('https://', 'http://')):
                            return value
                        if isinstance(value, dict):
                            for nested in keys:
                                nested_value = value.get(nested)
                                if isinstance(nested_value, str) and nested_value.startswith(('https://', 'http://')):
                                    return nested_value
                    return destination_url
        except Exception as exc:
            logging.warning('Shortener failed; using direct link: %s', exc)
            return destination_url
