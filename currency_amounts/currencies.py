# ISO 4217 minor unit counts. Two digits is the default for the vast
# majority of currencies (DEFAULT_MINOR_UNITS below), so this table only
# needs to carry the exceptions: currencies with zero, three, or four
# decimal digits. A code that isn't in here - whether it's a mainstream
# 2-digit currency or one this table simply doesn't know about yet - falls
# back to DEFAULT_MINOR_UNITS rather than raising.
CURRENCY_MINOR_UNITS = {
    # Zero decimal digits.
    "BIF": 0,  # Burundian franc
    "CLP": 0,  # Chilean peso
    "DJF": 0,  # Djiboutian franc
    "GNF": 0,  # Guinean franc
    "ISK": 0,  # Icelandic krona
    "JPY": 0,  # Japanese yen
    "KMF": 0,  # Comorian franc
    "KRW": 0,  # South Korean won
    "PYG": 0,  # Paraguayan guarani
    "RWF": 0,  # Rwandan franc
    "UGX": 0,  # Ugandan shilling
    "UYI": 0,  # Uruguay peso en unidades indexadas
    "VND": 0,  # Vietnamese dong
    "VUV": 0,  # Vanuatu vatu
    "XAF": 0,  # CFA franc BEAC
    "XOF": 0,  # CFA franc BCEAO
    "XPF": 0,  # CFP franc
    # Three decimal digits.
    "BHD": 3,  # Bahraini dinar
    "IQD": 3,  # Iraqi dinar
    "JOD": 3,  # Jordanian dinar
    "KWD": 3,  # Kuwaiti dinar
    "LYD": 3,  # Libyan dinar
    "OMR": 3,  # Omani rial
    "TND": 3,  # Tunisian dinar
    # Four decimal digits.
    "CLF": 4,  # Chilean unidad de fomento
    "UYW": 4,  # Uruguay unidad previsional
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
