"""Tests for auto vendor expansion (A-share vs global tickers)."""

import unittest

from tradingagents.dataflows import interface


class AutoVendorRoutingTests(unittest.TestCase):
    def test_expand_auto_a_share_prefers_akshare(self):
        s = interface._expand_auto_vendor("get_stock_data", ("600519.SS",))
        self.assertTrue(s.startswith("akshare"))

    def test_expand_auto_us_stock_prefers_yfinance(self):
        s = interface._expand_auto_vendor("get_stock_data", ("NVDA",))
        self.assertTrue(s.startswith("yfinance"))

    def test_normalize_vendor_auto(self):
        out = interface._normalize_vendor_string("auto", "get_fundamentals", ("000001.SZ",))
        self.assertIn("akshare", out)


if __name__ == "__main__":
    unittest.main()
