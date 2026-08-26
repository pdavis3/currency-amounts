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
from .locales import DEFAULT_LOCALE, LOCALE_FORMATS

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

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        self._require_same_currency(other, "add")
        return Money(self.units + other.units, self.currency)

    def __sub__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        self._require_same_currency(other, "subtract")
        return Money(self.units - other.units, self.currency)

    def __neg__(self):
        return Money(-self.units, self.currency)

    def __abs__(self):
        return Money(abs(self.units), self.currency)

    def __mul__(self, factor):
        if not isinstance(factor, int):
            return NotImplemented
        return Money(self.units * factor, self.currency)

    __rmul__ = __mul__

    def __lt__(self, other):
        return self._compare(other) < 0

    def __le__(self, other):
        return self._compare(other) <= 0

    def __gt__(self, other):
        return self._compare(other) > 0

    def __ge__(self, other):
        return self._compare(other) >= 0

    def _require_same_currency(self, other, verb):
        if self.currency != other.currency:
            raise ValueError(f"cannot {verb} {self.currency} and {other.currency}")

    def _compare(self, other):
        if not isinstance(other, Money):
            raise TypeError(f"cannot compare Money with {type(other).__name__}")
        self._require_same_currency(other, "compare")
        return (self.units > other.units) - (self.units < other.units)

    def allocate(self, ratios):
        """Split this amount into len(ratios) parts proportional to ratios.

        Plain "amount * ratio / total" splitting drops or invents minor
        units whenever the division isn't exact (splitting 10 cents three
        ways gives 3.33... each). This uses the largest-remainder method
        instead: take the integer share each ratio is entitled to, then
        hand the leftover minor units one at a time to the parts with the
        largest dropped remainder, so the parts always sum back to exactly
        this amount.
        """
        if not ratios or any(r < 0 for r in ratios) or not any(ratios):
            raise ValueError(
                "ratios must be a non-empty list of non-negative numbers "
                "with at least one positive value"
            )

        total_ratio = sum(ratios)
        negative = self.units < 0
        magnitude = abs(self.units)

        shares = [magnitude * r // total_ratio for r in ratios]
        leftover = magnitude - sum(shares)

        by_dropped_remainder = sorted(
            range(len(ratios)),
            key=lambda i: (magnitude * ratios[i]) % total_ratio,
            reverse=True,
        )
        for i in by_dropped_remainder[:leftover]:
            shares[i] += 1

        if negative:
            shares = [-s for s in shares]

        return [Money(s, self.currency) for s in shares]


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


def format_amount(money, symbol=True, thousands_sep=None, locale=None):
    """Render a Money value back into a display string.

    `locale` selects a regional convention (see currency_amounts.locales)
    for the grouping/decimal punctuation and where the currency marker
    sits, e.g. locale="de_DE" renders 1234.56 EUR as "1.234,56 €" instead
    of the "en_US" default "€1,234.56". An unrecognized locale falls back
    to the default rather than raising. `thousands_sep`, if given, still
    overrides the locale's grouping character.
    """
    fmt = LOCALE_FORMATS.get(locale or DEFAULT_LOCALE, LOCALE_FORMATS[DEFAULT_LOCALE])
    if thousands_sep is None:
        thousands_sep = fmt.thousands_sep

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
    body = f"{grouped}{fmt.decimal_sep}{fraction}" if fraction else grouped

    if not symbol:
        return f"{sign}{body}"

    known_symbol = CURRENCY_TO_SYMBOL.get(money.currency)
    marker = known_symbol if known_symbol is not None else money.currency
    marker_space = fmt.symbol_space if known_symbol is not None else True
    sep = " " if marker_space else ""

    if fmt.symbol_after:
        return f"{sign}{body}{sep}{marker}"
    return f"{sign}{marker}{sep}{body}"


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
