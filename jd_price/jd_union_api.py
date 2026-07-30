"""JD Union Open Platform client (optional, requires App Key / Secret)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

import requests

ROUTER_URL = "https://api.jd.com/routerjson"


def _md5_sign(params: dict[str, str], app_secret: str) -> str:
    ordered = sorted(params.items())
    raw = app_secret + "".join(f"{k}{v}" for k, v in ordered) + app_secret
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


def _call_router(
    method: str,
    param_json: dict[str, Any],
    *,
    app_key: str,
    app_secret: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    param_str = json.dumps(param_json, ensure_ascii=False, separators=(",", ":"))
    sys_params: dict[str, str] = {
        "method": method,
        "app_key": app_key,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "format": "json",
        "v": "1.0",
        "sign_method": "md5",
        "param_json": param_str,
    }
    if access_token:
        sys_params["access_token"] = access_token
    sys_params["sign"] = _md5_sign(sys_params, app_secret)

    resp = requests.post(ROUTER_URL, data=sys_params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    err = payload.get("error_response")
    if err:
        raise RuntimeError(
            f"JD API error {err.get('code')}: {err.get('zh_desc') or err}"
        )
    return payload


def fetch_prices_union(
    sku_ids: list[str],
    *,
    delay_sec: float = 0.5,
) -> list[dict[str, Any]]:
    """Fetch goods info via jd.union.open.goods.query (needs Union account)."""
    app_key = os.environ.get("JD_APP_KEY", "").strip()
    app_secret = os.environ.get("JD_APP_SECRET", "").strip()
    if not app_key or not app_secret:
        raise RuntimeError(
            "请设置环境变量 JD_APP_KEY 与 JD_APP_SECRET（京东联盟/开放平台）"
        )
    access_token = os.environ.get("JD_ACCESS_TOKEN", "").strip() or None

    rows: list[dict[str, Any]] = []
    # Union API accepts batch skuIds in param; keep batches small
    batch_size = 20
    for i in range(0, len(sku_ids), batch_size):
        batch = sku_ids[i : i + batch_size]
        param = {
            "goodsReqDTO": {
                "skuIds": [int(s) for s in batch],
                "fields": "skuId,skuName,price,lowestPrice,purchasePrice",
            }
        }
        data = _call_router(
            "jd.union.open.goods.query",
            param,
            app_key=app_key,
            app_secret=app_secret,
            access_token=access_token,
        )
        key = "jd_union_open_goods_query_responce"
        inner = data.get(key) or data.get("jd_union_open_goods_query_response") or {}
        result_str = inner.get("result") or inner.get("queryResult")
        if isinstance(result_str, str):
            result = json.loads(result_str)
        else:
            result = result_str or {}

        goods_list = result.get("data") or result.get("goodsList") or []
        for g in goods_list:
            sku = str(g.get("skuId", ""))
            price_info = g.get("priceInfo") or g
            rows.append(
                {
                    "sku": sku,
                    "price": price_info.get("price") or g.get("price"),
                    "market_price": price_info.get("lowestPrice"),
                    "original_price": None,
                    "title": g.get("skuName") or g.get("productName"),
                    "source": "jd.union.open.goods.query",
                    "raw": g,
                }
            )
        if delay_sec > 0 and i + batch_size < len(sku_ids):
            time.sleep(delay_sec)
    return rows
