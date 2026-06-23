# Crypto Fixtures

Generate or refresh these shared CSV files before running the crypto notebooks:

```bash
python3 scripts/python/download-crypto-fixtures.py --source binance-monthly-archive
```

The notebooks read `fixtures/crypto/crypto_daily_close.csv` from the repository
root and do not download data themselves. This keeps the teaching examples
reproducible after the fixture has been refreshed. The default fixture window
is daily BTC, ETH, and BNB data for the first half of 2024.
