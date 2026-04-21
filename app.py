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
            return pd.read_csv(file, skiprows=[1], dtype=str, keep_default_na=False, na_values=[])
        except Exception:
            file.seek(0)
            return pd.read_csv(file, skiprows=[1], encoding="latin1", dtype=str, keep_default_na=False, na_values=[])
    elif file.name.lower().endswith(".xlsx") or file.name.lower().endswith(".xls"):
        return pd.read_excel(file, skiprows=[1], dtype=str)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV, XLSX, or XLS file.")


def clean_missing_strings(df):
    df = df.copy()
    df = df.fillna("")
    return df


def ensure_columns(df, cols):
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            df[col] = ""
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
        return ""
    s = str(value)
    keep = re.sub(r"[^0-9.\-]", " ", s)
    parts = keep.split()
    if len(parts) == 0:
        return ""
    return parts[0]


def convert_food_frequency(value):
    if pd.isna(value):
        return 0
    v = str(value)

    if v == "PREFER NOT TO ANSWER":
        return 0
    if sas_index(v, "< ONE") > 0:
        return 0
    if sas_index(v, "LESS THAN ONE") > 0:
        return 0
    if sas_index_eq_1(v, "ONE"):
        return 1
    if sas_index_eq_1(v, "TWO"):
        return 2
    if sas_index_eq_1(v, "THREE"):
        return 3
    if sas_index_eq_1(v, "FOUR "):
        return 4
    if sas_index_eq_1(v, "FIVE"):
        return 5
    if sas_index_eq_1(v, "SIX "):
        return 6
    if sas_index_eq_1(v, "SEVEN "):
        return 7
    if sas_index_eq_1(v, "EIGHT "):
        return 8
    if sas_index_eq_1(v, "NINE "):
        return 9
    if sas_index(v, "TEN") > 0:
        return 10
    if sas_index(v, "ELEVEN") > 0:
        return 11
    if sas_index(v, "TWELVE") > 0:
        return 12
    if sas_index(v, "THIRTEEN") > 0:
        return 13
    if sas_index(v, "FOURTEEN") > 0:
        return 14
    if sas_index_eq_1(v, "FIFTEEN"):
        return 15
    if sas_index(v, "> FIFTEEN") > 0:
        return 16
    if sas_index(v, "SIXTEEN") > 0:
        return 16
    if sas_index(v, "SEVENTEEN") > 0:
        return 17
    if sas_index(v, "EIGHTEEN") > 0:
        return 18
    if sas_index(v, "NINETEEN") > 0:
        return 19
    if sas_index_eq_1(v, "TWENTY "):
        return 20
    if sas_index(v, "TWENTY-ONE") > 0:
        return 21
    if sas_index(v, "TWENTY-TWO") > 0:
        return 22
    if sas_index(v, "TWENTY-THREE") > 0:
        return 23
    if sas_index(v, "TWENTY-FOUR") > 0:
        return 24
    if sas_index(v, "TWENTY-FIVE") > 0:
        return 25
    if sas_index(v, "TWENTY-SIX") > 0:
        return 26
    if sas_index(v, "TWENTY-SEVEN") > 0:
        return 27
    if sas_index(v, "TWENTY-EIGHT") > 0:
        return 28
    if sas_index(v, "TWENTY-NINE") > 0:
        return 29
    if sas_index_eq_1(v, "THIRTY "):
        return 30
    if sas_index(v, "> THIRTY") > 0:
        return 31
    if sas_index(v, "THIRTY-ONE") > 0:
        return 31
    if sas_index(v, "THIRTY-TWO") > 0:
        return 32
    if sas_index(v, "THIRTY-THREE") > 0:
        return 33
    if sas_index(v, "THIRTY-FOUR") > 0:
        return 34
    if sas_index_eq_1(v, "THIRTY-FIVE"):
        return 35
    if sas_index(v, "> THIRTY-FIVE") > 0:
        return 36

    num = to_num(v)
    if pd.isna(num):
        return 0
    return num


def convert_hours_text(value):
    if pd.isna(value):
        return 0
    v = str(value)

    if v == "None":
        return 0
    if sas_index_eq_1(v, "HALF"):
        return 0.5
    if sas_index_eq_1(v, "ONE hour"):
        return 1
    if sas_index_eq_1(v, "ONE and a HALF"):
        return 1.5
    if sas_index_eq_1(v, "TWO and a HALF"):
        return 2.5
    if sas_index_eq_1(v, "TWO"):
        return 2
    if sas_index_eq_1(v, "THREE and a HALF"):
        return 3.5
    if sas_index_eq_1(v, "THREE hours"):
        return 3
    if sas_index_eq_1(v, "FOUR and a HALF"):
        return 4.5
    if sas_index_eq_1(v, "FOUR hours"):
        return 4
    if sas_index_eq_1(v, "FIVE and a HALF"):
        return 5.5
    if sas_index_eq_1(v, "FIVE hours"):
        return 5
    if sas_index_eq_1(v, "SIX and a HALF"):
        return 6.5
    if sas_index_eq_1(v, "SIX hours"):
        return 6
    if sas_index_eq_1(v, "SEVEN and a HALF"):
        return 7.5
    if sas_index_eq_1(v, "SEVEN hours"):
        return 7
    if sas_index_eq_1(v, "EIGHT and a HALF"):
        return 8.5
    if sas_index_eq_1(v, "EIGHT hours"):
        return 8
    if sas_index_eq_1(v, "NINE and a HALF"):
        return 9.5
    if sas_index_eq_1(v, "NINE hours"):
        return 9
    if sas_index_eq_1(v, "TEN and a HALF"):
        return 10.5
    if sas_index_eq_1(v, "TEN hours"):
        return 10
    if sas_index_eq_1(v, "ELEVEN and a HALF"):
        return 11.5
    if sas_index_eq_1(v, "ELEVEN hours"):
        return 11
    if sas_index_eq_1(v, "TWELVE and a HALF"):
        return 12.5
    if sas_index_eq_1(v, "TWELVE hours"):
        return 12
    if sas_index_eq_1(v, "THIRTEEN and a HALF"):
        return 13.5
    if sas_index_eq_1(v, "THIRTEEN hours"):
        return 13
    if sas_index_eq_1(v, "FOURTEEN and a HALF"):
        return 14.5
    if sas_index_eq_1(v, "FOURTEEN hours"):
        return 14
    if sas_index_eq_1(v, "FIFTEEN hours"):
        return 15

    num = to_num(v)
    if pd.isna(num):
        return 0
    return num


def build_nutrition1(df_raw):
    df = df_raw.copy()

    # --- SAS-style variable initialization ---
    all_cols_needed = [
        "milk","FlvMilk","Yogurt","FlvYogurt","cheese","cotcheese",
        "SwtBvg","SwtTCfee","OtrSwtBvg","NrgDrnk",
        "coconutwater","zerocaldrnk","unSwtTCfee","water",
        "beer","spirits","mixed","wine",
        "nrgbar","probar","prodrnk","gel"
    ]

    for col in all_cols_needed:
        if col not in df.columns:
            df[col] = np.nan

    # --- CLEAN + ENSURE COLUMNS ---
    required_cols = [
        "Q10","Q11","Q12","Q149","Q146","Q1","Q150","Q24","Q165_0001","Q23","Q148",
        "Q161_0001","Q162_0001","Q163","Q164","Q27","Q28","Q29","Q177","Q178","Q33",
        "Q169","Q170","Q168","Q171","Q35","Q261","Q262","Q263","Q264","Q265","Q266",
        "Q267","Q268","Q26","Q270","Q271","Q160_0001","Q158_0001","Q134","Q42",
        "Q61","Q62","Q63","Q43","Q60","Q278","Q279","Q280","Q276","Q257","Q125",
        "Q281","Q282","Q285","Q284","Q273","Q272","Q52","Q269","Q289","Q290","Q291","Q292",
        "Q64","Q65","Q286","Q179","Q156_0001","Q209","Q210","Q230","Q200","Q213","Q212",
        "Q215","Q219","Q224","Q225","Q70","Q218","Q221","Q223","Q152","Q153","Q154",
        "Q155","Q157","Q158","Q232","Q240","Q241","Q245","Q250","Q251","Q252",
        "Q253","Q254","Q165","Q166"
    ]

    df = clean_missing_strings(df)
    df = ensure_columns(df, required_cols)

    # --- FOOD FREQUENCY ---
    food_vars = [
        "Q10","Q11","Q12","Q149","Q146","Q1","Q150","Q24","Q165_0001","Q23","Q148",
        "Q161_0001","Q162_0001","Q163","Q164","Q27","Q28","Q29","Q177","Q178",
        "Q33","Q169","Q170","Q168","Q171","Q35","Q261","Q262","Q263","Q264",
        "Q265","Q266","Q267","Q268","Q26","Q270","Q271","Q160_0001","Q158_0001",
        "Q134","Q42","Q61","Q62","Q63","Q43","Q60","Q278","Q279","Q280","Q276",
        "Q257","Q125","Q281","Q282","Q285","Q284","Q273","Q272","Q52","Q269",
        "Q289","Q290","Q291","Q292"
    ]

    for col in food_vars:
        df[col] = df[col].apply(convert_food_frequency)

    # --- BASIC MAPPINGS ---
    df["fruits"] = pd.to_numeric(df["Q10"], errors="coerce").fillna(0)
    df["driedfruit"] = pd.to_numeric(df["Q11"], errors="coerce").fillna(0)
    df["fruitjuice"] = pd.to_numeric(df["Q12"], errors="coerce").fillna(0)

    # --- HEIGHT / WEIGHT ---
    df["Q209"] = df["Q209"].apply(first_numeric_from_string)
    df["Q210"] = df["Q210"].apply(first_numeric_from_string)

    df["Q209"] = pd.to_numeric(df["Q209"], errors="coerce")
    df["Q210"] = pd.to_numeric(df["Q210"], errors="coerce")

    df["weightkg"] = df["Q210"] / 2.2
    df["heightm"] = df["Q209"] * 0.0254
    df["bmi"] = df["weightkg"] / (df["heightm"] * df["heightm"])

    # --- SEX / AGE ---
    df["ismale"] = np.nan
    df.loc[df["Q230"] == "Female", "ismale"] = 0
    df.loc[df["Q230"] == "Male", "ismale"] = 1

    df["gender"] = df["Q230"]
    df["age"] = pd.to_numeric(df["Q200"], errors="coerce").fillna(0)

    # --- RUNNING ---
    df["runMETS"] = pd.to_numeric(df["Q219"], errors="coerce").fillna(0)
    df["runpace"] = pd.to_numeric(df["Q213"], errors="coerce").fillna(0)
    df["miles_wk"] = pd.to_numeric(df["Q218"], errors="coerce").fillna(0)
    df["hrsrunning"] = (df["miles_wk"] * df["runpace"]) / 60

    # --- WEIGHT LIFTING ---
    df["weightliftMETS"] = pd.to_numeric(df["Q224"], errors="coerce").fillna(0)
    df["weightlifthrs"] = df["Q221"].apply(convert_hours_text)

    # --- BIKE ---
    df["bikeMETS"] = pd.to_numeric(df["Q225"], errors="coerce").fillna(0)
    df["bikehrs"] = df["Q223"].apply(convert_hours_text)

    # --- ELLIPTICAL ---
    df["ellipticalMETS"] = pd.to_numeric(df["Q226"], errors="coerce").fillna(0)
    df["ellipticalhrs"] = df["Q222"].apply(convert_hours_text)

    # --- AQUAJOG ---
    df["aquajogMETS"] = pd.to_numeric(df["Q227"], errors="coerce").fillna(0)
    df["aquajoghrs"] = df["Q220"].apply(convert_hours_text)

    # --- BODY FAT / FFM ---
    df["BodyFat"] = 1.2 * df["bmi"] + 0.23 * df["age"] - 10.8 * df["ismale"] - 5.4
    df["FFM"] = df["weightkg"] - df["weightkg"] * df["BodyFat"] * 0.01

    # --- MILK / YOGURT / CHEESE TYPES ---
    df["milktype"] = 2
    df.loc[df["Q64"].str.contains("Non fat", na=False), "milktype"] = 1
    df.loc[df["Q64"].str.contains("Low fat", na=False), "milktype"] = 2
    df.loc[df["Q64"].str.contains("Regular", na=False), "milktype"] = 3
    df.loc[df["Q64"].str.contains("Non-dairy", na=False), "milktype"] = 4

    df["yogtype"] = 2
    df.loc[df["Q65"].str.contains("Non fat", na=False), "yogtype"] = 1
    df.loc[df["Q65"].str.contains("Low fat", na=False), "yogtype"] = 2
    df.loc[df["Q65"].str.contains("Regular", na=False), "yogtype"] = 3
    df.loc[df["Q65"].str.contains("Non-dairy", na=False), "yogtype"] = 4

    df["cheesetype"] = 1
    df.loc[df["Q179"].str.contains("Reduced", na=False), "cheesetype"] = 2
    df.loc[df["Q179"].str.contains("Non-dairy", na=False), "cheesetype"] = 3

    # --- VEGETABLES ---
    df["vegrlg"] = pd.to_numeric(df["Q149"], errors="coerce").fillna(0)
    df["vegother"] = pd.to_numeric(df["Q146"], errors="coerce").fillna(0)

    # --- DIET GROUPS ---
    df["fruit"] = df["fruits"] + df["driedfruit"] + df["fruitjuice"]

    df["NSVeg"] = df["vegrlg"] + df["vegother"]
    df["StarchVeg"] = df["Q162_0001"].fillna(0) + df["Q163"].fillna(0) + df["Q164"].fillna(0)
    df["VegAll"] = df["NSVeg"] + df["StarchVeg"]

    df["Grains"] = df["Q24"].fillna(0) + df["Q165_0001"].fillna(0) + df["Q23"].fillna(0) + df["Q148"].fillna(0)

    df["MtPltry"] = df["Q27"].fillna(0) + df["Q28"].fillna(0)
    df["eggs"] = df["Q177"].fillna(0) + df["Q178"].fillna(0)

    # --- DAIRY (NOW SAFE) ---
    df["dairy"] = (
        df["milk"] + df["FlvMilk"] + df["Yogurt"] +
        df["FlvYogurt"] + df["cheese"] + df["cotcheese"]
    )

    df["id"] = df["Q182"]

    return df



def to_excel_bytes(sheets_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, data in sheets_dict.items():
            data.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    output.seek(0)
    return output.getvalue()


if uploaded_file is not None:
    raw_df = read_uploaded_file(uploaded_file)
    raw_df = clean_missing_strings(raw_df)

    missing_hw = ("Q209" not in raw_df.columns) or ("Q210" not in raw_df.columns)
    if missing_hw:
        st.warning("Please enter height in inches as variable Q209 and weight in lbs as variable Q210. The app will still calculate everything else.")

    nutrition1 = build_nutrition1(raw_df)


# =========================
# CHUNK 2: nutrition2 + final outputs
# =========================

def build_nutrition2(nutrition1):
    df = nutrition1.copy()

    # -------------------------
    # TOTALS (mirrors SAS sums)
    # -------------------------
    # --- FRUIT ---
    df["fruitkcal"] = (df["fruits"]*60) + (df["driedfruit"]*60) + (df["fruitjuice"]*120/7)
    df["FruitCHO"] = (df["fruits"]*15) + (df["driedfruit"]*15) + (df["fruitjuice"]*30/7)
    df["FruitFiber"] = (df["fruits"]*2) + (df["driedfruit"]*2)
    df["fruit"] = (df["fruits"]/2) + (df["driedfruit"]/2) + (df["fruitjuice"]/7)

    # --- COCONUT WATER ---
    df["coconutwaterkcal"] = df["coconutwater"]*45/7
    df["coconutwatercho"] = df["coconutwater"]*10/7

    # --- NON-STARCHY VEGETABLES ---
    df["vegNSkcal"] = (df["vegrlg"]*25) + (df["vegother"]*37.5) + (df["TomSauc"]*50/7) + (df["TomJuice"]*50/7)
    df["vegNSCHO"] = (df["vegrlg"]*5) + (df["vegother"]*7.5) + (df["TomSauc"]*10/7) + (df["TomJuice"]*10/7)
    df["vegNSPRO"] = (df["vegrlg"]*2) + (df["vegother"]*3) + (df["TomSauc"]*4/7) + (df["TomJuice"]*4/7)
    df["vegNSFiber"] = (df["vegrlg"]*2.5) + (df["vegother"]*4) + (df["TomSauc"]*4/7) + (df["TomJuice"]*4/7)
    df["NSVeg"] = (df["vegrlg"]*0.5) + (df["vegother"]*1) + (df["TomSauc"]/7) + (df["TomJuice"]/7)

    # --- GRAINS ---
    df["Grainkcal"] = (df["plainbrd"]*80) + (df["BkdBrd"]*125) + (df["CRPast"]*80) + (df["GrnsOtr"]*125)
    df["GrainCHO"] = (df["plainbrd"]*15) + (df["BkdBrd"]*15) + (df["CRPast"]*15) + (df["GrnsOtr"]*15)
    df["GrainPRO"] = (df["plainbrd"]*3) + (df["BkdBrd"]*3) + (df["CRPast"]*3) + (df["GrnsOtr"]*3)
    df["GrainFAT"] = (df["BkdBrd"]*5) + (df["GrnsOtr"]*5)
    df["GrainFiber"] = (df["plainbrd"]*1) + (df["BkdBrd"]*1) + (df["CRPast"]*1) + (df["GrnsOtr"]*1)
    df["Grains"] = df["plainbrd"] + df["BkdBrd"] + df["CRPast"] + df["GrnsOtr"]

    # --- LEGUMES ---
    df["Legumeskcal"] = df["Legumess"]*100/7
    df["LegumesCHO"] = df["Legumess"]*15/7
    df["LegumesPRO"] = df["Legumess"]*6/7
    df["LegumesFiber"] = df["Legumess"]*5/7
    df["legumes"] = df["Legumess"]*0.14/2
    # --- CORN ---
    df["Cornkcal"] = df["Corn"]*77/7
    df["CornCHO"] = df["Corn"]*17/7
    df["CornPRO"] = df["Corn"]*3/7
    df["CornFiber"] = df["Corn"]*2/7

    # --- POTATO (NON-FRIED) ---
    df["PotatoNFkcal"] = df["PotatoNF"]*161/7
    df["PotatoNFCHO"] = df["PotatoNF"]*37/7
    df["PotatoNFPRO"] = df["PotatoNF"]*4/7
    df["PotatoNFFiber"] = df["PotatoNF"]*4/7

    # --- STARCHY VEGETABLES ---
    df["StarchVeg"] = df["Corn"] + df["PotatoNF"]

    # --- MEAT / POULTRY ---
    df["MtPltrykcal"] = (df["LeanMeat"]*55) + (df["FatMeat"]*100)
    df["MtPltryPRO"] = (df["LeanMeat"]*7) + (df["FatMeat"]*7)
    df["MtPltryFAT"] = (df["LeanMeat"]*3) + (df["FatMeat"]*8)
    df["MtPltry"] = df["LeanMeat"] + df["FatMeat"]

    # --- FATTY FISH ---
    df["FttyFishkcal"] = df["FtyFish"]*100
    df["FttyFishPRO"] = df["FtyFish"]*7
    df["FttyFishFAT"] = df["FtyFish"]*8
    df["FttyFish"] = df["FtyFish"]

    # --- EGGS ---
    df["eggskcal"] = (df["WhEgg"]*70) + (df["EggWt"]*17)
    df["eggsPRO"] = (df["WhEgg"]*6) + (df["EggWt"]*4)
    df["eggsFAT"] = (df["WhEgg"]*5)
    df["eggs"] = df["WhEgg"] + df["EggWt"]
    # --- DAIRY ---
    df["dairykcal"] = (df["milk"]*100) + (df["FlvMilk"]*150) + (df["Yogurt"]*100) + (df["FlvYogurt"]*150) + (df["cheese"]*110) + (df["cotcheese"]*90)
    df["dairyCHO"] = (df["milk"]*12) + (df["FlvMilk"]*25) + (df["Yogurt"]*12) + (df["FlvYogurt"]*25) + (df["cotcheese"]*6)
    df["dairyPRO"] = (df["milk"]*8) + (df["FlvMilk"]*8) + (df["Yogurt"]*8) + (df["FlvYogurt"]*8) + (df["cheese"]*7) + (df["cotcheese"]*11)
    df["dairyFAT"] = (df["milk"]*5) + (df["FlvMilk"]*5) + (df["Yogurt"]*5) + (df["FlvYogurt"]*5) + (df["cheese"]*9) + (df["cotcheese"]*2)
    df["dairy"] = df["milk"] + df["FlvMilk"] + df["Yogurt"] + df["FlvYogurt"] + df["cheese"] + df["cotcheese"]

    # --- FLUIDS ---
    df["fluidskcal"] = (df["water"]*0) + (df["SwtBvg"]*150) + (df["SwtTCfee"]*120) + (df["OtrSwtBvg"]*150) + (df["NrgDrnk"]*120)
    df["fluidsCHO"] = (df["SwtBvg"]*40) + (df["SwtTCfee"]*30) + (df["OtrSwtBvg"]*40) + (df["NrgDrnk"]*30)
    df["fluids"] = df["water"] + df["SwtBvg"] + df["SwtTCfee"] + df["OtrSwtBvg"] + df["NrgDrnk"]

    # --- TOTAL ENERGY & MACROS ---
    df["kcaltotal"] = (
        df["fruitkcal"] + df["coconutwaterkcal"] + df["vegNSkcal"] + df["Grainkcal"] +
        df["Legumeskcal"] + df["Cornkcal"] + df["PotatoNFkcal"] +
        df["MtPltrykcal"] + df["FttyFishkcal"] + df["eggskcal"] +
        df["dairykcal"] + df["fluidskcal"]
    )

    df["cho"] = (
        df["FruitCHO"] + df["coconutwatercho"] + df["vegNSCHO"] + df["GrainCHO"] +
        df["LegumesCHO"] + df["CornCHO"] + df["PotatoNFCHO"] +
        df["dairyCHO"] + df["fluidsCHO"]
    )

    df["pro"] = (
        df["vegNSPRO"] + df["GrainPRO"] + df["LegumesPRO"] + df["CornPRO"] +
        df["PotatoNFPRO"] + df["MtPltryPRO"] + df["FttyFishPRO"] +
        df["eggsPRO"] + df["dairyPRO"]
    )

    df["fat"] = (
        df["GrainFAT"] + df["MtPltryFAT"] + df["FttyFishFAT"] +
        df["eggsFAT"] + df["dairyFAT"]
    )

    df["fiber"] = (
        df["FruitFiber"] + df["vegNSFiber"] + df["GrainFiber"] +
        df["LegumesFiber"] + df["CornFiber"] + df["PotatoNFFiber"]
    )

    df["chokg"] = df["cho"] / df["weightkg"]
    df["prokg"] = df["pro"] / df["weightkg"]
    df["fatkg"] = df["fat"] / df["weightkg"]

    df["fiber"] = (
        df["FruitFiber"] + df["vegNSFiber"] + df["GrainFiber"] +
        df["LegumesFiber"] + df["CornFiber"] + df["PotatoNFFiber"]
    )

    df["chokg"] = df["cho"] / df["weightkg"]
    df["prokg"] = df["pro"] / df["weightkg"]
    df["fatkg"] = df["fat"] / df["weightkg"]

    met_cols = [
        "run_MET_min",
        "lift_MET_min",
        "bike_MET_min",
        "elliptical_MET_min",
        "aquajog_MET_min"
    ]

    df["EEE"] = df[[c for c in met_cols if c in df.columns]].sum(axis=1) / 60

    df["EI"] = df["kcaltotal"]
    df.loc[df["EI"] == 0, "EI"] = np.nan

    df["EI_kg"] = df["EI"] / df["weightkg"]

    df["EA"] = (df["kcaltotal"] - df["EEE"]) / df["FFM"]
    df.loc[df["kcaltotal"] == 0, "EA"] = np.nan

    df["LowEA_clinical"] = np.where(df["EA"] < 30, 1, 0)
    df["LowEA_subclinical"] = np.where((df["EA"] >= 30) & (df["EA"] < 45), 1, 0)

    df["barswk"] = df["nrgbar"]
    df["probarswk"] = df["probar"]
    df["prodrnkwk"] = df["prodrnk"]
    df["gelchewwk"] = df["gel"]

    df["chodrnk"] = df["chodrnk"] * 8 / 7
    df["caffdrnk"] = df["NrgDrnk"] * 8 / 7

    df["id"] = df["Q182"]

    return df

# =========================
# APPLY CHUNK 2
# =========================

if uploaded_file is not None:
    raw_df = read_uploaded_file(uploaded_file)
    raw_df = clean_missing_strings(raw_df)

    missing_hw = ("Q209" not in raw_df.columns) or ("Q210" not in raw_df.columns)
    if missing_hw:
        st.warning("Please enter height in inches as variable Q209 and weight in lbs as variable Q210.")

    nutrition1 = build_nutrition1(raw_df)
    nutrition2 = build_nutrition2(nutrition1)

    keep_cols = [
    "id",
    "age",
    "gender",
    "isMale",
    "weightkg",
    "heightm",
    "BMI",
    "FFM",
    "EEE",
    "EI",
    "EI_kg",
    "EA",
    "LowEA_clinical",
    "LowEA_subclinical",
    "miles_wk",
    "fruit",
    "NSVeg",
    "StarchVeg",
    "VegAll",
    "legumes",
    "Grains",
    "Profoods",
    "MtPltry",
    "FttyFish",
    "eggs",
    "dairy",
    "fluids",
    "cho",
    "chokg",
    "pro",
    "prokg",
    "fat",
    "fatkg",
    "fiber",
    "mealsday",
    "snacksday",
    "fasting",
    "skip",
    "vegetarian",
    "vegan",
    "restrict",
    "restrictallergy",
    "housing",
    "foodprep",
    "foodinsecure",
    "barswk",
    "probarswk",
    "prodrnkwk",
    "gelchewwk",
    "chodrnk",
    "caffdrnk",
    "supp",
    "vitamin",
    "iron",
    "calcium",
    "vitaminD",
    "caffeine",
    "creatine",
    "prewrkout",
    "wtgainer",
    "wtlosssupp",
    "aasupp",
    "herbotsupp"
    ]

    keep_cols = [c for c in keep_cols if c in nutrition2.columns]

    redcapnutrition = nutrition2[keep_cols].copy()
    allnutrition = nutrition2.copy()

    st.success("Done")

    st.dataframe(redcapnutrition.head())

    st.download_button("Download redcapnutrition.csv", redcapnutrition.to_csv(index=False), "redcapnutrition.csv")
    st.download_button("Download allnutrition.csv", allnutrition.to_csv(index=False), "allnutrition.csv")
