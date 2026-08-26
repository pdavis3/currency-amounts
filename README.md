# currency-amounts

A small parser and pretty printer for currency amounts written as text.

## The problem

Amounts show up as text in a lot of places: pasted from an invoice, typed
into a form, dumped from a CSV export. The formatting is never consistent.
`$1,234.56`, `1.234,56 EUR`, `(12.00)` for a negative, `¥1000` with no
decimal places at all, `KWD 12.345` with three. Parsing this with `float()`
and a bit of string stripping works until it doesn't, usually silently,
because binary floating point can't represent most decimal fractions
exactly and different currencies don't even agree on how many fraction
digits they have.

This library parses that text into an exact integer amount (minor units,
like cents) tagged with a currency code, and can render it back out into a
readable string.

## Usage

```python
from currency_amounts import parse_amount, format_amount, AmountParseError

money = parse_amount("$1,234.56")
print(money)                 # $1,234.56
print(money.units)           # 123456
print(money.currency)        # USD

# Currency can also come from an explicit argument when the text has none:
parse_amount("1 234,50", currency="EUR")

# Negative amounts: leading minus, trailing minus, or accounting parens
parse_amount("-12.00", currency="USD")
parse_amount("12.00-", currency="USD")
parse_amount("(12.00)", currency="USD")

# Currencies with a different number of minor units are handled correctly
parse_amount("KWD 12.345")   # Kuwaiti dinar, 3 decimal places
parse_amount("¥1000")        # yen, no decimal places

try:
    parse_amount("¥10.00")   # yen has no fractional unit
except AmountParseError as exc:
    print(exc)

# format_amount can drop the currency marker if you just want the number
format_amount(money, symbol=False)   # "1,234.56"

# Or render it with another locale's grouping, decimal point, and marker
# placement instead of the US-style default:
eur = parse_amount("1.234,56", currency="EUR")
format_amount(eur, locale="de_DE")   # "1.234,56 €"
format_amount(eur, locale="fr_FR")   # "1 234,56 €"

# Arithmetic stays exact because it's all integer minor units underneath.
# +, -, unary -, abs(), *, and ordering all require matching currencies.
total = parse_amount("$10.00") + parse_amount("$2.50")   # $12.50
tripled = parse_amount("$1.25") * 3                       # $3.75

# Splitting an amount N ways without losing or inventing minor units:
parse_amount("$10.00").allocate([1, 1, 1])
# [Money(334, 'USD'), Money(333, 'USD'), Money(333, 'USD')]
```

`Money` is a plain value object: two fields, `units` (an `int`, in the
currency's minor unit) and `currency` (an ISO 4217 code).

## Known limitations

- Only four currency symbols are recognized directly (`$`, `€`, `£`, `¥`).
  Symbols shared across multiple currencies, like `kr` or `Fr`, aren't
  handled — pass the currency code explicitly instead.
- When a number has exactly one separator and no currency-specific hint
  (say, `1,234`), the parser guesses based on group length rather than
  locale. This is documented and tested in `tests/test_money.py` rather
  than hidden.
- `format_amount`'s `locale` argument covers a handful of regional
  punctuation and marker-placement conventions (see
  `currency_amounts/locales.py`), not every locale glibc knows about.
  Grouping schemes that don't split digits into groups of three, like the
  Indian lakh/crore system, aren't modeled.

## Running the tests

```
python -m unittest discover tests
```

## License

MIT, see `LICENSE`.
