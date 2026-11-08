# Data Quality Report

Source: https://dummyjson.com/users?limit=0
Rows before: 208, rows after: 208
Columns: 52

## Problems found

### Missing values (NaN or empty text)
- maidenName: 148 (71.2%)

### Duplicates
- Duplicate rows: 0
- crypto.wallet: 207 repeated values

### Suspicious values
- Ages outside 0-120: 0
- Heights outside 100-250 cm: 0
- Weights outside 30-300 kg: 0
- Age not matching birthDate (more than 1 year off): 0

### Formatting
- birthDate not in YYYY-MM-DD format: 179
- Invalid emails: 0
- firstName with extra spaces: 0

## Basic statistics (original data)

          age  height  weight
count  208.00  208.00  208.00
mean    33.14  175.72   75.04
std      5.54   14.12   14.09
min     23.00  150.25   50.10
25%     29.00  164.19   62.55
50%     32.00  177.43   75.98
75%     36.00  186.96   86.99
max     46.00  199.81   99.54


## What cleaning changed

- Removed 0 duplicate rows
- Replaced 148 empty values in maidenName with 'not provided'
- Changed 179 birthDate values to YYYY-MM-DD
- age: 0 impossible values set to the median and flagged
- height: 0 impossible values set to the median and flagged
- weight: 0 impossible values set to the median and flagged
- Flagged 0 rows with invalid emails
- Flagged 208 rows that share a crypto.wallet value
- Rows marked suspicious: 0