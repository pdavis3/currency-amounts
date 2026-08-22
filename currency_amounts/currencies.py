# ISO 4217 minor unit counts, limited to the currencies this project has
# actually needed to parse so far. Anything missing falls back to
# DEFAULT_MINOR_UNITS rather than raising, since most of the world uses 2.
CURRENCY_MINOR_UNITS = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "CHF": 2,
    "CAD": 2,
    "AUD": 2,
    "INR": 2,
    "CNY": 2,
    "MXN": 2,
    "BRL": 2,
    "JPY": 0,
    "KRW": 0,
    "CLP": 0,
    "VND": 0,
    "KWD": 3,
    "BHD": 3,
    "OMR": 3,
}

DEFAULT_MINOR_UNITS = 2

# Deliberately small: these four symbols are unambiguous on their own.
# Symbols like "kr" or "Fr" are shared by several currencies and are left
# for callers to disambiguate by passing an explicit currency code.
SYMBOL_TO_CURRENCY = {
    "$": "USD",
    "€": "EUR",  # €
    "£": "GBP",  # £
    "¥": "JPY",  # ¥
}

CURRENCY_TO_SYMBOL = {code: symbol for symbol, code in SYMBOL_TO_CURRENCY.items()}
