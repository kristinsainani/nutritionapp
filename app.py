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
    safe_assign("tomsauc", "Q1")
    safe_assign("tomjuice", "Q150")
    safe_assign("plainbrd", "Q24")
    safe_assign("bkdbrd", "Q165_0001")
    safe_assign("crpast", "Q23")
    safe_assign("grnsotr", "Q148")
    safe_assign("legumess", "Q161_0001")
    safe_assign("corn", "Q162_0001")
    safe_assign("potatonf", "Q163")
    safe_assign("potatofr", "Q164")
    safe_assign("leanmeat", "Q27")
    safe_assign("fatmeat", "Q28")
    safe_assign("ftyfish", "Q29")
    safe_assign("whegg", "Q177")
    safe_assign("eggwt", "Q178")
    safe_assign("milk", "Q33")
    safe_assign("flvmilk", "Q169")
    safe_assign("yogurt", "Q170")
    safe_assign("flvyogurt", "Q168")
    safe_assign("cheese", "Q171")
    safe_assign("cotcheese", "Q35")
    safe_assign("vegoil", "Q261")
    safe_assign("nutbtr", "Q262")
    safe_assign("cocoilbt", "Q263")
    safe_assign("butter", "Q264")
    safe_assign("lard", "Q265")
    safe_assign("srcrm", "Q266")
    safe_assign("crmchs", "Q267")
    safe_assign("cream", "Q268")
    safe_assign("mayo", "Q269")
    safe_assign("mrgrne", "Q270")
    safe_assign("hlfhlf", "Q271")
    safe_assign("olives", "Q160_0001")
    safe_assign("nuts", "Q158_0001")
    safe_assign("avocado", "Q134")
    safe_assign("choccndy", "Q42")
    safe_assign("nonchccndy", "Q61")
    safe_assign("icecrm", "Q62")
    safe_assign("froyo", "Q63")
    safe_assign("bkdgd", "Q43")
    safe_assign("swtbvg", "Q60")
    safe_assign("swttcfee", "Q278")
    safe_assign("otrswtbvg", "Q280")
    safe_assign("nrgdrnk", "Q279")
    safe_assign("coconutwater", "Q276")
    safe_assign("slddressing", "Q257")
    safe_assign("nrgbar", "Q125")
    safe_assign("probar", "Q281")
    safe_assign("chodrnk", "Q282")
    safe_assign("gel", "Q285")
    safe_assign("prodrnk", "Q284")
    safe_assign("zerocaldrnk", "Q273")
    safe_assign("unswttcfee", "Q272")
    safe_assign("water", "Q52")
    safe_assign("beer", "Q289")
    safe_assign("spirits", "Q290")
    safe_assign("mixed", "Q291")
    safe_assign("wine", "Q292")

    return df

def process_dairy_types(df):
    df = df.copy()

    def get_series(col):
        if col in df.columns:
            return df[col].astype(str)
        else:
            return pd.Series([""] * len(df))

    # ---- MILK ----
    s = get_series("Q64")

    df["milktype"] = np.nan
    df.loc[s.str.contains("Non fat", na=False, regex=False), "milktype"] = 1
    df.loc[s.str.contains("Low fat", na=False, regex=False), "milktype"] = 2
    df.loc[s.str.contains("Regular", na=False, regex=False), "milktype"] = 3
    df.loc[s.str.contains("soy milk", na=False, regex=False), "milktype"] = 4
    df.loc[s.str.contains("almond milk", na=False, regex=False), "milktype"] = 5

    df["milktype"] = df["milktype"].fillna(2)

    # ---- PLAIN YOGURT ----
    s = get_series("Q65")

    df["yogtype"] = np.nan
    df.loc[s.str.contains("Non fat yogurt", na=False, regex=False), "yogtype"] = 1
    df.loc[s.str.contains("Low fat yogurt", na=False, regex=False), "yogtype"] = 2
    df.loc[s.str.contains("Regular (full-fat) yogurt", na=False, regex=False), "yogtype"] = 3
    df.loc[s.str.contains("Non-dairy yogurt", na=False, regex=False), "yogtype"] = 4
    df.loc[s.str.contains("Greek yogurt (non fat", na=False, regex=False), "yogtype"] = 5
    df.loc[s.str.contains("Greek yogurt (regular", na=False, regex=False), "yogtype"] = 6

    df["yogtype"] = df["yogtype"].fillna(2)

    # ---- FLAVORED YOGURT ----
    s = get_series("Q286")

    df["flvyogtype"] = np.nan
    df.loc[s.str.contains("Non fat yogurt", na=False, regex=False), "flvyogtype"] = 1
    df.loc[s.str.contains("Low fat yogurt", na=False, regex=False), "flvyogtype"] = 2
    df.loc[s.str.contains("Non-dairy yogurt", na=False, regex=False), "flvyogtype"] = 3
    df.loc[s.str.contains("Greek yogurt", na=False, regex=False), "flvyogtype"] = 4
    df.loc[s.str.contains("no sugar added", na=False, regex=False), "flvyogtype"] = 5

    df["flvyogtype"] = df["flvyogtype"].fillna(2)

    # ---- CHEESE ----
    s = get_series("Q179")

    df["cheesetype"] = np.nan
    df.loc[s.str.contains("Regular dairy cheese", na=False, regex=False), "cheesetype"] = 1
    df.loc[s.str.contains("Reduced fat", na=False, regex=False) | 
           s.str.contains("light", na=False, regex=False), "cheesetype"] = 2
    df.loc[s.str.contains("Non-dairy cheese", na=False, regex=False), "cheesetype"] = 3

    df["cheesetype"] = df["cheesetype"].fillna(1)

    # ---- SALAD DRESSING ----
    s = get_series("Q156_0001")

    df["slddessingtype"] = np.nan
    df.loc[s.str.contains("Regular", na=False, regex=False), "slddessingtype"] = 1
    df.loc[s.str.contains("Reduced", na=False, regex=False), "slddessingtype"] = 2
    df.loc[s.str.contains("Fat-free", na=False, regex=False), "slddessingtype"] = 3

    df["slddessingtype"] = df["slddessingtype"].fillna(1)

    return df

def process_body_composition(df):
    df = df.copy()

    df["bodyfat"] = 1.2 * df["bmi"] + 0.23 * df["age"] - 10.8 * df["ismale"] - 5.4
    df["ffm"] = df["weightkg"] - (df["weightkg"] * df["bodyfat"] * 0.01)

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

    df["mealsday"] = get_series("Q152").str.lower().map(num_map)
    df["snacksday"] = get_series("Q153").str.lower().map(num_map)

    # ---- Yes / No ----
    df["fasting"] = np.where(get_series("Q154")=="Yes",1,0)
    df["skip"] = np.where(get_series("Q155")=="Yes",1,0)

    # ---- Diet type ----
    s = get_series("Q157").str.lower()

    df["vegetarian"] = np.where(s.str.contains("vegetarian", na=False),1,0)
    df["vegan"] = np.where(s.str.contains("vegan", na=False),1,0)

    df["restrict"] = np.where(
        (df["vegetarian"]==1) | (df["vegan"]==1) |
        ((get_series("Q158")=="Yes") & (get_series("Q232")=="No")),
        1,0
    )

    df["restrictallergy"] = np.where(get_series("Q232")=="Yes",1,0)

    # ---- Housing ----
    s = get_series("Q240").str.lower()

    df["housing"] = np.nan
    df.loc[s.str.contains("student housing", na=False), "housing"] = 1
    df.loc[s.str.contains("alone", na=False), "housing"] = 2
    df.loc[s.str.contains("with one", na=False), "housing"] = 3
    df.loc[s.str.contains("other", na=False), "housing"] = 4

    # ---- Food prep ----
    s = get_series("Q241").str.lower()

    df["foodprep"] = np.nan
    df.loc[s.str.contains("family", na=False), "foodprep"] = 1
    df.loc[s.str.contains("i am", na=False), "foodprep"] = 2
    df.loc[s.str.contains("campus", na=False), "foodprep"] = 3
    df.loc[s.str.contains("another", na=False), "foodprep"] = 4

    # ---- Food insecurity ----
    s = get_series("Q245")

    df["foodinsecure"] = np.where(
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
    df["wtgainer"] = np.where(s166.str.contains("gain", na=False),1,0)
    df["wtlosssupp"] = np.where(s166.str.contains("loss", na=False),1,0)
    df["aasupp"] = np.where(s166.str.contains("acids", na=False),1,0)
    df["herbotsupp"] = np.where(s166.str.contains("botanicals", na=False),1,0)

    return df

def process_nutrients(df):
    df = df.copy()

    # helper: safe numeric (ALWAYS return a Series)
    def num(col):
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            return pd.Series(0, index=df.index)

    # ---- FRUIT ----
    df["fruitkcal"] = (num("fruits")*60) + (num("driedfruit")*60) + (num("fruitjuice")*120/7)
    df["fruitcho"] = (num("fruits")*15) + (num("driedfruit")*15) + (num("fruitjuice")*30/7)
    df["fruitfiber"] = (num("fruits")*2) + (num("driedfruit")*2)
    df["fruit"] = (num("fruits")/2) + (num("driedfruit")/2) + (num("fruitjuice")/7)

    # ---- COCONUT WATER ----
    df["coconutwaterkcal"] = num("coconutwater")*45/7
    df["coconutwatercho"] = num("coconutwater")*10/7

    # ---- NON-STARCHY VEG ----
    df["vegnskcal"] = (num("vegrlg")*25) + (num("vegother")*37.5) + (num("tomsauc")*50/7) + (num("tomjuice")*50/7)
    df["vegnscho"] = (num("vegrlg")*5) + (num("vegother")*7.5) + (num("tomsauc")*10/7) + (num("tomjuice")*10/7)
    df["vegnspro"] = (num("vegrlg")*2) + (num("vegother")*3) + (num("tomsauc")*4/7) + (num("tomjuice")*4/7)
    df["vegnsfiber"] = (num("vegrlg")*2.5) + (num("vegother")*4) + (num("tomsauc")*4/7) + (num("tomjuice")*4/7)
    df["nsveg"] = (num("vegrlg")*0.5) + (num("vegother")*1) + (num("tomsauc")/7) + (num("tomjuice")/7)

    # ---- GRAINS ----
    df["grainkcal"] = (num("plainbrd")*80) + (num("bkdbrd")*125) + (num("crpast")*80) + (num("grnsotr")*125)
    df["graincho"] = (num("plainbrd")*15) + (num("bkdbrd")*15) + (num("crpast")*15) + (num("grnsotr")*15)
    df["grainpro"] = (num("plainbrd")*3) + (num("bkdbrd")*3) + (num("crpast")*3) + (num("grnsotr")*3)
    df["grainfat"] = (num("bkdbrd")*5) + (num("grnsotr")*5)
    df["grainfiber"] = (num("plainbrd") + num("bkdbrd") + num("crpast") + num("grnsotr"))
    df["grains"] = num("plainbrd") + num("bkdbrd") + num("crpast") + num("grnsotr")

    # ---- LEGUMES ----
    df["legumeskcal"] = num("legumess")*100/7
    df["legumescho"] = num("legumess")*15/7
    df["legumespro"] = num("legumess")*6/7
    df["legumesfiber"] = num("legumess")*5/7
    df["legumes"] = num("legumess")*0.14/2

    # ---- CORN ----
    df["cornkcal"] = num("corn")*80/7
    df["corncho"] = num("corn")*15/7
    df["cornpro"] = num("corn")*3/7
    df["cornfiber"] = num("corn")*1

    # ---- POTATO ----
    df["potatokcal"] = (num("potatonf")*80 + num("potatofr")*125)/7
    df["potatocho"] = (num("potatonf")*15 + num("potatofr")*15)/7
    df["potatopro"] = (num("potatonf")*3 + num("potatofr")*3)/7
    df["potatofat"] = num("potatofr")*5/7
    df["potatofiber"] = (num("potatonf") + num("potatofr"))/7
    df["potatototal"] = (num("potatonf") + num("potatofr"))*0.14/2

    # ---- STARCH VEG ----
    df["vegskcal"] = df["legumeskcal"] + df["cornkcal"] + df["potatokcal"]
    df["vegscho"] = df["legumescho"] + df["corncho"] + df["potatocho"]
    df["vegspro"] = df["legumespro"] + df["cornpro"] + df["potatopro"]
    df["vegsfat"] = df["potatofat"]
    df["vegsfiber"] = df["legumesfiber"] + df["cornfiber"] + df["potatofiber"]

    df["starchveg"] = (num("legumess") + num("corn") + num("potatonf") + num("potatofr"))*0.14/2
    df["vegall"] = df["nsveg"] + df["starchveg"]

    # ---- MEAT + FISH + EGGS ----
    df["meatpoultrykcal"] = (num("leanmeat")*135 + num("fatmeat")*262.5)/7
    df["meatpoultrypro"] = (num("leanmeat")*21 + num("fatmeat")*21)/7
    df["meatpoultryfat"] = (num("leanmeat")*4.5 + num("fatmeat")*19.5)/7

    df["fattyfishkcal"] = num("ftyfish")*195/7
    df["fattyfishpro"] = num("ftyfish")*21/7
    df["fattyfishfat"] = num("ftyfish")*12/7

    df["eggskcal"] = (num("whegg")*70 + num("eggwt")*20)/7
    df["eggspro"] = (num("whegg")*6 + num("eggwt")*4)/7
    df["eggsfat"] = num("whegg")*5/7

    # ---- TOTAL KCAL ----
    df["kcaltotal"] = (
        df["fruitkcal"] + df["vegnskcal"] + df["grainkcal"] + df["vegskcal"] +
        df["meatpoultrykcal"] + df["fattyfishkcal"] + df["eggskcal"] +
        df["coconutwaterkcal"]
    )

    # ---- MACROS ----
    df["cho"] = (
        df["fruitcho"] + df["vegnscho"] + df["graincho"] +
        df["vegscho"] + df["coconutwatercho"]
    )

    df["fat"] = (
        df["grainfat"] + df["vegsfat"] +
        df["meatpoultryfat"] + df["fattyfishfat"] + df["eggsfat"]
    )

    df["pro"] = (
        df["vegnspro"] + df["grainpro"] + df["vegspro"] +
        df["meatpoultrypro"] + df["fattyfishpro"] + df["eggspro"]
    )

    df["fiber"] = (
        df["fruitfiber"] + df["vegnsfiber"] + df["grainfiber"] + df["vegsfiber"]
    )

    # ---- EXERCISE ----
    df["runkcal"] = (num("weightkg")*num("runmets")*num("hrsrunning"))/7
    df["weightliftkcal"] = (num("weightkg")*num("weightliftmets")*num("weightlifthrs"))/7
    df["aquajogkcal"] = (num("weightkg")*num("aquajogmets")*num("aquajoghrs"))/7
    df["bikekcal"] = (num("weightkg")*num("bikemets")*num("bikehrs"))/7
    df["ellipticalkcal"] = (num("weightkg")*num("ellipticalmets")*num("ellipticalhrs"))/7

    df["eee"] = df["runkcal"] + df["weightliftkcal"] + df["aquajogkcal"] + df["bikekcal"] + df["ellipticalkcal"]

    # ---- EA ----
    df["ea"] = (df["kcaltotal"] - df["eee"]) / num("ffm")
    df.loc[df["kcaltotal"] == 0, "ea"] = np.nan

    return df
    
def process_nutrients_part2(df):
    df = df.copy()

    def num(col):
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            return pd.Series(0, index=df.index)

    # =========================
    # ---- MILK (by type) ----
    # =========================
    df["milkkcal"] = 0.0
    df["milkcho"] = 0.0
    df["milkpro"] = 0.0
    df["milkfat"] = 0.0

    df["flvmilkkcal"] = 0.0
    df["flvmilkcho"] = 0.0
    df["flvmilkpro"] = 0.0
    df["flvmilkfat"] = 0.0

    # nonfat
    mask = df["milktype"] == 1
    df.loc[mask, "milkkcal"] = num("milk")*90/7
    df.loc[mask, "milkcho"] = num("milk")*12/7
    df.loc[mask, "milkpro"] = num("milk")*8/7
    df.loc[mask, "milkfat"] = num("milk")*1.5/7

    df.loc[mask, "flvmilkkcal"] = num("flvmilk")*168/7
    df.loc[mask, "flvmilkcho"] = num("flvmilk")*34/7
    df.loc[mask, "flvmilkpro"] = num("flvmilk")*8/7

    # lowfat
    mask = df["milktype"] == 2
    df.loc[mask, "milkkcal"] = num("milk")*120/7
    df.loc[mask, "milkfat"] = num("milk")*5/7

    # whole
    mask = df["milktype"] == 3
    df.loc[mask, "milkkcal"] = num("milk")*150/7
    df.loc[mask, "milkfat"] = num("milk")*8/7

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
    df["yogcho"] = 0.0
    df["yogpro"] = 0.0
    df["yogfat"] = 0.0

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
    df["cheesepro"] = 0.0
    df["cheesefat"] = 0.0
    df["cheesecho"] = 0.0

    mask = df["cheesetype"] == 1
    df.loc[mask, "cheesekcal"] = num("cheese")*100/7
    df.loc[mask, "cheesepro"] = num("cheese")*7/7
    df.loc[mask, "cheesefat"] = num("cheese")*8/7

    mask = df["cheesetype"] == 2
    df.loc[mask, "cheesekcal"] = num("cheese")*75/7

    mask = df["cheesetype"] == 3
    df.loc[mask, "cheesekcal"] = num("cheese")*74/7
    df.loc[mask, "cheesecho"] = num("cheese")*3/7

    # =========================
    # ---- SWEETS ----
    # =========================
    df["sweetskcal"] = (
        num("choccndy")*105/7 +
        num("nonchccndy")*60/7 +
        num("icecrm")*150/7 +
        num("froyo")*105/7 +
        num("bkdgd")*105/7
    )

    # =========================
    # ---- DRINKS ----
    # =========================
    df["drinkskcal"] = (
        num("swtbvg")*120 +
        num("swttcfee")*75 +
        num("otrswtbvg")*120 +
        num("nrgdrnk")*110 +
        num("chodrnk")*65/7
    )

    # =========================
    # ---- TOTAL KCAL FINAL ----
    # =========================
    df["kcaltotal"] = (
        df["kcaltotal"] +
        df["milkkcal"] + df["flvmilkkcal"] +
        df["yogkcal"] +
        df["cheesekcal"] +
        df["sweetskcal"] +
        df["drinkskcal"]
    )

    # =========================
    # ---- FINAL ENERGY ----
    # =========================
    df["ei"] = df["kcaltotal"]
    df.loc[df["ei"] == 0, "ei"] = np.nan

    df["ei_kg"] = df["ei"] / num("weightkg")

    # =========================
    # ---- LOW EA FLAGS ----
    # =========================
    df["lowea_clinical"] = 0
    df["lowea_subclinical"] = 0

    male = df["ismale"] == 1
    female = df["ismale"] == 0

    df.loc[male & (df["ea"] > 0) & (df["ea"] < 15), "lowea_clinical"] = 1
    df.loc[male & (df["ea"] >= 15) & (df["ea"] < 30), "lowea_subclinical"] = 1

    df.loc[female & (df["ea"] > 0) & (df["ea"] < 30), "lowea_clinical"] = 1
    df.loc[female & (df["ea"] >= 30) & (df["ea"] < 45), "lowea_subclinical"] = 1

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

    # 👇 PREVIEW UPLOADED FILE
    st.write("Preview of uploaded file")
    st.dataframe(df.head())

    # ===============================
    # PROCESSING PIPELINE
    # ===============================
    df = process_servings(df)
    df = create_food_variables(df)
    df = process_dairy_types(df)
    df = process_body_metrics(df)
    df = process_exercise(df)
    df = process_body_composition(df)
    df = process_behavior_and_supplements(df)
    df = process_nutrients(df)
    df = process_nutrients_part2(df)

    # ===============================
    # OUTPUT DATASETS
    # ===============================
    df_redcap = create_redcap_dataset(df)
    df_all = create_allnutrition_dataset(df)

    # 👇 PREVIEW FINAL REDCAP DATA
    st.write("REDCap dataset (final output)")
    st.dataframe(df_redcap.head())

    # 👇 OPTIONAL DEBUG (REMOVE LATER)
    st.write("Check key outputs")
    st.dataframe(df[["kcaltotal","cho","fat","pro","fiber","ea","ei"]].head())

    # ===============================
    # DOWNLOADS
    # ===============================
    st.download_button(
        "Download REDCap dataset",
        df_redcap.to_csv(index=False),
        "redcapnutrition.csv"
    )

    st.download_button(
        "Download full dataset (allnutrition)",
        df_all.to_csv(index=False),
        "allnutrition.csv"
    )
