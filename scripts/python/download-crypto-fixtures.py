#!/usr/bin/env python3
"""Download daily crypto OHLCV fixtures from public crypto data APIs."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BINANCE_ARCHIVE_URL = "https://data.binance.vision/data/spot/daily/klines"
BINANCE_MONTHLY_ARCHIVE_URL = "https://data.binance.vision/data/spot/monthly/klines"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}
DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
]
DEFAULT_YAHOO_SYMBOLS = [
    "BTC-USD",
    "ETH-USD",
    "BNB-USD",
    "SOL-USD",
    "XRP-USD",
    "ADA-USD",
    "DOGE-USD",
    "LINK-USD",
    "LTC-USD",
    "BCH-USD",
]


def parse_utc_date(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def utc_date_from_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()


def iter_utc_dates(start: str, end: str):
    current = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    while current <= end_date:
        yield current.isoformat()
        current = current.fromordinal(current.toordinal() + 1)


def iter_utc_months(start: str, end: str):
    current = datetime.strptime(start, "%Y-%m-%d").date().replace(day=1)
    end_month = datetime.strptime(end, "%Y-%m-%d").date().replace(day=1)
    while current <= end_month:
        yield f"{current.year:04d}-{current.month:02d}"
        year = current.year + (current.month // 12)
        month = 1 if current.month == 12 else current.month + 1
        current = current.replace(year=year, month=month)


def fetch_klines(symbol: str, start_ms: int, end_ms: int, interval: str) -> list[list[object]]:
    rows: list[list[object]] = []
    next_start = start_ms

    while next_start < end_ms:
        query = urlencode(
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": next_start,
                "endTime": end_ms,
                "limit": 1000,
            }
        )
        request = Request(f"{BINANCE_KLINES_URL}?{query}", headers=REQUEST_HEADERS)
        with urlopen(request, timeout=30) as response:
            batch = json.loads(response.read().decode("utf-8"))

        if not batch:
            break

        rows.extend(batch)
        last_open_time = int(batch[-1][0])
        next_start = last_open_time + 1

        if len(batch) < 1000:
            break

        time.sleep(0.2)

    return rows


def download_archive_bytes(url: str) -> bytes:
    try:
        result = subprocess.run(
            ["curl", "-fsSL", "--connect-timeout", "10", "--retry", "2", url],
            check=True,
            capture_output=True,
            timeout=60,
        )
        return result.stdout
    except (FileNotFoundError, subprocess.SubprocessError):
        request = Request(url, headers=REQUEST_HEADERS)
        with urlopen(request, timeout=30) as response:
            return response.read()


def fetch_binance_archive(symbol: str, start: str, end: str, interval: str) -> list[list[object]]:
    rows: list[list[object]] = []
    for date in iter_utc_dates(start, end):
        filename = f"{symbol}-{interval}-{date}.zip"
        url = f"{BINANCE_ARCHIVE_URL}/{symbol}/{interval}/{filename}"
        try:
            archive_bytes = download_archive_bytes(url)
        except subprocess.CalledProcessError as error:
            if error.returncode == 22:
                continue
            raise
        except HTTPError as error:
            if error.code == 404:
                continue
            raise

        with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
            csv_name = archive.namelist()[0]
            with archive.open(csv_name) as file:
                text_rows = csv.reader(line.decode("utf-8") for line in file)
                for row in text_rows:
                    if not row or row[0] == "open_time":
                        continue
                    rows.append([int(row[0]), row[1], row[2], row[3], row[4], row[5]])

        time.sleep(0.05)

    return rows


def fetch_binance_monthly_archive(
    symbol: str,
    start: str,
    end: str,
    interval: str,
) -> list[list[object]]:
    start_ms = parse_utc_date(start)
    end_ms = parse_utc_date(end)
    rows: list[list[object]] = []

    for month in iter_utc_months(start, end):
        filename = f"{symbol}-{interval}-{month}.zip"
        url = f"{BINANCE_MONTHLY_ARCHIVE_URL}/{symbol}/{interval}/{filename}"
        try:
            archive_bytes = download_archive_bytes(url)
        except subprocess.CalledProcessError as error:
            if error.returncode == 22:
                continue
            raise
        except HTTPError as error:
            if error.code == 404:
                continue
            raise

        with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
            csv_name = archive.namelist()[0]
            with archive.open(csv_name) as file:
                text_rows = csv.reader(line.decode("utf-8") for line in file)
                for row in text_rows:
                    if not row or row[0] == "open_time":
                        continue
                    open_time = int(row[0])
                    if start_ms <= open_time <= end_ms:
                        rows.append([open_time, row[1], row[2], row[3], row[4], row[5]])

        time.sleep(0.05)

    return rows


def fetch_yahoo(symbol: str, start_ms: int, end_ms: int, interval: str) -> list[list[object]]:
    period1 = start_ms // 1000
    period2 = end_ms // 1000
    query = urlencode({"period1": period1, "period2": period2, "interval": interval})
    request = Request(f"{YAHOO_CHART_URL.format(symbol=symbol)}?{query}", headers=REQUEST_HEADERS)
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as error:
            if error.code != 429 or attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
        except URLError:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"Unable to download {symbol}")

    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    rows: list[list[object]] = []

    for i, ts in enumerate(timestamps):
        values = [
            quote["open"][i],
            quote["high"][i],
            quote["low"][i],
            quote["close"][i],
            quote["volume"][i],
        ]
        if any(value is None for value in values):
            continue
        rows.append([int(ts) * 1000, *values])

    return rows


def write_long_ohlcv(path: Path, symbol_rows: dict[str, list[list[object]]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "symbol", "open", "high", "low", "close", "volume"])
        for symbol, rows in symbol_rows.items():
            for row in rows:
                writer.writerow([utc_date_from_ms(int(row[0])), symbol, *row[1:6]])


def write_close_matrix(path: Path, symbol_rows: dict[str, list[list[object]]]) -> None:
    dates = sorted({utc_date_from_ms(int(row[0])) for rows in symbol_rows.values() for row in rows})
    close_by_symbol = {
        symbol: {utc_date_from_ms(int(row[0])): row[4] for row in rows}
        for symbol, rows in symbol_rows.items()
    }

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", *symbol_rows.keys()])
        for date in dates:
            writer.writerow([date, *[close_by_symbol[symbol].get(date, "") for symbol in symbol_rows]])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="fixtures/crypto",
        help="Directory where fixture CSV files will be written.",
    )
    parser.add_argument(
        "--source",
        choices=["binance-monthly-archive", "binance-archive", "yahoo", "binance"],
        default="binance-monthly-archive",
        help="Public data source to use.",
    )
    parser.add_argument("--start", default="2024-01-01", help="UTC start date, YYYY-MM-DD.")
    parser.add_argument("--end", default="2024-06-30", help="UTC end date, YYYY-MM-DD.")
    parser.add_argument("--interval", default="1d", help="Daily candle interval, such as 1d.")
    parser.add_argument("--symbols", nargs="+", default=None, help="Symbols to download.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_ms = parse_utc_date(args.start)
    end_ms = parse_utc_date(args.end)
    symbol_rows: dict[str, list[list[object]]] = {}

    symbols = args.symbols
    if symbols is None:
        symbols = DEFAULT_YAHOO_SYMBOLS if args.source == "yahoo" else DEFAULT_SYMBOLS

    for symbol in symbols:
        print(f"Downloading {symbol} {args.interval} candles from {args.source}...")
        if args.source == "binance-monthly-archive":
            rows = fetch_binance_monthly_archive(symbol, args.start, args.end, args.interval)
        elif args.source == "binance-archive":
            rows = fetch_binance_archive(symbol, args.start, args.end, args.interval)
        elif args.source == "yahoo":
            rows = fetch_yahoo(symbol, start_ms, end_ms, args.interval)
        else:
            rows = fetch_klines(symbol, start_ms, end_ms, args.interval)
        if not rows:
            raise RuntimeError(f"No data returned for {symbol}")
        symbol_rows[symbol] = rows

    write_long_ohlcv(output_dir / "crypto_daily_ohlcv.csv", symbol_rows)
    write_close_matrix(output_dir / "crypto_daily_close.csv", symbol_rows)

    metadata = {
        "source": args.source,
        "url": (
            BINANCE_ARCHIVE_URL
            if args.source == "binance-archive"
            else BINANCE_MONTHLY_ARCHIVE_URL
            if args.source == "binance-monthly-archive"
            else YAHOO_CHART_URL
            if args.source == "yahoo"
            else BINANCE_KLINES_URL
        ),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "start": args.start,
        "end": args.end,
        "interval": args.interval,
        "symbols": list(symbol_rows.keys()),
        "rows_by_symbol": {symbol: len(rows) for symbol, rows in symbol_rows.items()},
    }
    (output_dir / "crypto_daily_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
