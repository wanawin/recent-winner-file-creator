import pandas as pd, re
from datetime import datetime

SRC_TXT  = "new_winners.txt"     # your latest reverse-ordered text like “Mon, Aug 18, 2025    89803”
REPO_CSV = "DC5_Midday_Full_Cleaned_Expanded.csv"  # winners file used by the app

# Load existing (or start empty)
try:
    df = pd.read_csv(REPO_CSV)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Date","Result"])

# Parse the new text
rows = []
with open(SRC_TXT, encoding="utf-8") as f:
    for line in f:
        m = re.search(r"(\d{5})\s*$", line.strip())
        if not m: 
            continue
        result = m.group(1)
        date_part = line[:m.start()].strip()
        dt = None
        for fmt in ("%a, %b %d, %Y", "%A, %b %d, %Y", "%a, %B %d, %Y", "%A, %B %d, %Y"):
            try:
                dt = datetime.strptime(date_part, fmt).date().isoformat()
                break
            except: 
                pass
        rows.append({"Date": dt or date_part, "Result": result})

new = pd.DataFrame(rows)

# Normalize, merge, dedupe, sort (oldest→newest)
for d in (df, new):
    if not d.empty:
        d["Result"] = d["Result"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(5)

df = pd.concat([df, new], ignore_index=True)
df = df.drop_duplicates(subset=["Date","Result"], keep="last")
try:
    df["_d"] = pd.to_datetime(df["Date"], errors="raise")
    df = df.sort_values("_d").drop(columns=["_d"])
except:
    df = df.reset_index(drop=True)

df.to_csv(REPO_CSV, index=False)
print(f"Updated {REPO_CSV}: {len(df)} rows")
