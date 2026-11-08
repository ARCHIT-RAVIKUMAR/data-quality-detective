# Data quality checker
# Gets user data from the dummyjson API, checks it for problems with pandas,
# cleans it and writes a report.
#
# Run:  python detective.py

import json
import re
import sys
import time

import pandas as pd
import requests

URL = "https://dummyjson.com/users?limit=0"
CACHE_FILE = "raw_cache.json"
EMAIL_PATTERN = r"^[\w.+-]+@[\w-]+\.[\w.-]+$"
DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

# columns that should be different for every user
SHOULD_BE_UNIQUE = ["id", "email", "username", "phone", "ssn", "crypto.wallet"]


def get_data():
    """Download the users. Retry a few times, then fall back to the saved copy."""
    for attempt in range(1, 4):
        try:
            response = requests.get(URL, timeout=10)
            response.raise_for_status()
            users = response.json()["users"]
            if not isinstance(users, list) or len(users) == 0:
                raise ValueError("API did not return a non-empty list")
            with open(CACHE_FILE, "w") as f:
                json.dump(users, f)
            print(f"Got {len(users)} records from the API")
            return users
        except (requests.RequestException, ValueError, KeyError, TypeError) as err:
            print(f"Attempt {attempt} failed: {err}")
            time.sleep(2)

    try:
        with open(CACHE_FILE) as f:
            users = json.load(f)
        print("API is down, using the saved copy instead")
        return users
    except (FileNotFoundError, json.JSONDecodeError):
        print("No data from the API or the saved copy. Stopping.")
        sys.exit(1)


def blank_cells(df):
    """True where a cell is NaN or just an empty string."""
    empty_text = df.astype(str).apply(lambda col: col.str.strip()) == ""
    return df.isna() | empty_text


def find_problems(df):
    problems = {}

    # 1. missing values (empty strings count too, isna() alone would miss them)
    missing = blank_cells(df).sum()
    problems["missing"] = missing[missing > 0]

    # 2. duplicates
    problems["duplicate_rows"] = int(df.astype(str).duplicated().sum())
    problems["duplicate_values"] = {}
    for col in SHOULD_BE_UNIQUE:
        if col in df.columns:
            count = int(df[col].duplicated().sum())
            if count > 0:
                problems["duplicate_values"][col] = count

    # 3. values that look wrong
    problems["bad_age"] = int(((df["age"] < 0) | (df["age"] > 120)).sum())
    problems["bad_height"] = int(((df["height"] < 100) | (df["height"] > 250)).sum())
    problems["bad_weight"] = int(((df["weight"] < 30) | (df["weight"] > 300)).sum())
    birth = pd.to_datetime(df["birthDate"], errors="coerce")
    age_from_birth = (pd.Timestamp.today() - birth).dt.days // 365.25
    problems["age_mismatch"] = int((abs(age_from_birth - df["age"]) > 1).sum())

    # 4. formatting
    problems["date_format"] = int((~df["birthDate"].str.match(DATE_PATTERN)).sum())
    problems["bad_email"] = int((~df["email"].str.match(EMAIL_PATTERN, na=True)).sum())
    names = df["firstName"].dropna()
    problems["name_spaces"] = int((names != names.str.strip()).sum())

    return problems


def clean_data(df, problems):
    notes = []
    df = df.copy()

    before = len(df)
    df = df[~df.astype(str).duplicated()].reset_index(drop=True)
    notes.append(f"Removed {before - len(df)} duplicate rows")

    # empty text -> a clear label
    blanks = blank_cells(df)
    for col in problems["missing"].index:
        if df[col].dtype.kind in "iuf":
            continue
        n = int(blanks[col].sum())
        df.loc[blanks[col], col] = "not provided"
        notes.append(f"Replaced {n} empty values in {col} with 'not provided'")

    # make dates look the same: YYYY-MM-DD
    fixed = pd.to_datetime(df["birthDate"], errors="coerce").dt.strftime("%Y-%m-%d")
    changed = int((fixed != df["birthDate"]).sum())
    df["birthDate"] = fixed.fillna(df["birthDate"])
    notes.append(f"Changed {changed} birthDate values to YYYY-MM-DD")

    df["firstName"] = df["firstName"].str.strip()
    df["lastName"] = df["lastName"].str.strip()

    # flag rows that look wrong
    df["suspicious"] = False
    for col, low, high in [("age", 0, 120), ("height", 100, 250), ("weight", 30, 300)]:
        bad = (df[col] < low) | (df[col] > high)
        df.loc[bad, "suspicious"] = True
        df.loc[bad, col] = None
        df[col] = df[col].fillna(df[col].median())
        notes.append(f"{col}: {int(bad.sum())} impossible values set to the median and flagged")

    bad_email = ~df["email"].str.match(EMAIL_PATTERN, na=True)
    df.loc[bad_email, "suspicious"] = True
    notes.append(f"Flagged {int(bad_email.sum())} rows with invalid emails")

    # shared values: keep the rows but add a flag column
    df["duplicate_wallet"] = df["crypto.wallet"].duplicated(keep=False)
    notes.append(f"Flagged {int(df['duplicate_wallet'].sum())} rows that share a crypto.wallet value")

    return df, notes


def write_report(original, cleaned, problems, notes):
    lines = []
    lines.append("# Data Quality Report\n")
    lines.append(f"Source: {URL}")
    lines.append(f"Rows before: {len(original)}, rows after: {len(cleaned)}")
    lines.append(f"Columns: {original.shape[1]}\n")

    lines.append("## Problems found\n")
    lines.append("### Missing values (NaN or empty text)")
    if len(problems["missing"]) == 0:
        lines.append("- none")
    for col, count in problems["missing"].items():
        lines.append(f"- {col}: {count} ({count / len(original) * 100:.1f}%)")

    lines.append("\n### Duplicates")
    lines.append(f"- Duplicate rows: {problems['duplicate_rows']}")
    if not problems["duplicate_values"]:
        lines.append("- No repeated values in columns that should be unique")
    for col, count in problems["duplicate_values"].items():
        lines.append(f"- {col}: {count} repeated values")

    lines.append("\n### Suspicious values")
    lines.append(f"- Ages outside 0-120: {problems['bad_age']}")
    lines.append(f"- Heights outside 100-250 cm: {problems['bad_height']}")
    lines.append(f"- Weights outside 30-300 kg: {problems['bad_weight']}")
    lines.append(f"- Age not matching birthDate (more than 1 year off): {problems['age_mismatch']}")

    lines.append("\n### Formatting")
    lines.append(f"- birthDate not in YYYY-MM-DD format: {problems['date_format']}")
    lines.append(f"- Invalid emails: {problems['bad_email']}")
    lines.append(f"- firstName with extra spaces: {problems['name_spaces']}")

    lines.append("\n## Basic statistics (original data)\n")
    lines.append(original[["age", "height", "weight"]].describe().round(2).to_string())

    lines.append("\n\n## What cleaning changed\n")
    for note in notes:
        lines.append(f"- {note}")
    lines.append(f"- Rows marked suspicious: {int(cleaned['suspicious'].sum())}")

    with open("quality_report.md", "w") as f:
        f.write("\n".join(lines))


def main():
    users = get_data()
    df = pd.json_normalize(users)

    # lists and dicts can't go in a csv nicely, so store them as text
    for col in df.columns:
        df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)

    print(df.shape)
    print(df.dtypes)

    problems = find_problems(df)
    cleaned, notes = clean_data(df, problems)

    df.to_csv("original_dataset.csv", index=False)
    cleaned.to_csv("cleaned_dataset.csv", index=False)
    write_report(df, cleaned, problems, notes)
    print("Done. Check quality_report.md")


if __name__ == "__main__":
    main()
