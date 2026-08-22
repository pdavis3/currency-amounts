"""Parse and format currency amounts without ever touching a float.

Amounts are stored as integer minor units (cents, fils, whatever the
currency's smallest unit is) so that rounding errors from binary floating
point never enter the picture.
"""

import re

from .currencies import (
    CURRENCY_MINOR_UNITS,
    CURRENCY_TO_SYMBOL,
    DEFAULT_MINOR_UNITS,
    SYMBOL_TO_CURRENCY,
)

_PARENS_RE = re.compile(r"^\((.*)\)$")
_NUMBER_RE = re.compile(r"^[0-9](?:[0-9,.\s]*[0-9])?$")


class AmountParseError(ValueError):
    pass


class Money:
    __slots__ = ("units", "currency")

    def __init__(self, units, currency):
        self.units = units
        self.currency = currency

    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return self.units == other.units and self.currency == other.currency

    def __hash__(self):
        return hash((self.units, self.currency))

    def __repr__(self):
        return f"Money({self.units!r}, {self.currency!r})"

    def __str__(self):
        return format_amount(self)


def parse_amount(text, currency=None):
    """Parse freeform text like "$1,234.56" or "(12.00)" into a Money value.

    `currency` is an ISO 4217 code used when the text has no symbol or code
    of its own. If the text does carry a currency marker it must agree with
    `currency`, if one was given.
    """
    if not isinstance(text, str):
        raise AmountParseError(f"expected str, got {type(text).__name__}")

    if currency is not None:
        currency = currency.upper()

    raw = text.strip()
    if not raw:
        raise AmountParseError("empty amount")

    negative = False
    parens = _PARENS_RE.match(raw)
    if parens:
        negative = True
        raw = parens.group(1).strip()

    raw, sign_before = _extract_sign(raw, text)
    raw, detected_currency = _strip_currency_marker(raw)
    raw, sign_after = _extract_sign(raw, text)

    if (parens and (sign_before or sign_after)) or (sign_before and sign_after):
        raise AmountParseError(f"conflicting sign in {text!r}")
    negative = negative or sign_before or sign_after

    if currency is None:
        currency = detected_currency
    elif detected_currency is not None and detected_currency != currency:
        raise AmountParseError(
            f"amount says {detected_currency} but caller expects {currency}"
        )

    if currency is None:
        raise AmountParseError(f"no currency given or detected in {text!r}")

    if not raw:
        raise AmountParseError(f"no digits found in {text!r}")
    if not _NUMBER_RE.match(raw):
        raise AmountParseError(f"malformed number {raw!r} in {text!r}")

    minor_digits = CURRENCY_MINOR_UNITS.get(currency, DEFAULT_MINOR_UNITS)
    integer_part, fraction_part = _split_integer_fraction(raw, minor_digits, text)

    if minor_digits == 0 and fraction_part:
        raise AmountParseError(f"{currency} has no minor unit but {text!r} has a fraction")
    if len(fraction_part) > minor_digits:
        raise AmountParseError(f"{text!r} has more precision than {currency} allows")
    fraction_part = fraction_part.ljust(minor_digits, "0")

    units = int(integer_part) * (10 ** minor_digits)
    if fraction_part:
        units += int(fraction_part)
    if negative:
        units = -units

    return Money(units, currency)


def format_amount(money, symbol=True, thousands_sep=","):
    """Render a Money value back into a display string.

    This is intentionally a single, simple style (sign, marker, grouped
    integer part, dot, fraction) rather than a locale-aware formatter.
    """
    minor_digits = CURRENCY_MINOR_UNITS.get(money.currency, DEFAULT_MINOR_UNITS)
    sign = "-" if money.units < 0 else ""
    magnitude = abs(money.units)

    if minor_digits == 0:
        integer_units, fraction = magnitude, ""
    else:
        divisor = 10 ** minor_digits
        integer_units, fraction_value = divmod(magnitude, divisor)
        fraction = str(fraction_value).rjust(minor_digits, "0")

    grouped = _group_thousands(str(integer_units), thousands_sep)
    body = f"{grouped}.{fraction}" if fraction else grouped

    if not symbol:
        return f"{sign}{body}"

    marker = CURRENCY_TO_SYMBOL.get(money.currency, f"{money.currency} ")
    return f"{sign}{marker}{body}"


def _extract_sign(raw, original_text):
    leading_minus = raw.startswith("-")
    leading_plus = raw.startswith("+")
    trailing_minus = raw.endswith("-")

    if leading_minus and trailing_minus:
        raise AmountParseError(f"conflicting sign in {original_text!r}")

    if leading_minus:
        return raw[1:].strip(), True
    if leading_plus:
        return raw[1:].strip(), False
    if trailing_minus:
        return raw[:-1].strip(), True
    return raw, False


def _strip_currency_marker(raw):
    for symbol, code in SYMBOL_TO_CURRENCY.items():
        if raw.startswith(symbol):
            return raw[len(symbol):].strip(), code
        if raw.endswith(symbol):
            return raw[: -len(symbol)].strip(), code

    words = raw.split()
    if words and words[0].isalpha() and len(words[0]) == 3:
        return " ".join(words[1:]).strip(), words[0].upper()
    if words and words[-1].isalpha() and len(words[-1]) == 3:
        return " ".join(words[:-1]).strip(), words[-1].upper()

    return raw, None


def _split_integer_fraction(raw, minor_digits, original_text):
    has_comma = "," in raw
    has_dot = "." in raw

    if has_comma and has_dot:
        # Whichever separator appears last is the decimal point; the other
        # one is thousands grouping. Handles both "1,234.56" and "1.234,56".
        decimal_sep = "," if raw.rfind(",") > raw.rfind(".") else "."
        thousands_sep = "." if decimal_sep == "," else ","
        integer_part, _, fraction_part = raw.rpartition(decimal_sep)
        integer_part = integer_part.replace(thousands_sep, "")
    elif has_comma or has_dot:
        sep = "," if has_comma else "."
        pieces = raw.split(sep)
        if len(pieces) > 2:
            # Repeated separator: it can only be thousands grouping.
            integer_part, fraction_part = "".join(pieces), ""
        else:
            first, last = pieces
            if len(last) == minor_digits:
                # Matches the currency's own precision: it's a fraction,
                # even if that happens to be 3 digits (KWD, BHD, OMR).
                integer_part, fraction_part = first, last
            elif len(last) == 3:
                # A trailing group of exactly 3 that doesn't match the
                # currency's precision reads as thousands grouping.
                integer_part, fraction_part = first + last, ""
            else:
                integer_part, fraction_part = first, last
    else:
        integer_part, fraction_part = raw, ""

    integer_part = integer_part.replace(" ", "")
    fraction_part = fraction_part.replace(" ", "")
    if not integer_part:
        integer_part = "0"
    if not integer_part.isdigit() or (fraction_part and not fraction_part.isdigit()):
        raise AmountParseError(f"malformed number in {original_text!r}")

    return integer_part, fraction_part


def _group_thousands(digits, sep):
    if len(digits) <= 3:
        return digits
    groups = []
    while len(digits) > 3:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    groups.insert(0, digits)
    return sep.join(groups)
