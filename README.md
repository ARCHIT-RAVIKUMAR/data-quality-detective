# Live Data Quality Detective

A Python script that gets user data from a public API, checks it for data quality problems with pandas, cleans it, and writes a report.

Data source: https://dummyjson.com/users?limit=0 (208 records, 52 columns after flattening)

## How to run
```
pip install -r requirements.txt
python detective.py
```
It writes `original_dataset.csv`, `cleaned_dataset.csv` and `quality_report.md`.

## Files
- `detective.py` - the script
- `quality_report.md` - the report
- `original_dataset.csv` - data as downloaded
- `cleaned_dataset.csv` - data after cleaning
- `OBSTACLE_LOG.md` - problems I ran into and how I fixed them

## What it checks
1. Missing values, including empty strings
2. Duplicate rows and repeated values in columns that should be unique
3. Suspicious values (age, height, weight ranges, age vs birthDate)
4. Formatting (date format, invalid emails, extra spaces in names)

## Problems found in the real data
- `maidenName` is empty for 148 users
- `birthDate` is not in a consistent YYYY-MM-DD format for 179 users
- `crypto.wallet` has the same value for every user

## API errors
The request has a timeout and retries 3 times. The response must be a non-empty list. If the API still fails it uses the last saved copy (`raw_cache.json`), and if there is none it exits with `sys.exit(1)` and a message.
