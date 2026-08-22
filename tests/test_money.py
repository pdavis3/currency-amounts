import unittest

from currency_amounts import AmountParseError, Money, format_amount, parse_amount

# Each row: (label, input text, currency arg, expected Money)
PARSE_CASES = [
    ("plain decimal", "12.34", "USD", Money(1234, "USD")),
    ("leading zero", "0.05", "USD", Money(5, "USD")),
    ("no fraction at all", "12", "USD", Money(1200, "USD")),
    ("leading plus", "+12.34", "USD", Money(1234, "USD")),
    ("leading minus", "-12.34", "USD", Money(-1234, "USD")),
    ("trailing minus", "12.34-", "USD", Money(-1234, "USD")),
    ("parens negative", "(12.34)", "USD", Money(-1234, "USD")),
    ("parens with symbol inside", "($12.34)", None, Money(-1234, "USD")),
    ("whitespace padding", "  12.34  ", "USD", Money(1234, "USD")),
    ("symbol prefix", "$12.34", None, Money(1234, "USD")),
    ("symbol prefix negative", "-$12.34", None, Money(-1234, "USD")),
    ("symbol and negative swapped", "$-12.34", None, Money(-1234, "USD")),
    ("euro symbol suffix", "12,34€", None, Money(1234, "EUR")),
    ("code prefix", "USD 12.34", None, Money(1234, "USD")),
    ("code suffix", "12.34 USD", None, Money(1234, "USD")),
    ("lowercase code prefix", "usd 12.34", None, Money(1234, "USD")),
    ("code plus sign", "USD -12.34", None, Money(-1234, "USD")),
    ("us thousands grouping", "$1,234.56", None, Money(123456, "USD")),
    ("european thousands and decimal", "1.234,56 EUR", None, Money(123456, "EUR")),
    ("space thousands grouping", "1 234.56", "EUR", Money(123456, "EUR")),
    ("multiple thousands groups", "1,234,567.89", "USD", Money(123456789, "USD")),
    ("ambiguous comma defaults to grouping", "1,234", "USD", Money(123400, "USD")),
    ("comma as decimal when short", "12,34", "EUR", Money(1234, "EUR")),
    ("yen has no minor unit", "¥1000", None, Money(1000, "JPY")),
    ("yen with thousands grouping", "¥1,000", None, Money(1000, "JPY")),
    ("three-decimal currency", "KWD 12.345", None, Money(12345, "KWD")),
    ("three-decimal currency short fraction", "KWD 12.3", None, Money(12300, "KWD")),
    ("short fraction padded", "12.3", "USD", Money(1230, "USD")),
    ("unknown code falls back to two decimals", "SEK 12.34", None, Money(1234, "SEK")),
]

# Each row: (label, input text, currency arg) -> must raise AmountParseError
PARSE_ERROR_CASES = [
    ("empty string", "", "USD"),
    ("only whitespace", "   ", "USD"),
    ("no currency anywhere", "12.34", None),
    ("conflicting leading and trailing minus", "-12.34-", "USD"),
    ("double negative via parens and sign", "(-12.34)", "USD"),
    ("mismatched currency marker and argument", "USD 12.34", "EUR"),
    ("letters inside the number", "12a.34", "USD"),
    ("yen with a fraction", "¥10.00", None),
    ("too much precision for currency", "12.3456", "USD"),
    ("not a string", 1234, "USD"),
]

# Each row: (label, Money value, expected default rendering)
FORMAT_CASES = [
    ("plain", Money(1234, "USD"), "$12.34"),
    ("negative", Money(-1234, "USD"), "-$12.34"),
    ("thousands grouping", Money(123456, "USD"), "$1,234.56"),
    ("large amount", Money(123456789, "USD"), "$1,234,567.89"),
    ("yen has no fraction shown", Money(1000, "JPY"), "¥1,000"),
    ("three-decimal currency", Money(12345, "KWD"), "KWD 12.345"),
    ("unknown code uses code as marker", Money(1234, "SEK"), "SEK 12.34"),
    ("small amount under a hundred minor units", Money(5, "USD"), "$0.05"),
]


class ParseAmountTests(unittest.TestCase):
    def test_valid_cases(self):
        for label, text, currency, expected in PARSE_CASES:
            with self.subTest(label=label, text=text):
                self.assertEqual(parse_amount(text, currency), expected)

    def test_error_cases(self):
        for label, text, currency in PARSE_ERROR_CASES:
            with self.subTest(label=label, text=text):
                with self.assertRaises(AmountParseError):
                    parse_amount(text, currency)


class FormatAmountTests(unittest.TestCase):
    def test_default_rendering(self):
        for label, money, expected in FORMAT_CASES:
            with self.subTest(label=label, money=money):
                self.assertEqual(format_amount(money), expected)

    def test_symbol_can_be_suppressed(self):
        self.assertEqual(format_amount(Money(123456, "USD"), symbol=False), "1,234.56")

    def test_round_trip_through_parse_and_format(self):
        for text, currency in [("$1,234.56", None), ("KWD 12.345", None), ("¥1,000", None)]:
            money = parse_amount(text, currency)
            self.assertEqual(parse_amount(format_amount(money)), money)


if __name__ == "__main__":
    unittest.main()
