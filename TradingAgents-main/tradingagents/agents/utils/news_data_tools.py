from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.a_share_news import (
    get_a_share_macro_news_yfinance,
    get_a_share_company_social_digest_yfinance,
)


@tool
def get_a_share_macro_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Days to look back"] = 7,
    limit: Annotated[int, "Max articles"] = 12,
) -> str:
    """
    A-share / China market macro and policy-oriented news digest (Chinese search queries via yfinance).
    Use for CSRC, monetary policy, northbound flows, index/policy headlines relevant to A-shares.
    """
    return get_a_share_macro_news_yfinance(curr_date, look_back_days, limit)


@tool
def get_a_share_company_sentiment(
    ticker: Annotated[str, "Exchange-qualified ticker e.g. 600519.SS"],
    start_date: Annotated[str, "Start yyyy-mm-dd"],
    end_date: Annotated[str, "End yyyy-mm-dd"],
    limit: Annotated[int, "Max items"] = 15,
) -> str:
    """
    Company-level A-share discussion and media digest (Chinese queries: name, code, earnings, major portals).
    Supplement to get_news; not real-time forum order flow, but topic and sentiment clues.
    """
    return get_a_share_company_social_digest_yfinance(ticker, start_date, end_date, limit)


@tool
def get_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve news data for a given ticker symbol.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted string containing news data
    """
    return route_to_vendor("get_news", ticker, start_date, end_date)

@tool
def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    """
    Retrieve global news data.
    Uses the configured news_data vendor.
    Args:
        curr_date (str): Current date in yyyy-mm-dd format
        look_back_days (int): Number of days to look back (default 7)
        limit (int): Maximum number of articles to return (default 5)
    Returns:
        str: A formatted string containing global news data
    """
    return route_to_vendor("get_global_news", curr_date, look_back_days, limit)

@tool
def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve insider transaction information about a company.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A report of insider transaction data
    """
    return route_to_vendor("get_insider_transactions", ticker)
