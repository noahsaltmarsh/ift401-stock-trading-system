from datetime import datetime, time, date

from app.services.market_time import MarketSettings, is_market_open


def test_open_during_weekday_hours():
    settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0))
    now = datetime(2026, 2, 6, 10, 0)  # Friday
    assert is_market_open(now, settings) is True


def test_closed_outside_hours():
    settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0))
    now = datetime(2026, 2, 6, 8, 0)  # Friday before open
    assert is_market_open(now, settings) is False


def test_closed_on_weekend():
    settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0))
    now = datetime(2026, 2, 7, 10, 0)  # Saturday
    assert is_market_open(now, settings) is False


def test_closed_on_holiday():
    holiday = date(2026, 2, 6)
    settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0), holidays={holiday})
    now = datetime(2026, 2, 6, 10, 0)  # Friday but holiday
    assert is_market_open(now, settings) is False
