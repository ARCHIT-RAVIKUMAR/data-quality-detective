# Obstacle Log

**1. Nested JSON turned into 52 columns**
Each user has address, bank and company details inside it. `pd.json_normalize` flattened
it into columns like `address.city`. A few fields were lists, so I saved those as text so
the CSV export would work.

**2. My first checks said the data was perfect**
My first version used `isna()` and reported zero missing values. But when I looked at the
CSV, `maidenName` was empty for most users. They were empty strings, not NaN, so pandas
didn't count them. I changed the check to treat empty text as missing too (148 values).
Looking at the other columns also showed that `birthDate` has no zero-padding in some
rows and that every user has the same `crypto.wallet`.

**3. I tried adding fake bad data and then removed it**
Because the data looked clean, I first added a `--noise` option that inserted fake
errors to test my checks. It made the report confusing because it mixed made-up problems
with real ones, so I removed it and only report issues that are really in the API data.

**4. Handling API failure**
The request can fail, time out or return something unexpected. The script retries 3
times with a timeout and checks that the response is a non-empty list. If that fails it
uses the saved copy, and if there is no saved copy it prints a message and stops with
`sys.exit(1)` instead of crashing later.

**5. Deciding what to do with problem values**
I didn't want to delete rows just for an empty maidenName or a shared wallet. I replaced
empty text with "not provided", fixed the date format, and added flag columns
(`suspicious`, `duplicate_wallet`) so the changes can still be seen.
