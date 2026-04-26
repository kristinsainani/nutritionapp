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
    s = df.get("Q64", "").astype(str).str.lower()

    df["milktype"] = np.nan
    df.loc[s.str.contains("non fat", na=False), "milktype"] = 1
    df.loc[s.str.contains("low fat", na=False), "milktype"] = 2
    df.loc[s.str.contains("regular", na=False), "milktype"] = 3
    df.loc[s.str.contains("soy", na=False), "milktype"] = 4
    df.loc[s.str.contains("almond", na=False), "milktype"] = 5

    df["milktype"] = df["milktype"].fillna(2)

    # ---- Plain yogurt ----
    s = df.get("Q65", "").astype(str).str.lower()

    df["yogtype"] = np.nan
    df.loc[s.str.contains("non fat yogurt", na=False), "yogtype"] = 1
    df.loc[s.str.contains("low fat yogurt", na=False), "yogtype"] = 2
    df.loc[s.str.contains("regular", na=False) & s.str.contains("yogurt", na=False), "yogtype"] = 3
    df.loc[s.str.contains("non-dairy", na=False), "yogtype"] = 4
    df.loc[s.str.contains("greek", na=False) & s.str.contains("non fat", na=False), "yogtype"] = 5
    df.loc[s.str.contains("greek", na=False) & s.str.contains("regular", na=False), "yogtype"] = 6

    df["yogtype"] = df["yogtype"].fillna(2)

    # ---- Flavored yogurt ----
    s = df.get("Q286", "").astype(str).str.lower()

    df["flvyogtype"] = np.nan
    df.loc[s.str.contains("non fat", na=False), "flvyogtype"] = 1
    df.loc[s.str.contains("low fat", na=False), "flvyogtype"] = 2
    df.loc[s.str.contains("non-dairy", na=False), "flvyogtype"] = 3
    df.loc[s.str.contains("greek", na=False), "flvyogtype"] = 4
    df.loc[s.str.contains("no sugar", na=False) | s.str.contains("diet", na=False), "flvyogtype"] = 5

    df["flvyogtype"] = df["flvyogtype"].fillna(2)

    # ---- Cheese ----
    s = df.get("Q179", "").astype(str).str.lower()

    df["cheesetype"] = np.nan
    df.loc[s.str.contains("regular", na=False), "cheesetype"] = 1
    df.loc[s.str.contains("reduced", na=False) | s.str.contains("light", na=False), "cheesetype"] = 2
    df.loc[s.str.contains("non-dairy", na=False), "cheesetype"] = 3

    df["cheesetype"] = df["cheesetype"].fillna(1)

    # ---- Salad dressing ----
    s = df.get("Q156_0001", df.get("Q156", "")).astype(str).str.lower()

    df["slddessingtype"] = np.nan
    df.loc[s.str.contains("regular", na=False), "slddessingtype"] = 1
    df.loc[s.str.contains("reduced", na=False), "slddessingtype"] = 2
    df.loc[s.str.contains("fat-free", na=False) | s.str.contains("non fat", na=False), "slddessingtype"] = 3

    df["slddessingtype"] = df["slddessingtype"].fillna(1)

    return df

def process_body_metrics(df):
    df = df.copy()

    # ---- Extract numeric values (like SAS scan/compress) ----
    df["Q209_num"] = df["Q209"].apply(first_numeric_from_string)  # height
    df["Q210_num"] = df["Q210"].apply(first_numeric_from_string)  # weight

    # ---- Convert units ----
    df["weightkg"] = df["Q210_num"] / 2.2
    df["heightm"] = df["Q209_num"] * 0.0254

    # ---- BMI ----
    df["bmi"] = df["weightkg"] / (df["heightm"] ** 2)

    # ---- Gender ----
    df["ismale"] = np.nan
    df.loc[df["Q230"] == "Female", "ismale"] = 0
    df.loc[df["Q230"] == "Male", "ismale"] = 1

    df["gender"] = df["Q230"]

    # ---- Age ----
    df["age"] = pd.to_numeric(df["Q200"], errors="coerce")

    return df


def process_exercise(df):
    df = df.copy()

    # ---- Run pace + METS ----
    s = df.get("Q213", "").astype(str)

    df["runpace"] = np.nan
    df["runMETS"] = np.nan

    df.loc[s.str.contains("5:30", na=False), ["runpace","runMETS"]] = [5.5, 16]
    df.loc[s.str.contains("6:00", na=False), ["runpace","runMETS"]] = [6, 14.5]
    df.loc[s.str.contains("6:30", na=False), ["runpace","runMETS"]] = [6.5, 12.8]
    df.loc[s.str.contains("7:00", na=False), ["runpace","runMETS"]] = [7, 12.3]
    df.loc[s.str.contains("7:30", na=False), ["runpace","runMETS"]] = [7.5, 11.8]
    df.loc[s.str.contains("8:00", na=False), ["runpace","runMETS"]] = [8, 11.8]
    df.loc[s.str.contains("8:30", na=False), ["runpace","runMETS"]] = [8.5, 11]
    df.loc[s.str.contains("9:00", na=False), ["runpace","runMETS"]] = [9, 10.5]

    # defaults (SAS rule)
    df["runpace"] = df["runpace"].fillna(8)
    df["runMETS"] = df["runMETS"].fillna(11.8)

    # ---- Miles per week ----
    df["miles_wk"] = pd.to_numeric(df.get("Q212"), errors="coerce").fillna(0)

    # ---- Hours running ----
    df["hrsrunning"] = (df["miles_wk"] * df["runpace"]) / 60

    # ---- Intensity → METS helper ----
    def mets_from_intensity(series, high, mod, low, default):
        s = series.astype(str).str.lower()
        out = np.nan
        out = np.where(s.str.contains("high"), high, out)
        out = np.where(s.str.contains("moderate"), mod, out)
        out = np.where(s.str.contains("low"), low, out)
        return pd.Series(out).fillna(default)

    df["weightliftMETS"] = mets_from_intensity(df.get("Q215",""), 6, 5, 3.5, 5)
    df["aquajogMETS"]   = mets_from_intensity(df.get("Q219",""), 9.8, 6.8, 4.8, 6.8)
    df["bikeMETS"]      = mets_from_intensity(df.get("Q224",""), 10, 8, 6.8, 8)
    df["ellipticalMETS"]= mets_from_intensity(df.get("Q225",""), 9, 7, 5, 7)

    # ---- Activity hours (string → number) ----
    def hours_map(series):
        s = series.astype(str).str.lower()
        out = np.nan

        mapping = {
            "none": 0,
            "half": 0.5,
            "one hour": 1,
            "one and a half": 1.5,
            "two": 2,
            "two and a half": 2.5,
            "three": 3,
            "three and a half": 3.5,
            "four": 4,
            "four and a half": 4.5,
            "five": 5,
            "five and a half": 5.5,
            "six": 6,
            "six and a half": 6.5,
            "seven": 7,
            "seven and a half": 7.5,
            "eight": 8,
            "eight and a half": 8.5,
            "nine": 9,
            "nine and a half": 9.5,
            "ten": 10,
            "ten and a half": 10.5,
            "eleven": 11,
            "eleven and a half": 11.5,
            "twelve": 12,
            "twelve and a half": 12.5,
            "thirteen": 13,
            "thirteen and a half": 13.5,
            "fourteen": 14,
            "fourteen and a half": 14.5,
            "fifteen": 15
        }

        for key, val in mapping.items():
            out = np.where(s.str.contains(key), val, out)

        return pd.Series(out).fillna(0)

    df["weightlifthrs"] = hours_map(df.get("Q70",""))
    df["aquajoghrs"]    = hours_map(df.get("Q218",""))
    df["bikehrs"]       = hours_map(df.get("Q221",""))
    df["ellipticalhrs"] = hours_map(df.get("Q223",""))

    return df

def process_body_composition(df):
    df = df.copy()

    df["BodyFat"] = 1.2 * df["bmi"] + 0.23 * df["age"] - 10.8 * df["ismale"] - 5.4
    df["FFM"] = df["weightkg"] - (df["weightkg"] * df["BodyFat"] * 0.01)

    return df


def process_behavior_and_supplements(df):
    df = df.copy()

    def get_series(col):
        if col in df.columns:
            return df[col].astype(str)
        else:
            return pd.Series([""] * len(df))

    # ---- Meals / snacks ----
    num_map = {
        "one":1,"two":2,"three":3,"four":4,"five":5,
        "six":6,"seven":7,"eight":8,"nine":9,"ten":10
    }

    df["MealsDay"] = get_series("Q152").str.lower().map(num_map)
    df["SnacksDay"] = get_series("Q153").str.lower().map(num_map)

    # ---- Yes / No ----
    df["Fasting"] = np.where(get_series("Q154")=="Yes",1,0)
    df["Skip"] = np.where(get_series("Q155")=="Yes",1,0)

    # ---- Diet type ----
    s = get_series("Q157").str.lower()

    df["Vegetarian"] = np.where(s.str.contains("vegetarian", na=False),1,0)
    df["Vegan"] = np.where(s.str.contains("vegan", na=False),1,0)

    df["Restrict"] = np.where(
        (df["Vegetarian"]==1) | (df["Vegan"]==1) |
        ((get_series("Q158")=="Yes") & (get_series("Q232")=="No")),
        1,0
    )

    df["RestrictAllergy"] = np.where(get_series("Q232")=="Yes",1,0)

    # ---- Housing ----
    s = get_series("Q240").str.lower()

    df["Housing"] = np.nan
    df.loc[s.str.contains("student housing", na=False), "Housing"] = 1
    df.loc[s.str.contains("alone", na=False), "Housing"] = 2
    df.loc[s.str.contains("with one", na=False), "Housing"] = 3
    df.loc[s.str.contains("other", na=False), "Housing"] = 4

    # ---- Food prep ----
    s = get_series("Q241").str.lower()

    df["FoodPrep"] = np.nan
    df.loc[s.str.contains("family", na=False), "FoodPrep"] = 1
    df.loc[s.str.contains("i am", na=False), "FoodPrep"] = 2
    df.loc[s.str.contains("campus", na=False), "FoodPrep"] = 3
    df.loc[s.str.contains("another", na=False), "FoodPrep"] = 4

    # ---- Food insecurity ----
    s = get_series("Q245")

    df["FoodInsecure"] = np.where(
        (s=="Often true") | (s=="Sometimes true"), 1, 0
    )

    # ---- Supplements ----
    s165 = get_series("Q165")
    s166 = get_series("Q166")

    df["supp"] = np.where(
        ((s165=="I do not take vitamins or minerals.") | (s165=="")) &
        ((s166=="None") | (s166=="")),
        0,1
    )

    df["vitamin"] = np.where(s165.str.contains("Multivitamin", na=False),1,0)
    df["vitamind"] = np.where(s165.str.contains("Vitamin D", na=False),1,0)
    df["iron"] = np.where(s165.str.contains("Iron", na=False),1,0)
    df["calcium"] = np.where(s165.str.contains("Calcium", na=False),1,0)

    df["caffeine"] = np.where(s166.str.contains("Caffeine", na=False),1,0)
    df["creatine"] = np.where(s166.str.contains("Creatine", na=False),1,0)
    df["prewrkout"] = np.where(s166.str.contains("Preworkout", na=False),1,0)
    df["WtGainer"] = np.where(s166.str.contains("gain", na=False),1,0)
    df["WtLosssupp"] = np.where(s166.str.contains("loss", na=False),1,0)
    df["AAsupp"] = np.where(s166.str.contains("acids", na=False),1,0)
    df["HerBotSupp"] = np.where(s166.str.contains("botanicals", na=False),1,0)

    return df

def process_nutrients(df):
    df = df.copy()

    # helper: safe numeric
    def num(col):
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            return 0

    # ---- FRUIT ----
    df["fruitkcal"] = (num("fruits")*60) + (num("driedfruit")*60) + (num("fruitjuice")*120/7)
    df["FruitCHO"] = (num("fruits")*15) + (num("driedfruit")*15) + (num("fruitjuice")*30/7)
    df["FruitFiber"] = (num("fruits")*2) + (num("driedfruit")*2)
    df["Fruit"] = (num("fruits")/2) + (num("driedfruit")/2) + (num("fruitjuice")/7)

    # ---- COCONUT WATER ----
    df["coconutwaterkcal"] = num("coconutwater")*45/7
    df["coconutwatercho"] = num("coconutwater")*10/7

    # ---- NON-STARCHY VEG ----
    df["vegNSkcal"] = (num("vegrlg")*25) + (num("vegother")*37.5) + (num("TomSauc")*50/7) + (num("TomJuice")*50/7)
    df["vegNSCHO"] = (num("vegrlg")*5) + (num("vegother")*7.5) + (num("TomSauc")*10/7) + (num("TomJuice")*10/7)
    df["vegNSPRO"] = (num("vegrlg")*2) + (num("vegother")*3) + (num("TomSauc")*4/7) + (num("TomJuice")*4/7)
    df["vegNSFiber"] = (num("vegrlg")*2.5) + (num("vegother")*4) + (num("TomSauc")*4/7) + (num("TomJuice")*4/7)
    df["NSVeg"] = (num("vegrlg")*0.5) + (num("vegother")*1) + (num("TomSauc")/7) + (num("TomJuice")/7)

    # ---- GRAINS ----
    df["Grainkcal"] = (num("plainbrd")*80) + (num("BkdBrd")*125) + (num("CRPast")*80) + (num("GrnsOtr")*125)
    df["GrainCHO"] = (num("plainbrd")*15) + (num("BkdBrd")*15) + (num("CRPast")*15) + (num("GrnsOtr")*15)
    df["GrainPRO"] = (num("plainbrd")*3) + (num("BkdBrd")*3) + (num("CRPast")*3) + (num("GrnsOtr")*3)
    df["GrainFAT"] = (num("BkdBrd")*5) + (num("GrnsOtr")*5)
    df["GrainFiber"] = (num("plainbrd") + num("BkdBrd") + num("CRPast") + num("GrnsOtr"))*1
    df["Grains"] = num("plainbrd") + num("BkdBrd") + num("CRPast") + num("GrnsOtr")

    # ---- LEGUMES ----
    df["Legumeskcal"] = num("Legumess")*100/7
    df["LegumesCHO"] = num("Legumess")*15/7
    df["LegumesPRO"] = num("Legumess")*6/7
    df["LegumesFiber"] = num("Legumess")*5/7
    df["Legumes"] = num("Legumess")*0.14/2

    # ---- CORN ----
    df["Cornkcal"] = num("Corn")*80/7
    df["CornCHO"] = num("Corn")*15/7
    df["CornPRO"] = num("Corn")*3/7
    df["CornFiber"] = num("Corn")*1

    # ---- POTATO ----
    df["Potatokcal"] = (num("PotatoNF")*80 + num("PotatoFr")*125)/7
    df["PotatoCHO"] = (num("PotatoNF")*15 + num("PotatoFr")*15)/7
    df["PotatoPRO"] = (num("PotatoNF")*3 + num("PotatoFr")*3)/7
    df["PotatoFAT"] = num("PotatoFr")*5/7
    df["PotatoFiber"] = (num("PotatoNF") + num("PotatoFr"))/7
    df["PotatoTotal"] = (num("PotatoNF") + num("PotatoFr"))*0.14/2

    # ---- STARCH VEG ----
    df["VegSkcal"] = df["Legumeskcal"] + df["Cornkcal"] + df["Potatokcal"]
    df["VegSCHO"] = df["LegumesCHO"] + df["CornCHO"] + df["PotatoCHO"]
    df["vegSpro"] = df["LegumesPRO"] + df["CornPRO"] + df["PotatoPRO"]
    df["vegSfat"] = df["PotatoFAT"]
    df["vegSfiber"] = df["LegumesFiber"] + df["CornFiber"] + df["PotatoFiber"]

    df["StarchVeg"] = (num("Legumess") + num("Corn") + num("PotatoNF") + num("PotatoFr"))*0.14/2
    df["VegAll"] = df["NSVeg"] + df["StarchVeg"]

    # ---- MEAT + FISH + EGGS ----
    df["MeatPoultrykcal"] = (num("LeanMeat")*135 + num("FatMeat")*262.5)/7
    df["MeatPoultryPRO"] = (num("LeanMeat")*21 + num("FatMeat")*21)/7
    df["MeatPoultryFAT"] = (num("LeanMeat")*4.5 + num("FatMeat")*19.5)/7

    df["FattyFishkcal"] = num("FtyFish")*195/7
    df["FattyFishPRO"] = num("FtyFish")*21/7
    df["FattyFishFAT"] = num("FtyFish")*12/7

    df["Eggskcal"] = (num("WhEgg")*70 + num("EggWt")*20)/7
    df["EggsPRO"] = (num("WhEgg")*6 + num("EggWt")*4)/7
    df["EggsFAT"] = num("WhEgg")*5/7

    # ---- TOTAL KCAL (core outcome) ----
    df["KcalTotal"] = (
        df["fruitkcal"] + df["vegNSkcal"] + df["Grainkcal"] + df["VegSkcal"] +
        df["MeatPoultrykcal"] + df["FattyFishkcal"] + df["Eggskcal"] +
        df["coconutwaterkcal"]
    )

    # ---- MACROS ----
    df["CHO"] = (
        df["FruitCHO"] + df["vegNSCHO"] + df["GrainCHO"] +
        df["VegSCHO"] + df["coconutwatercho"]
    )

    df["FAT"] = (
        df["GrainFAT"] + df["vegSfat"] +
        df["MeatPoultryFAT"] + df["FattyFishFAT"] + df["EggsFAT"]
    )

    df["PRO"] = (
        df["vegNSPRO"] + df["GrainPRO"] + df["vegSpro"] +
        df["MeatPoultryPRO"] + df["FattyFishPRO"] + df["EggsPRO"]
    )

    df["Fiber"] = (
        df["FruitFiber"] + df["vegNSFiber"] + df["GrainFiber"] + df["vegSfiber"]
    )

    # ---- EXERCISE ENERGY ----
    df["runkcal"] = (num("weightkg")*num("runMETS")*num("hrsrunning"))/7
    df["weightliftkcal"] = (num("weightkg")*num("weightliftMETS")*num("weightlifthrs"))/7
    df["aquajogkcal"] = (num("weightkg")*num("aquajogMETS")*num("aquajoghrs"))/7
    df["bikekcal"] = (num("weightkg")*num("bikeMETS")*num("bikehrs"))/7
    df["ellipticalkcal"] = (num("weightkg")*num("ellipticalMETS")*num("ellipticalhrs"))/7

    df["EEE"] = df["runkcal"] + df["weightliftkcal"] + df["aquajogkcal"] + df["bikekcal"] + df["ellipticalkcal"]

    # ---- ENERGY AVAILABILITY ----
    df["EA"] = (df["KcalTotal"] - df["EEE"]) / num("FFM")
    df.loc[df["KcalTotal"] == 0, "EA"] = np.nan

    return df

def process_nutrients_part2(df):
    df = df.copy()

    def num(col):
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            return pd.Series([0]*len(df), index=df.index)

    # =========================
    # ---- MILK (by type) ----
    # =========================
    df["milkkcal"] = 0.0
    df["milkCHO"] = 0.0
    df["milkPRO"] = 0.0
    df["milkFAT"] = 0.0

    df["FlvMilkkcal"] = 0.0
    df["FlvMilkCHO"] = 0.0
    df["FlvMilkPRO"] = 0.0
    df["FlvMilkFAT"] = 0.0
    # nonfat
    mask = df["milktype"] == 1
    df.loc[mask, "milkkcal"] = num("milk")*90/7
    df.loc[mask, "milkCHO"] = num("milk")*12/7
    df.loc[mask, "milkPRO"] = num("milk")*8/7
    df.loc[mask, "milkFAT"] = num("milk")*1.5/7

    df.loc[mask, "FlvMilkkcal"] = num("FlvMilk")*168/7
    df.loc[mask, "FlvMilkCHO"] = num("FlvMilk")*34/7
    df.loc[mask, "FlvMilkPRO"] = num("FlvMilk")*8/7

    # lowfat
    mask = df["milktype"] == 2
    df.loc[mask, "milkkcal"] = num("milk")*120/7
    df.loc[mask, "milkFAT"] = num("milk")*5/7

    # whole
    mask = df["milktype"] == 3
    df.loc[mask, "milkkcal"] = num("milk")*150/7
    df.loc[mask, "milkFAT"] = num("milk")*8/7

    # soy
    mask = df["milktype"] == 4
    df.loc[mask, "milkkcal"] = num("milk")*100/7

    # almond/nonsoy
    mask = df["milktype"] == 5
    df.loc[mask, "milkkcal"] = num("milk")*50/7

    # =========================
    # ---- YOGURT ----
    # =========================
    df["yogkcal"] = 0.0
    df["yogCHO"] = 0.0
    df["yogPRO"] = 0.0
    df["yogFAT"] = 0.0
    mask = df["yogtype"] == 1
    df.loc[mask, "yogkcal"] = num("yogurt")*120/7

    mask = df["yogtype"] == 2
    df.loc[mask, "yogkcal"] = num("yogurt")*150/7

    mask = df["yogtype"] == 3
    df.loc[mask, "yogkcal"] = num("yogurt")*150/7

    mask = df["yogtype"] == 4
    df.loc[mask, "yogkcal"] = num("yogurt")*162/7

    mask = df["yogtype"] == 5
    df.loc[mask, "yogkcal"] = num("yogurt")*179/7

    mask = df["yogtype"] == 6
    df.loc[mask, "yogkcal"] = num("yogurt")*238/7

    # =========================
    # ---- CHEESE ----
    # =========================
    df["cheesekcal"] = 0.0
    df["cheesePRO"] = 0.0
    df["cheeseFAT"] = 0.0
    df["cheesecho"] = 0.0

    mask = df["cheesetype"] == 1
    df.loc[mask, "cheesekcal"] = num("cheese")*100/7
    df.loc[mask, "cheesePRO"] = num("cheese")*7/7
    df.loc[mask, "cheeseFAT"] = num("cheese")*8/7

    mask = df["cheesetype"] == 2
    df.loc[mask, "cheesekcal"] = num("cheese")*75/7

    mask = df["cheesetype"] == 3
    df.loc[mask, "cheesekcal"] = num("cheese")*74/7
    df.loc[mask, "cheesecho"] = num("cheese")*3/7

    # =========================
    # ---- SWEETS ----
    # =========================
    df["sweetskcal"] = (
        num("ChocCndy")*105/7 +
        num("NonChcCndy")*60/7 +
        num("IceCrm")*150/7 +
        num("FroYo")*105/7 +
        num("BkdGd")*105/7
    )

    # =========================
    # ---- DRINKS ----
    # =========================
    df["drinkskcal"] = (
        num("SwtBvg")*120 +
        num("SwtTCfee")*75 +
        num("OtrSwtBvg")*120 +
        num("NrgDrnk")*110 +
        num("chodrnk")*65/7
    )

    # =========================
    # ---- TOTAL KCAL FINAL ----
    # =========================
    df["KcalTotal"] = (
        df["KcalTotal"] +
        df["milkkcal"] + df["FlvMilkkcal"] +
        df["yogkcal"] +
        df["cheesekcal"] +
        df["sweetskcal"] +
        df["drinkskcal"]
    )

    # =========================
    # ---- FINAL ENERGY ----
    # =========================
    df["EI"] = df["KcalTotal"]
    df.loc[df["EI"] == 0, "EI"] = np.nan

    df["EI_kg"] = df["EI"] / num("weightkg")

    # =========================
    # ---- LOW EA FLAGS ----
    # =========================
    df["lowEA_clinical"] = 0
    df["lowEA_subclinical"] = 0

    male = df["ismale"] == 1
    female = df["ismale"] == 0

    df.loc[male & (df["EA"] > 0) & (df["EA"] < 15), "lowEA_clinical"] = 1
    df.loc[male & (df["EA"] >= 15) & (df["EA"] < 30), "lowEA_subclinical"] = 1

    df.loc[female & (df["EA"] > 0) & (df["EA"] < 30), "lowEA_clinical"] = 1
    df.loc[female & (df["EA"] >= 30) & (df["EA"] < 45), "lowEA_subclinical"] = 1

    return df

# ===============================
# OUTPUT DATASET FUNCTIONS
# ===============================

def create_redcap_dataset(df):
    df = df.copy()

    cols = [
        "id","age","gender","ismale","weightkg","heightm","bmi","FFM",
        "EEE","EI","EI_kg","EA","lowEA_clinical","lowEA_subclinical",
        "miles_wk","Fruit","NSVeg","StarchVeg","VegAll","Legumes","Grains",
        "ProFoods","MtPltry","FttyFish","Eggs","Dairy","fluids",
        "CHO","CHOkg","PRO","PROkg","FAT","FATkg","Fiber",
        "MealsDay","SnacksDay","Fasting","Skip","Vegetarian","Vegan",
        "Restrict","RestrictAllergy","Housing","FoodPrep","FoodInsecure",
        "percep1","percep2","percep3","percep4","percep5",
        "BarsWk","ProBarsWk","ProDrnkWk","GelChewWk",
        "chodrnk","caffdrnk",
        "supp","vitamin","iron","calcium","vitamind",
        "caffeine","creatine","prewrkout","wtgainer","wtlosssupp",
        "aasupp","herbotsupp"
    ]

    cols = [c for c in cols if c in df.columns]
    return df[cols]


def create_allnutrition_dataset(df):
    df = df.copy()

    drop_cols = [c for c in df.columns if c.startswith("Q")]

    return df.drop(columns=drop_cols, errors="ignore")


# ===============================
# MAIN APP EXECUTION
# ===============================

if uploaded_file is not None:
    df = read_uploaded_file(uploaded_file)
    df = normalize_qualtrics_columns(df)

    df = process_servings(df)
    df = create_food_variables(df)
    df = process_dairy_types(df)
    df = process_body_metrics(df)
    df = process_exercise(df)
    df = process_body_composition(df)
    df = process_behavior_and_supplements(df)
    df = process_nutrients(df)
    df = process_nutrients_part2(df)

    df_redcap = create_redcap_dataset(df)
    df_all = create_allnutrition_dataset(df)

    # DISPLAY
    st.write("REDCap dataset")
    st.dataframe(df_redcap.head())

    # DOWNLOAD BUTTONS
    st.download_button(
        "Download REDCap dataset",
        df_redcap.to_csv(index=False),
        "redcap.csv"
    )

    st.download_button(
        "Download full dataset",
        df_all.to_csv(index=False),
        "allnutrition.csv"
    )
