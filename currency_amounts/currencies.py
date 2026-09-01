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
    "SEK": 2,
    "NOK": 2,
    "DKK": 2,
    "XAF": 0,
    "XOF": 0,
}

DEFAULT_MINOR_UNITS = 2

# Deliberately small: these four symbols are unambiguous on their own.
SYMBOL_TO_CURRENCY = {
    "$": "USD",
    "€": "EUR",  # €
    "£": "GBP",  # £
    "¥": "JPY",  # ¥
}

CURRENCY_TO_SYMBOL = {code: symbol for symbol, code in SYMBOL_TO_CURRENCY.items()}

# Symbols that several currencies share, so the text alone can't say which
# one is meant. The caller has to pass the intended currency; parsing fails
# with the candidate list rather than guessing. Not exhaustive - just the
# two ambiguous symbols this project has actually run into so far.
AMBIGUOUS_SYMBOLS = {
    "kr": ("DKK", "NOK", "SEK"),
    "fr": ("CHF", "XAF", "XOF"),
}
