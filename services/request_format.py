"""Split a /request line into the parts admins actually need.

Users write it the way they talk about a movie:
    /request Don 2002 Hindi 1080p
    /request Don - 2002 - Hindi - 1080p
Both mean title Don, year 2002, Hindi audio, 1080p quality.
"""

import re

KNOWN_YEARS = range(1900, 2100)

AUDIO_LANGUAGES = {
    'hindi', 'english', 'telugu', 'tamil', 'kannada', 'malayalam', 'bengali',
    'marathi', 'gujarati', 'punjabi', 'odia', 'oriya', 'assamese', 'urdu',
    'nepali', 'sinhala', 'korean', 'japanese', 'chinese', 'spanish', 'french',
    'german', 'italian', 'portuguese', 'russian', 'arabic', 'turkish',
    'indonesian', 'malay', 'thai', 'vietnamese', 'dubbed', 'dual audio',
    'multi audio',
}

RESOLUTIONS = re.compile(
    r'^(?:4k|8k|hd|sd|full\s?hd|hdrip|\d{3,4}p(?:\s?x\s?\d{3,4})?)$', re.I
)

YEAR = re.compile(r'^\d{4}$')

SEPARATORS = re.compile(r'\s+[-–—|]\s+')


def _is_year(part: str) -> bool:
    return bool(YEAR.match(part)) and 1900 <= int(part) < 2100


def _is_language(part: str) -> bool:
    return part.lower().strip() in AUDIO_LANGUAGES


def _is_resolution(part: str) -> bool:
    return bool(RESOLUTIONS.match(part.strip()))


def parse_request(text: str) -> dict:
    raw = ' '.join((text or '').split()).strip()

    parts = [p.strip() for p in SEPARATORS.split(raw) if p.strip()] if SEPARATORS.search(raw) else [raw]
    parts = [p for p in parts if p]

    year = language = resolution = ''
    title_parts = []

    if len(parts) > 1:
        for part in parts:
            if not year and _is_year(part):
                year = part
            elif not resolution and _is_resolution(part):
                resolution = part
            elif not language and _is_language(part):
                language = part.title()
            else:
                title_parts.append(part)
    else:
        words = raw.split()
        index = 0
        while index < len(words):
            word = words[index]
            following = words[index + 1] if index + 1 < len(words) else ''

            if not year and _is_year(word):
                year = word
            elif not resolution and _is_resolution(word):
                resolution = word
            elif not language and following and _is_language(f'{word} {following}'):
                # "dual audio" spans two words; plain "Hindi" does not.
                language = f'{word} {following}'.title()
                index += 1
            elif not language and _is_language(word):
                language = word.title()
            else:
                title_parts.append(word)

            index += 1

    title = ' '.join(title_parts).strip() or raw

    return {
        'title': title,
        'year': year,
        'audio_language': language,
        'resolution': resolution,
        'display': display_title(title, year, language, resolution),
    }


def display_title(title: str, year: str = '', language: str = '', resolution: str = '') -> str:
    """One line that carries everything the user asked for."""
    text = title
    if year:
        text = f'{text} ({year})'
    extras = ' · '.join(part for part in (language, resolution) if part)
    return f'{text} · {extras}' if extras else text
