import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

st.set_page_config(page_title="Nutrition Processing App", layout="wide")
st.title("Nutrition Processing App")

uploaded_file = st.file_uploader("Upload Qualtrics export", type=["csv", "xlsx", "xls"])


def read_uploaded_file(file):
    if file.name.lower().endswith(".csv"):
        try:
            return pd.read_csv(file, skiprows=[1], dtype=str)
        except Exception:
            file.seek(0)
            return pd.read_csv(file, skiprows=[1], encoding="latin1", dtype=str)
    elif file.name.lower().endswith(".xlsx") or file.name.lower().endswith(".xls"):
        return pd.read_excel(file, skiprows=[1], dtype=str)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV, XLSX, or XLS file.")


def clean_missing_strings(df):
    df = df.copy()
    return df


def ensure_columns(df, cols):
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            df[col] = ""
    return df

def normalize_qualtrics_columns(df):
    counts = {}
    new_cols = []

    for col in df.columns:
        if col not in counts:
            counts[col] = 0
            new_cols.append(col)
        else:
            counts[col] += 1
            new_cols.append(f"{col}_{counts[col]:04d}")

    df.columns = new_cols
    return df

def sas_index(value, substring):
    if pd.isna(value):
        return 0
    return 1 if substring in str(value) else 0


def sas_index_eq_1(value, substring):
    if pd.isna(value):
        return False
    return str(value).startswith(substring)


def to_num(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    if s == "":
        return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def first_numeric_from_string(value):
    if pd.isna(value):
        return np.nan
    s = str(value)
    keep = re.sub(r"[^0-9.\-]", " ", s)
    parts = keep.split()
    if len(parts) == 0:
        return np.nan
    return float(parts[0])


def process_servings(df):
    df = df.copy()

    vars_list = [
        "Q10","Q11","Q12","Q149","Q146","Q1","Q150","Q24","Q165_0001","Q23",
        "Q148","Q161_0001","Q162_0001","Q163","Q164","Q27","Q28","Q29","Q177",
        "Q178","Q33","Q169","Q170","Q168","Q171","q35","Q261","Q262","Q263",
        "Q264","Q265","Q266","Q267","Q268","Q26","Q270","Q271","Q160_0001",
        "Q158_0001","Q134","Q42","Q61","Q62","Q63","Q43","Q60","Q278","Q279",
        "Q280","Q276","Q257","Q125","Q281","Q282","Q285","Q284","Q273","Q272",
        "Q52","Q269","Q289","Q290","Q291","Q292"
    ]

    for col in vars_list:
        if col not in df.columns:
            continue

        s = df[col].astype(str).str.upper()

        # Start with NaN
        out = pd.Series(np.nan, index=df.index)

        # Apply rules (order matters, same as SAS)

        out[s == "PREFER NOT TO ANSWER"] = 0
        out[s.str.contains("< ONE", na=False)] = 0
        out[s.str.contains("LESS THAN ONE", na=False)] = 0

        out[s.str.startswith("ONE", na=False)] = 1
        out[s.str.startswith("TWO", na=False)] = 2
        out[s.str.startswith("THREE", na=False)] = 3
        out[s.str.startswith("FOUR ", na=False)] = 4
        out[s.str.startswith("FIVE", na=False)] = 5
        out[s.str.startswith("SIX ", na=False)] = 6
        out[s.str.startswith("SEVEN ", na=False)] = 7
        out[s.str.startswith("EIGHT ", na=False)] = 8
        out[s.str.startswith("NINE ", na=False)] = 9

        out[s.str.contains("TEN", na=False)] = 10
        out[s.str.contains("ELEVEN", na=False)] = 11
        out[s.str.contains("TWELVE", na=False)] = 12
        out[s.str.contains("THIRTEEN", na=False)] = 13
        out[s.str.contains("FOURTEEN", na=False)] = 14

        out[s.str.contains("> FIFTEEN", na=False)] = 16
        out[s.str.startswith("FIFTEEN", na=False)] = 15
        
        out[s.str.contains("SIXTEEN", na=False)] = 16
        out[s.str.contains("SEVENTEEN", na=False)] = 17
        out[s.str.contains("EIGHTEEN", na=False)] = 18
        out[s.str.contains("NINETEEN", na=False)] = 19

        out[s.str.startswith("TWENTY ", na=False)] = 20
        out[s.str.contains("TWENTY-ONE", na=False)] = 21
        out[s.str.contains("TWENTY-TWO", na=False)] = 22
        out[s.str.contains("TWENTY-THREE", na=False)] = 23
        out[s.str.contains("TWENTY-FOUR", na=False)] = 24
        out[s.str.contains("TWENTY-FIVE", na=False)] = 25
        out[s.str.contains("TWENTY-SIX", na=False)] = 26
        out[s.str.contains("TWENTY-SEVEN", na=False)] = 27
        out[s.str.contains("TWENTY-EIGHT", na=False)] = 28
        out[s.str.contains("TWENTY-NINE", na=False)] = 29

        out[s.str.startswith("THIRTY ", na=False)] = 30
        out[s.str.contains("> THIRTY", na=False)] = 31

        out[s.str.contains("THIRTY-ONE", na=False)] = 31
        out[s.str.contains("THIRTY-TWO", na=False)] = 32
        out[s.str.contains("THIRTY-THREE", na=False)] = 33
        out[s.str.contains("THIRTY-FOUR", na=False)] = 34

        out[s.str.startswith("THIRTY-FIVE", na=False)] = 35
        out[s.str.contains("> THIRTY-FIVE", na=False)] = 36

        # Missing → 0 (SAS rule)
        out = out.fillna(0)

        df[col] = out

    return df




def create_food_variables(df):
    df = df.copy()

    def safe_assign(new_col, old_col):
        if old_col in df.columns:
            df[new_col] = df[old_col]
        else:
            df[new_col] = 0

    safe_assign("fruits", "Q10")
    safe_assign("driedfruit", "Q11")
    safe_assign("fruitjuice", "Q12")
    safe_assign("vegrlg", "Q149")
    safe_assign("vegother", "Q146")
    safe_assign("TomSauc", "Q1")
    safe_assign("TomJuice", "Q150")
    safe_assign("plainbrd", "Q24")
    safe_assign("BkdBrd", "Q165_0001")
    safe_assign("CRPast", "Q23")
    safe_assign("GrnsOtr", "Q148")
    safe_assign("Legumess", "Q161_0001")
    safe_assign("Corn", "Q162_0001")
    safe_assign("PotatoNF", "Q163")
    safe_assign("PotatoFr", "Q164")
    safe_assign("LeanMeat", "Q27")
    safe_assign("FatMeat", "Q28")
    safe_assign("FtyFish", "Q29")
    safe_assign("WhEgg", "Q177")
    safe_assign("EggWt", "Q178")
    safe_assign("milk", "Q33")
    safe_assign("FlvMilk", "Q169")
    safe_assign("Yogurt", "Q170")
    safe_assign("FlvYogurt", "Q168")
    safe_assign("cheese", "Q171")
    safe_assign("cotcheese", "q35")
    safe_assign("vegoil", "Q261")
    safe_assign("nutbtr", "Q262")
    safe_assign("CocOilBt", "Q263")
    safe_assign("Butter", "Q264")
    safe_assign("lard", "Q265")
    safe_assign("SrCrm", "Q266")
    safe_assign("CrmChs", "Q267")
    safe_assign("Cream", "Q268")
    safe_assign("Mayo", "Q269")
    safe_assign("Mrgrne", "Q270")
    safe_assign("HlfHlf", "Q271")
    safe_assign("olives", "Q160_0001")
    safe_assign("nuts", "Q158_0001")
    safe_assign("avocado", "Q134")
    safe_assign("ChocCndy", "Q42")
    safe_assign("NonChcCndy", "Q61")
    safe_assign("IceCrm", "Q62")
    safe_assign("FroYo", "Q63")
    safe_assign("BkdGd", "Q43")
    safe_assign("SwtBvg", "Q60")
    safe_assign("SwtTCfee", "Q278")
    safe_assign("OtrSwtBvg", "Q280")
    safe_assign("NrgDrnk", "Q279")
    safe_assign("coconutwater", "Q276")
    safe_assign("slddressing", "Q257")
    safe_assign("nrgbar", "Q125")
    safe_assign("probar", "Q281")
    safe_assign("chodrnk", "Q282")
    safe_assign("gel", "Q285")
    safe_assign("prodrnk", "Q284")
    safe_assign("zerocaldrnk", "Q273")
    safe_assign("unSwtTCfee", "Q272")
    safe_assign("water", "Q52")
    safe_assign("beer", "Q289")
    safe_assign("spirits", "Q290")
    safe_assign("mixed", "Q291")
    safe_assign("wine", "Q292")

    return df

def process_dairy_types(df):
    df = df.copy()

    # ---- Milk ----
    s = df["Q64"].astype(str)

    df["milktype"] = np.nan
    df.loc[s.str.contains("Non fat", na=False), "milktype"] = 1
    df.loc[s.str.contains("Low fat", na=False), "milktype"] = 2
    df.loc[s.str.contains("Regular", na=False), "milktype"] = 3
    df.loc[s.str.contains("soy milk", na=False), "milktype"] = 4
    df.loc[s.str.contains("almond milk", na=False), "milktype"] = 5

    df["milktype"] = df["milktype"].fillna(2)

    # ---- Plain yogurt ----
    s = df["Q65"].astype(str)

    df["yogtype"] = np.nan
    df.loc[s.str.contains("Non fat yogurt", na=False), "yogtype"] = 1
    df.loc[s.str.contains("Low fat yogurt", na=False), "yogtype"] = 2
    df.loc[s.str.contains("Regular (full-fat) yogurt", na=False), "yogtype"] = 3
    df.loc[s.str.contains("Non-dairy yogurt", na=False), "yogtype"] = 4
    df.loc[s.str.contains("Greek yogurt (non fat", na=False), "yogtype"] = 5
    df.loc[s.str.contains("Greek yogurt (regular", na=False), "yogtype"] = 6

    df["yogtype"] = df["yogtype"].fillna(2)

    # ---- Flavored yogurt ----
    s = df["Q286"].astype(str)

    df["flvyogtype"] = np.nan
    df.loc[s.str.contains("Non fat yogurt", na=False), "flvyogtype"] = 1
    df.loc[s.str.contains("Low fat yogurt", na=False), "flvyogtype"] = 2
    df.loc[s.str.contains("Non-dairy yogurt", na=False), "flvyogtype"] = 3
    df.loc[s.str.contains("Greek yogurt", na=False), "flvyogtype"] = 4
    df.loc[s.str.contains("no sugar added", na=False), "flvyogtype"] = 5

    df["flvyogtype"] = df["flvyogtype"].fillna(2)

    # ---- Cheese ----
    s = df["Q179"].astype(str)

    df["cheesetype"] = np.nan
    df.loc[s.str.contains("Regular dairy cheese", na=False), "cheesetype"] = 1
    df.loc[s.str.contains("Reduced fat or light", na=False), "cheesetype"] = 2
    df.loc[s.str.contains("Non-dairy cheese", na=False), "cheesetype"] = 3

    df["cheesetype"] = df["cheesetype"].fillna(1)

    # ---- Salad dressing ----
    s = df.get("Q156_0001", "").astype(str)

    df["slddessingtype"] = np.nan
    df.loc[s.str.contains("Regular", na=False), "slddessingtype"] = 1
    df.loc[s.str.contains("Reduced-fat", na=False), "slddessingtype"] = 2
    df.loc[s.str.contains("Fat-free", na=False), "slddessingtype"] = 3

    df["slddessingtype"] = df["slddessingtype"].fillna(1)

    return df


if uploaded_file is not None:
    df = read_uploaded_file(uploaded_file)
    df = normalize_qualtrics_columns(df)

    df = process_servings(df)
    df = create_food_variables(df)
    df = process_dairy_types(df)

    st.write("Preview of uploaded data:")
    st.dataframe(df.head())




