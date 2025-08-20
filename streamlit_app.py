import re
from datetime import datetime
from io import StringIO

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Winners TXT → CSV", page_icon="📄", layout="centered")
st.title("📄 Recent Winners TXT → CSV")

st.markdown(
    "Paste your raw winners text **or** upload a .txt file. "
    "The converter will pull the **last 5-digit** token on each line as the result, "
    "parse common date formats, de-dupe, and sort **oldest → newest**."
)

with st.expander("Options", expanded=True):
    keep_keyword = st.text_input(
        "Only keep lines containing this word/phrase (optional)",
        value="", placeholder="e.g., Midday"
    )

def parse_date_any(s: str):
    s = (s or "").strip().replace("–", "-").replace("—", "-")
    # ISO yyyy-mm-dd
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", s)
    if m:
        y, mo, d = map(int, m.groups())
        try: return f"{y:04d}-{mo:02d}-{d:02d}"
        except: pass
    # mm/dd/yyyy
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", s)
    if m:
        mo, d, y = map(int, m.groups())
        try: return f"{y:04d}-{mo:02d}-{d:02d}"
        except: pass
    # textual (Mon, Aug 18, 2025 / Aug 18, 2025)
    for fmt in ("%a, %b %d, %Y", "%A, %b %d, %Y", "%a, %B %d, %Y", "%A, %B %d, %Y",
                "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except:
            pass
    return None

def convert_text(txt: str, keyword: str | None = None) -> pd.DataFrame:
    rows = []
    if not txt:
        return pd.DataFrame(columns=["Date", "Result"])
    lines = txt.splitlines()
    for raw in lines:
        line = (raw or "").strip()
        if not line:
            continue
        if keyword and keyword.lower() not in line.lower():
            continue
        # last 5-digit token anywhere in the line
        matches = list(re.finditer(r"(?<!\d)(\d{5})(?!\d)", line))
        if not matches:
            continue
        result = matches[-1].group(1)
        before = line[:matches[-1].start()].strip()
        date_str = parse_date_any(before) or parse_date_any(line) or before
        rows.append({"Date": date_str, "Result": result})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # normalize, de-dupe, sort
    df["Result"] = df["Result"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(5)
    df = df.drop_duplicates(subset=["Date", "Result"], keep="last")
    try:
        df["_d"] = pd.to_datetime(df["Date"], errors="raise")
        df = df.sort_values("_d").drop(columns=["_d"]).reset_index(drop=True)
    except:
        df = df.reset_index(drop=True)
    return df

# Inputs
uploaded = st.file_uploader("Upload .txt file", type=["txt"], help="Raw winners text file")
text_input = st.text_area("…or paste text here", height=200, placeholder="Mon, Aug 18, 2025    89803")

if st.button("Convert", type="primary", use_container_width=True):
    raw = ""
    if uploaded is not None:
        raw = uploaded.getvalue().decode("utf-8", errors="ignore")
    elif text_input.strip():
        raw = text_input
    else:
        st.warning("Please upload a .txt or paste text, then click Convert.")
        st.stop()

    df = convert_text(raw, keep_keyword.strip() or None)

    if df.empty:
        st.error("No valid rows found. Tip: ensure each line ends with (or contains) a 5-digit result.")
        st.stop()

    st.success(f"Parsed {len(df)} rows.")
    st.dataframe(df.head(20), use_container_width=True)
    st.caption("Preview of first 20 rows (sorted oldest→newest)")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    default_name = f"DC5_Recent_Winners_converted.csv"
    st.download_button("⬇️ Download CSV", data=csv_bytes, file_name=default_name, mime="text/csv")
else:
    st.info("Upload a .txt or paste text, then click **Convert**.")
