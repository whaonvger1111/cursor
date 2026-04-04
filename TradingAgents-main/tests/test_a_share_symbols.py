"""Tests for China A-share symbol parsing."""

import unittest

from tradingagents.dataflows.a_share_symbols import (
    is_a_share_symbol,
    parse_yahoo_style_symbol,
    to_em_symbol,
)


class AShareSymbolTests(unittest.TestCase):
    def test_parse_yahoo_shanghai(self):
        self.assertEqual(parse_yahoo_style_symbol("600519.SS"), ("600519", "SH"))
        self.assertEqual(parse_yahoo_style_symbol(" 600519.ss "), ("600519", "SH"))

    def test_parse_yahoo_shenzhen(self):
        self.assertEqual(parse_yahoo_style_symbol("000001.SZ"), ("000001", "SZ"))

    def test_infer_exchange_without_suffix(self):
        self.assertEqual(parse_yahoo_style_symbol("600519"), ("600519", None))
        self.assertEqual(parse_yahoo_style_symbol("000001"), ("000001", None))

    def test_is_a_share(self):
        self.assertTrue(is_a_share_symbol("600519.SS"))
        self.assertTrue(is_a_share_symbol("600519"))
        self.assertTrue(is_a_share_symbol("000001.SZ"))
        self.assertTrue(is_a_share_symbol("300750"))
        self.assertFalse(is_a_share_symbol("NVDA"))
        self.assertFalse(is_a_share_symbol(""))

    def test_to_em_symbol(self):
        self.assertEqual(to_em_symbol("600519.SS"), "SH600519")
        self.assertEqual(to_em_symbol("000001.SZ"), "SZ000001")


if __name__ == "__main__":
    unittest.main()
