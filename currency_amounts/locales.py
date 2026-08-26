"""Regional conventions for rendering an amount as text.

Same spirit as CURRENCY_MINOR_UNITS in currencies.py: this only covers the
locales this project has had a concrete reason to format for, and an
unrecognized locale key falls back to DEFAULT_LOCALE rather than raising,
since guessing wrong about punctuation is a cosmetic problem, not a
correctness one.

Grouping schemes that don't split digits into groups of three - the Indian
lakh/crore system, for instance - aren't modeled here. See the README.
"""

from collections import namedtuple

# thousands_sep / decimal_sep: the grouping and fraction punctuation.
# symbol_after: currency marker goes after the number instead of before.
# symbol_space: put a space between the marker and the number. Currency
# codes (SEK, CHF, ...) always get a space regardless of this flag - it's
# only symbols like $ and € that can go either way.
LocaleFormat = namedtuple(
    "LocaleFormat", ["thousands_sep", "decimal_sep", "symbol_after", "symbol_space"]
)

DEFAULT_LOCALE = "en_US"

LOCALE_FORMATS = {
    "en_US": LocaleFormat(",", ".", symbol_after=False, symbol_space=False),
    "en_GB": LocaleFormat(",", ".", symbol_after=False, symbol_space=False),
    "de_DE": LocaleFormat(".", ",", symbol_after=True, symbol_space=True),
    "fr_FR": LocaleFormat(" ", ",", symbol_after=True, symbol_space=True),
    "de_CH": LocaleFormat("'", ".", symbol_after=False, symbol_space=True),
}
