"""Where our members live, so we know which cinema to upload next.

A member taps their country, or shares their Telegram contact, and the pair is
stored on the users row. Telegram only ever hands over a phone number the user
offers on purpose - there is no way to read it silently - so a blank means that
member never pressed the button.
"""

from telegram import InlineKeyboardButton

# country code -> flag and english name, in the order the picker shows them.
COUNTRIES = [
    ('IN', '🇮🇳 India'),
    ('US', '🇺🇸 USA'),
    ('GB', '🇬🇧 UK'),
    ('CA', '🇨🇦 Canada'),
    ('AU', '🇦🇺 Australia'),
    ('BD', '🇧🇩 Bangladesh'),
    ('PK', '🇵🇰 Pakistan'),
    ('NP', '🇳🇵 Nepal'),
    ('LK', '🇱🇰 Sri Lanka'),
    ('BT', '🇧🇹 Bhutan'),
    ('MV', '🇲🇻 Maldives'),
    ('AE', '🇦🇪 UAE'),
    ('SA', '🇸🇦 Saudi Arabia'),
    ('QA', '🇶🇦 Qatar'),
    ('KW', '🇰🇼 Kuwait'),
    ('OM', '🇴🇲 Oman'),
    ('BH', '🇧🇭 Bahrain'),
    ('YE', '🇾🇪 Yemen'),
    ('JO', '🇯🇴 Jordan'),
    ('LB', '🇱🇧 Lebanon'),
    ('IQ', '🇮🇶 Iraq'),
    ('IR', '🇮🇷 Iran'),
    ('TR', '🇹🇷 Türkiye'),
    ('IL', '🇮🇱 Israel'),
    ('EG', '🇪🇬 Egypt'),
    ('MA', '🇲🇦 Morocco'),
    ('DZ', '🇩🇿 Algeria'),
    ('TN', '🇹🇳 Tunisia'),
    ('NG', '🇳🇬 Nigeria'),
    ('GH', '🇬🇭 Ghana'),
    ('KE', '🇰🇪 Kenya'),
    ('ZA', '🇿🇦 South Africa'),
    ('TZ', '🇹🇿 Tanzania'),
    ('UG', '🇺🇬 Uganda'),
    ('MU', '🇲🇺 Mauritius'),
    ('FJ', '🇫🇯 Fiji'),
    ('ID', '🇮🇩 Indonesia'),
    ('MY', '🇲🇾 Malaysia'),
    ('SG', '🇸🇬 Singapore'),
    ('TH', '🇹🇭 Thailand'),
    ('VN', '🇻🇳 Vietnam'),
    ('PH', '🇵🇭 Philippines'),
    ('MM', '🇲🇲 Myanmar'),
    ('KH', '🇰🇭 Cambodia'),
    ('LA', '🇱🇦 Laos'),
    ('BN', '🇧🇳 Brunei'),
    ('TL', '🇹🇱 Timor-Leste'),
    ('CN', '🇨🇳 China'),
    ('TW', '🇹🇼 Taiwan'),
    ('HK', '🇭🇰 Hong Kong'),
    ('JP', '🇯🇵 Japan'),
    ('KR', '🇰🇷 South Korea'),
    ('MN', '🇲🇳 Mongolia'),
    ('KZ', '🇰🇿 Kazakhstan'),
    ('UZ', '🇺🇿 Uzbekistan'),
    ('RU', '🇷🇺 Russia'),
    ('UA', '🇺🇦 Ukraine'),
    ('BY', '🇧🇾 Belarus'),
    ('PL', '🇵🇱 Poland'),
    ('DE', '🇩🇪 Germany'),
    ('FR', '🇫🇷 France'),
    ('ES', '🇪🇸 Spain'),
    ('PT', '🇵🇹 Portugal'),
    ('IT', '🇮🇹 Italy'),
    ('GR', '🇬🇷 Greece'),
    ('CY', '🇨🇾 Cyprus'),
    ('NL', '🇳🇱 Netherlands'),
    ('BE', '🇧🇪 Belgium'),
    ('CH', '🇨🇭 Switzerland'),
    ('AT', '🇦🇹 Austria'),
    ('CZ', '🇨🇿 Czechia'),
    ('SK', '🇸🇰 Slovakia'),
    ('HU', '🇭🇺 Hungary'),
    ('RO', '🇷🇴 Romania'),
    ('BG', '🇧🇬 Bulgaria'),
    ('RS', '🇷🇸 Serbia'),
    ('HR', '🇭🇷 Croatia'),
    ('SI', '🇸🇮 Slovenia'),
    ('BA', '🇧🇦 Bosnia'),
    ('MK', '🇲🇰 North Macedonia'),
    ('AL', '🇦🇱 Albania'),
    ('XK', '🇽🇰 Kosovo'),
    ('LT', '🇱🇹 Lithuania'),
    ('LV', '🇱🇻 Latvia'),
    ('EE', '🇪🇪 Estonia'),
    ('FI', '🇫🇮 Finland'),
    ('SE', '🇸🇪 Sweden'),
    ('NO', '🇳🇴 Norway'),
    ('DK', '🇩🇰 Denmark'),
    ('IS', '🇮🇸 Iceland'),
    ('IE', '🇮🇪 Ireland'),
    ('NZ', '🇳🇿 New Zealand'),
    ('MX', '🇲🇽 Mexico'),
    ('GT', '🇬🇹 Guatemala'),
    ('CU', '🇨🇺 Cuba'),
    ('DO', '🇩🇴 Dominican Republic'),
    ('JM', '🇯🇲 Jamaica'),
    ('TT', '🇹🇹 Trinidad & Tobago'),
    ('CO', '🇨🇴 Colombia'),
    ('VE', '🇻🇪 Venezuela'),
    ('EC', '🇪🇨 Ecuador'),
    ('PE', '🇵🇪 Peru'),
    ('BO', '🇧🇴 Bolivia'),
    ('PY', '🇵🇾 Paraguay'),
    ('UY', '🇺🇾 Uruguay'),
    ('AR', '🇦🇷 Argentina'),
    ('CL', '🇨🇱 Chile'),
    ('BR', '🇧🇷 Brazil'),
    ('PA', '🇵🇦 Panama'),
    ('CR', '🇨🇷 Costa Rica'),
]

# Shown on the first page, in this order.
TOP_COUNTRIES = ['IN', 'US', 'GB', 'CA', 'AU', 'BD', 'PK', 'NP']

BUTTONS_PER_PAGE = 8

NAMES = {code: label for code, label in COUNTRIES}

# Dialling code -> country. A handful of codes cover several countries (+1 North
# America, +7 Russia and Kazakhstan); the most likely one wins, and the member
# can still correct it from the picker.
DIALING = {
    '91': 'IN', '1': 'US', '44': 'GB', '353': 'IE', '61': 'AU', '64': 'NZ',
    '880': 'BD', '92': 'PK', '977': 'NP', '94': 'LK', '975': 'BT', '960': 'MV',
    '971': 'AE', '966': 'SA', '974': 'QA', '965': 'KW', '968': 'OM', '973': 'BH',
    '967': 'YE', '962': 'JO', '961': 'LB', '964': 'IQ', '98': 'IR', '90': 'TR',
    '972': 'IL', '20': 'EG', '212': 'MA', '213': 'DZ', '216': 'TN', '234': 'NG',
    '233': 'GH', '254': 'KE', '27': 'ZA', '255': 'TZ', '256': 'UG', '230': 'MU',
    '679': 'FJ', '62': 'ID', '60': 'MY', '65': 'SG', '66': 'TH', '84': 'VN',
    '63': 'PH', '95': 'MM', '855': 'KH', '856': 'LA', '673': 'BN', '670': 'TL',
    '86': 'CN', '886': 'TW', '852': 'HK', '81': 'JP', '82': 'KR', '976': 'MN',
    '7': 'RU', '380': 'UA', '375': 'BY', '48': 'PL', '49': 'DE', '33': 'FR',
    '34': 'ES', '351': 'PT', '39': 'IT', '30': 'GR', '357': 'CY', '31': 'NL',
    '32': 'BE', '41': 'CH', '43': 'AT', '420': 'CZ', '421': 'SK', '36': 'HU',
    '40': 'RO', '359': 'BG', '381': 'RS', '385': 'HR', '386': 'SI', '387': 'BA',
    '389': 'MK', '355': 'AL', '383': 'XK', '370': 'LT', '371': 'LV', '372': 'EE',
    '358': 'FI', '46': 'SE', '47': 'NO', '45': 'DK', '354': 'IS', '52': 'MX',
    '502': 'GT', '53': 'CU', '1809': 'DO', '1876': 'JM', '1868': 'TT',
    '57': 'CO', '58': 'VE', '593': 'EC', '51': 'PE', '591': 'BO', '595': 'PY',
    '598': 'UY', '54': 'AR', '56': 'CL', '55': 'BR', '507': 'PA', '506': 'CR',
}

# Longest dialling codes first so +1809 is not read as +1.
_DIALING_BY_LENGTH = sorted(DIALING.items(), key=lambda item: len(item[0]), reverse=True)


def country_name(code: str) -> str:
    return NAMES.get(code, code or '')


def country_pages() -> int:
    rest = len([code for code, _ in COUNTRIES if code not in TOP_COUNTRIES])
    return 1 + (rest + BUTTONS_PER_PAGE - 1) // BUTTONS_PER_PAGE


def country_rows(page: int = 0):
    """Two countries per button row; page 0 is the common ones + More."""
    if page == 0:
        codes = TOP_COUNTRIES
    else:
        rest = [code for code, _ in COUNTRIES if code not in TOP_COUNTRIES]
        start = (page - 1) * BUTTONS_PER_PAGE
        codes = rest[start:start + BUTTONS_PER_PAGE]

    rows = []
    for index in range(0, len(codes), 2):
        rows.append([
            InlineKeyboardButton(NAMES[code], callback_data=f'country_{code}')
            for code in codes[index:index + 2]
        ])
    return rows


def country_from_phone(phone: str) -> str:
    """Best guess at a country from a shared contact number."""
    digits = ''.join(char for char in (phone or '') if char.isdigit())
    if not digits:
        return ''

    for dialing, code in _DIALING_BY_LENGTH:
        if digits.startswith(dialing):
            return code

    return ''
