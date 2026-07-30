"""BaoStock session helper with automatic re-login."""

from __future__ import annotations

from contextlib import contextmanager

import baostock as bs


@contextmanager
def baostock_session():
  lg = bs.login()
  if lg.error_code != "0":
    raise RuntimeError(f"baostock login failed: {lg.error_msg}")
  try:
    yield
  finally:
    bs.logout()


def ensure_login() -> None:
  lg = bs.login()
  if lg.error_code != "0":
    raise RuntimeError(f"baostock login failed: {lg.error_msg}")
