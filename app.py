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

    df["fruits"] = df["Q10"]
    df["driedfruit"] = df["Q11"]
    df["fruitjuice"] = df["Q12"]
    df["vegrlg"] = df["Q149"]
    df["vegother"] = df["Q146"]
    df["TomSauc"] = df["Q1"]
    df["TomJuice"] = df["Q150"]
    df["plainbrd"] = df["Q24"]
    df["BkdBrd"] = df["Q165_0001"]
    df["CRPast"] = df["Q23"]
    df["GrnsOtr"] = df["Q148"]
    df["Legumess"] = df["Q161_0001"]
    df["Corn"] = df["Q162_0001"]
    df["PotatoNF"] = df["Q163"]
    df["PotatoFr"] = df["Q164"]
    df["LeanMeat"] = df["Q27"]
    df["FatMeat"] = df["Q28"]
    df["FtyFish"] = df["Q29"]
    df["WhEgg"] = df["Q177"]
    df["EggWt"] = df["Q178"]
    df["milk"] = df["Q33"]
    df["FlvMilk"] = df["Q169"]
    df["Yogurt"] = df["Q170"]
    df["FlvYogurt"] = df["Q168"]
    df["cheese"] = df["Q171"]
    df["cotcheese"] = df["q35"]
    df["vegoil"] = df["Q261"]
    df["nutbtr"] = df["Q262"]
    df["CocOilBt"] = df["Q263"]
    df["Butter"] = df["Q264"]
    df["lard"] = df["Q265"]
    df["SrCrm"] = df["Q266"]
    df["CrmChs"] = df["Q267"]
    df["Cream"] = df["Q268"]
    df["Mayo"] = df["Q269"]
    df["Mrgrne"] = df["Q270"]
    df["HlfHlf"] = df["Q271"]
    df["olives"] = df["Q160_0001"]
    df["nuts"] = df["Q158_0001"]
    df["avocado"] = df["Q134"]
    df["ChocCndy"] = df["Q42"]
    df["NonChcCndy"] = df["Q61"]
    df["IceCrm"] = df["Q62"]
    df["FroYo"] = df["Q63"]
    df["BkdGd"] = df["Q43"]
    df["SwtBvg"] = df["Q60"]
    df["SwtTCfee"] = df["Q278"]
    df["OtrSwtBvg"] = df["Q280"]
    df["NrgDrnk"] = df["Q279"]
    df["coconutwater"] = df["Q276"]
    df["slddressing"] = df["Q257"]
    df["nrgbar"] = df["Q125"]
    df["probar"] = df["Q281"]
    df["chodrnk"] = df["Q282"]
    df["gel"] = df["Q285"]
    df["prodrnk"] = df["Q284"]
    df["zerocaldrnk"] = df["Q273"]
    df["unSwtTCfee"] = df["Q272"]
    df["water"] = df["Q52"]
    df["beer"] = df["Q289"]
    df["spirits"] = df["Q290"]
    df["mixed"] = df["Q291"]
    df["wine"] = df["Q292"]

    return df

if uploaded_file is not None:
    df = read_uploaded_file(uploaded_file)
    df = normalize_qualtrics_columns(df)

    df = process_servings(df)
    df = create_food_variables(df)

    st.write("Preview of uploaded data:")
    st.dataframe(df.head())






