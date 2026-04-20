import io
import re
import numpy as np
from typing import List, Tuple


import pandas as pd
import streamlit as st

st.set_page_config(page_title="Nutrition FFQ Processor", layout="wide")

FOOD_COUNT_VARS = [
    "Q10", "Q11", "Q12", "Q149", "Q146", "Q1", "Q150", "Q24", "Q165_0001", "Q23", "Q148", "Q161_0001", "Q162_0001", "Q163", "Q164", "Q27",
    "Q28", "Q29", "Q177", "Q178", "Q33", "Q169", "Q170", "Q168", "Q171", "Q35", "Q261", "Q262",
    "Q263", "Q264", "Q265", "Q266", "Q267", "Q268", "Q26", "Q270", "Q271", "Q160_0001", "Q158_0001", "Q134", "Q42", "Q61", "Q62", "Q63", "Q43", "Q60", "Q278",
    "Q279", "Q280", "Q276", "Q257", "Q125", "Q281", "Q282", "Q285", "Q284", "Q273", "Q272", "Q52", "Q269", "Q289", "Q290", "Q291", "Q292",
]

HOUR_VARS = ["Q70", "Q218", "Q221", "Q223"]

REDCAP_KEEP = [
    "id", "age", "gender", "ismale", "weightkg", "heightm", "bmi", "ffm", "eee", "ei", "ei_kg", "ea", "lowea_clinical", "lowea_subclinical",
    "miles_wk", "fruit", "nsveg", "starchveg", "vegall", "legumes", "grains", "profoods", "mtpltry", "fttyfish", "eggs", "dairy", "fluids",
    "cho", "chokg", "pro", "prokg", "fat", "fatkg", "fiber", "mealsday", "snacksday", "fasting", "skip", "vegetarian", "vegan", "restrict",
    "restrictallergy", "housing", "foodprep", "foodinsecure", "percep1", "percep2", "percep3", "percep4", "percep5", "barswk", "probarswk",
    "prodrnkwk", "gelchewwk", "chodrnk", "caffdrnk", "supp", "vitamin", "iron", "calcium", "vitamind", "caffeine", "creatine", "prewrkout",
    "wtgainer", "wtlosssupp", "aasupp", "herbotsupp",
]

NUM_WORDS = {
    "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9,
    "TEN": 10, "ELEVEN": 11, "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14, "FIFTEEN": 15, "SIXTEEN": 16,
    "SEVENTEEN": 17, "EIGHTEEN": 18, "NINETEEN": 19, "TWENTY": 20, "TWENTY-ONE": 21, "TWENTY-TWO": 22,
    "TWENTY-THREE": 23, "TWENTY-FOUR": 24, "TWENTY-FIVE": 25, "TWENTY-SIX": 26, "TWENTY-SEVEN": 27,
    "TWENTY-EIGHT": 28, "TWENTY-NINE": 29, "THIRTY": 30, "THIRTY-ONE": 31, "THIRTY-TWO": 32,
    "THIRTY-THREE": 33, "THIRTY-FOUR": 34, "THIRTY-FIVE": 35,
}
NUM_PATTERNS = sorted(NUM_WORDS.items(), key=lambda kv: len(kv[0]), reverse=True)

HOUR_WORDS = {
    "HALF": 0.5,
    "ONE AND A HALF": 1.5, "TWO AND A HALF": 2.5, "THREE AND A HALF": 3.5, "FOUR AND A HALF": 4.5,
    "FIVE AND A HALF": 5.5, "SIX AND A HALF": 6.5, "SEVEN AND A HALF": 7.5, "EIGHT AND A HALF": 8.5,
    "NINE AND A HALF": 9.5, "TEN AND A HALF": 10.5, "ELEVEN AND A HALF": 11.5, "TWELVE AND A HALF": 12.5,
    "THIRTEEN AND A HALF": 13.5, "FOURTEEN AND A HALF": 14.5,
    "ONE HOUR": 1, "TWO HOURS": 2, "THREE HOURS": 3, "FOUR HOURS": 4, "FIVE HOURS": 5,
    "SIX HOURS": 6, "SEVEN HOURS": 7, "EIGHT HOURS": 8, "NINE HOURS": 9, "TEN HOURS": 10,
    "ELEVEN HOURS": 11, "TWELVE HOURS": 12, "THIRTEEN HOURS": 13, "FOURTEEN HOURS": 14, "FIFTEEN HOURS": 15,
}
HOUR_PATTERNS = sorted(HOUR_WORDS.items(), key=lambda kv: len(kv[0]), reverse=True)


def drop_qualtrics_metadata_rows(df):
    return df.drop(index=1).reset_index(drop=True)

def contains(x, text: str) -> bool:
    if pd.isna(x):
        return False
    return text.lower() in str(x).lower()


def extract_first_numeric(x):
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    match = re.search(r"(\d+(?:\.\d+)?)", str(x))
    return float(match.group(1)) if match else np.nan


def parse_food_count(x) -> float:
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float, np.integer, np.floating)):
        return 0.0 if pd.isna(x) else float(x)

    s = str(x).strip().upper()
    if s in {"", "NAN", "NONE"}:
        return 0.0
    if "PREFER NOT TO ANSWER" in s or "< ONE" in s or "LESS THAN ONE" in s:
        return 0.0
    if "> THIRTY-FIVE" in s:
        return 36.0
    if "> THIRTY" in s:
        return 31.0
    if "> FIFTEEN" in s:
        return 16.0

    for pat, value in NUM_PATTERNS:
        if pat in {"ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TWENTY", "THIRTY", "FIFTEEN", "THIRTY-FIVE"}:
            if s.startswith(pat):
                return float(value)
        elif pat in s:
            return float(value)

    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if nums:
        return float(nums[0])
    return 0.0


def parse_hour_value(x) -> float:
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float, np.integer, np.floating)):
        return 0.0 if pd.isna(x) else float(x)

    s = str(x).strip().upper()
    if s in {"", "NAN", "NONE", "NO DAYS"}:
        return 0.0

    for pat, value in HOUR_PATTERNS:
        if s.startswith(pat):
            return float(value)

    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if nums:
        return float(nums[0])
    return 0.0


def load_input_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Please upload a CSV or Excel file.")


def ensure_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = np.nan
    return df


def process_nutrition_data(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str], pd.DataFrame]:
    warnings: List[str] = []

    df = raw_df.copy()
    out = df.copy()


    aliases = {
        "fruits": "Q10", "driedfruit": "Q11", "fruitjuice": "Q12", "vegrlg": "Q149", "vegother": "Q146",
        "tomsauc": "Q1", "tomjuice": "Q150", "plainbrd": "Q24", "bkdbrd": "Q165_0001", "crpast": "Q23",
        "grnsotr": "Q148", "legumess": "Q161_0001", "corn": "Q162_0001", "potatonf": "Q163", "potatofr": "Q164",
        "leanmeat": "Q27", "fatmeat": "Q28", "ftyfish": "Q29", "whegg": "Q177", "eggwt": "Q178",
        "milk": "Q33", "flvmilk": "Q169", "yogurt": "Q170", "flvyogurt": "Q168", "cheese": "Q171",
        "cotcheese": "Q35", "vegoil": "Q261", "nutbtr": "Q262", "cocoilbt": "Q263", "butter": "Q264",
        "lard": "Q265", "srcrm": "Q266", "crmchs": "Q267", "cream": "Q268", "mayo": "Q269",
        "mrgrne": "Q270", "hlfhlf": "Q271", "olives": "Q160_0001", "nuts": "Q158_0001", "avocado": "Q134",
        "choccndy": "Q42", "nonchccndy": "Q61", "icecrm": "Q62", "froyo": "Q63", "bkdgd": "Q43",
        "swtbvg": "Q60", "swttcfee": "Q278", "nrgdrnk": "Q279", "otrswtbvg": "Q280", "coconutwater": "Q276",
        "slddressing": "Q257", "nrgbar": "Q125", "probar": "Q281", "chodrnk": "Q282", "gel": "Q285",
        "prodrnk": "Q284", "zerocaldrnk": "Q273", "unswttcfee": "Q272", "water": "Q52", "beer": "Q289",
        "spirits": "Q290", "mixed": "Q291", "wine": "Q292",
    }
    for new_col, old_col in aliases.items():
        out[new_col] = pd.to_numeric(out[old_col], errors="coerce").fillna(0)

    # alcohol: put back; if missing, set to 0
    for alcohol_col in ["beer", "spirits", "mixed", "wine"]:
        out[alcohol_col] = pd.to_numeric(out[alcohol_col], errors="coerce").fillna(0)

    out["milktype"] = out["Q64"].apply(
        lambda x: 1 if contains(x, "Non fat") else 2 if contains(x, "Low fat") else 3 if contains(x, "Regular")
        else 4 if contains(x, "Non-dairy [soy milk]") else 5 if contains(x, "Non-dairy [almond milk,") else 2
    )

    def map_yogtype(x):
        if contains(x, "Non fat yogurt"):
            return 1
        if contains(x, "Low fat yogurt"):
            return 2
        if contains(x, "Regular (full-fat) yogurt"):
            return 3
        if contains(x, "Non-dairy yogurt"):
            return 4
        if contains(x, "Greek yogurt (non fat"):
            return 5
        if contains(x, "Greek yogurt (regular"):
            return 6
        return 2

    def map_flvyogtype(x):
        value = np.nan
        s = "" if pd.isna(x) else str(x)
        if "Non fat yogurt" in s:
            value = 1
        if "Low fat yogurt" in s:
            value = 2
        if "Non-dairy yogurt" in s:
            value = 3
        if "Greek yogurt" in s:
            value = 4
        if 'Non fat "no sugar added" or "diet" yogurt' in s:
            value = 5
        return 2 if pd.isna(value) else value

    def map_cheesetype(x):
        if contains(x, "Regular dairy cheese"):
            return 1
        if contains(x, "Reduced fat or light"):
            return 2
        if contains(x, "Non-dairy cheese"):
            return 3
        return 1

    def map_dressingtype(x):
        if contains(x, "Regular"):
            return 1
        if contains(x, "Reduced-fat"):
            return 2
        if contains(x, "Fat-free"):
            return 3
        return 1

    out["yogtype"] = out["Q65"].apply(map_yogtype)
    out["flvyogtype"] = out["Q286"].apply(map_flvyogtype)
    out["cheesetype"] = out["Q179"].apply(map_cheesetype)
    out["slddessingtype"] = out["Q156_0001"].apply(map_dressingtype)

    if "Q209" in out.columns and out["Q209"].notna().any():
        hsrc = "Q209"
    elif "height_in" in out.columns and out["height_in"].notna().any():
        hsrc = "height_in"
        warnings.append("Q209 (height) was missing. Please add a column for height in inches labeled Q209.")
    else:
        hsrc = None
        warnings.append("Missing Q209/height_in. Height-based outputs such as heightm, BMI, FFM, EA, and related variables could not be fully calculated.")

    if "Q210" in out.columns and out["Q210"].notna().any():
        wsrc = "Q210"
    elif "weight_kg" in out.columns and out["weight_kg"].notna().any():
        wsrc = "weight_kg"
        warnings.append("Q210 (weight) was missing. Please add a column for weight in lbs labeled Q10.")
    else:
        wsrc = None
        warnings.append("Missing Q210/weight_kg. Weight-based outputs such as weightkg, BMI, FFM, EEE, EA, and related variables could not be fully calculated.")

    if hsrc is not None:
        out["_height_raw"] = out[hsrc].apply(extract_first_numeric)
        out["heightm"] = out["_height_raw"] * 0.0254
    else:
        out["_height_raw"] = np.nan
        out["heightm"] = np.nan

    if wsrc is not None:
        weight_raw = out[wsrc].apply(extract_first_numeric)
        out["weightkg"] = weight_raw if wsrc == "weight_kg" else weight_raw / 2.2
    else:
        out["weightkg"] = np.nan

    out["bmi"] = out["weightkg"] / (out["heightm"] * out["heightm"])
    out["ismale"] = out["Q230"].map({"Female": 0, "Male": 1})
    out["gender"] = out["Q230"]
    out["age"] = pd.to_numeric(out["Q200"], errors="coerce")

    def run_values(x):
        s = "" if pd.isna(x) else str(x)
        mapping = [
            ("5:30", (5.5, 16)), ("6:00", (6.0, 14.5)), ("6:30", (6.5, 12.8)), ("7:00", (7.0, 12.3)),
            ("7:30", (7.5, 11.8)), ("8:00", (8.0, 11.8)), ("8:30", (8.5, 11.0)), ("9:00", (9.0, 10.5)),
        ]
        for key, value in mapping:
            if key in s:
                return value
        return (8.0, 11.8)

    run_info = out["Q213"].apply(run_values)
    out["runpace"] = [x[0] for x in run_info]
    out["runmets"] = [x[1] for x in run_info]
    out["miles_wk"] = pd.to_numeric(out["Q212"].apply(extract_first_numeric), errors="coerce").fillna(0)
    out["hrsrunning"] = (out["miles_wk"] * out["runpace"]) / 60

    def intensity_to_mets(x, high, moderate, low, default):
        s = "" if pd.isna(x) else str(x)
        if "High" in s:
            return high
        if "Moderate" in s:
            return moderate
        if "Low" in s:
            return low
        return default

    out["weightliftmets"] = out["Q215"].apply(lambda x: intensity_to_mets(x, 6, 5, 3.5, 5))
    out["aquajogmets"] = out["Q219"].apply(lambda x: intensity_to_mets(x, 9.8, 6.8, 4.8, 6.8))
    out["bikemets"] = out["Q224"].apply(lambda x: intensity_to_mets(x, 10, 8, 6.8, 8))
    out["ellipticalmets"] = out["Q225"].apply(lambda x: intensity_to_mets(x, 9, 7, 5, 7))

    for src, dest in zip(HOUR_VARS, ["weightlifthrs", "aquajoghrs", "bikehrs", "ellipticalhrs"]):
        out[dest] = out[src].apply(parse_hour_value)

    out["bodyfat"] = 1.2 * out["bmi"] + 0.23 * out["age"] - 10.8 * out["ismale"] - 5.4
    out["ffm"] = out["weightkg"] - out["weightkg"] * out["bodyfat"] * 0.01

    word_to_num = {word: i for i, word in enumerate(["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"], start=1)}
    out["mealsday"] = out["Q152"].map(word_to_num)
    out["snacksday"] = out["Q153"].map(word_to_num)
    out["fasting"] = out["Q154"].map({"No": 0, "Yes": 1})
    out["skip"] = out["Q155"].map({"No": 0, "Yes": 1})

    def vegetarian_flags(x):
        s = "" if pd.isna(x) else str(x)
        if "I follow a vegan diet" in s:
            return (1, 1)
        if "I follow a vegetarian diet" in s:
            return (1, 0)
        return (0, 0)

    vv = out["Q157"].apply(vegetarian_flags)
    out["vegetarian"] = [v[0] for v in vv]
    out["vegan"] = [v[1] for v in vv]
    out["restrict"] = np.where(
        (out["vegetarian"] == 1) | (out["vegan"] == 1),
        1,
        np.where((out["Q158"] == "Yes") & (out["Q232"] == "No"), 1, 0),
    )
    out["restrictallergy"] = np.where(out["Q232"] == "Yes", 1, 0)

    def housing_code(x):
        s = "" if pd.isna(x) else str(x)
        if "I live in student housing on campus" in s:
            return 1
        if "I live off campus (alone" in s:
            return 2
        if "I live off campus with one" in s:
            return 3
        if "Other" in s:
            return 4
        return np.nan

    def foodprep_code(x):
        s = "" if pd.isna(x) else str(x)
        if "A family member" in s:
            return 1
        if "I am" in s:
            return 2
        if "Campus" in s:
            return 3
        if "Another" in s:
            return 4
        return np.nan

    out["housing"] = out["Q240"].apply(housing_code)
    out["foodprep"] = out["Q241"].apply(foodprep_code)
    out["foodinsecure"] = np.where(out["Q245"].isin(["Often true", "Sometimes true"]), 1, 0)

    likert = {"Strongly Agree": 1, "Agree": 2, "Disagree": 3, "Strongly Disagree": 4}
    for src, dest in zip(["Q250", "Q251", "Q252", "Q253", "Q254"], ["percep1", "percep2", "percep3", "percep4", "percep5"]):
        out[dest] = out[src].map(likert)

    q165 = out["Q165"].fillna("").astype(str)
    q166 = out["Q166"].fillna("").astype(str)

    out["supp"] = np.where(
        ((q165 == "I do not take vitamins or minerals.") | (q165 == ".") | (q165 == ""))
        & ((q166 == "None") | (q166 == ".") | (q166 == "")),
        0,
        1,
    )

    def contains_flag(series: pd.Series, text: str) -> pd.Series:
        return series.str.contains(re.escape(text), case=False, na=False).astype(int)

    out["vitamin"] = contains_flag(q165, "Multivitamin")
    out["vitamind"] = contains_flag(q165, "Vitamin D supplement")
    out["iron"] = contains_flag(q165, "Iron")
    out["calcium"] = contains_flag(q165, "Calcium")
    out["caffeine"] = contains_flag(q166, "Caffeine")
    out["creatine"] = contains_flag(q166, "Creatine")
    out["prewrkout"] = contains_flag(q166, "Preworkout")
    out["wtgainer"] = contains_flag(q166, "gain")
    out["wtlosssupp"] = contains_flag(q166, "loss")
    out["aasupp"] = contains_flag(q166, "acids")
    out["herbotsupp"] = contains_flag(q166, "botanicals")

    df = df.fillna(0)
    
    o = out
    o["fruitkcal"] = (o["fruits"] * 60) + (o["driedfruit"] * 60) + (o["fruitjuice"] * 120 / 7)
    o["fruitcho"] = (o["fruits"] * 15) + (o["driedfruit"] * 15) + (o["fruitjuice"] * 30 / 7)
    o["fruitfiber"] = (o["fruits"] * 2) + (o["driedfruit"] * 2)
    o["fruit"] = (o["fruits"] / 2) + (o["driedfruit"] / 2) + (o["fruitjuice"] / 7)

    o["coconutwaterkcal"] = o["coconutwater"] * 45 / 7
    o["coconutwatercho"] = o["coconutwater"] * 10 / 7

    o["vegnskcal"] = (o["vegrlg"] * 25) + (o["vegother"] * 37.5) + ((o["tomsauc"] * 50) / 7) + ((o["tomjuice"] * 50) / 7)
    o["vegnscho"] = (o["vegrlg"] * 5) + (o["vegother"] * 7.5) + ((o["tomsauc"] * 10) / 7) + ((o["tomjuice"] * 10) / 7)
    o["vegnspro"] = (o["vegrlg"] * 2) + (o["vegother"] * 3) + ((o["tomsauc"] * 4) / 7) + ((o["tomjuice"] * 4) / 7)
    o["vegnsfiber"] = (o["vegrlg"] * 2.5) + (o["vegother"] * 4) + ((o["tomsauc"] * 4) / 7) + ((o["tomjuice"] * 4) / 7)
    o["nsveg"] = (o["vegrlg"] * 0.5) + (o["vegother"] * 1) + ((o["tomsauc"] * 1) / 7) + ((o["tomjuice"] * 1) / 7)

    o["grainkcal"] = (o["plainbrd"] * 80) + (o["bkdbrd"] * 125) + (o["crpast"] * 80) + (o["grnsotr"] * 125)
    o["graincho"] = (o["plainbrd"] * 15) + (o["bkdbrd"] * 15) + (o["crpast"] * 15) + (o["grnsotr"] * 15)
    o["grainpro"] = (o["plainbrd"] * 3) + (o["bkdbrd"] * 3) + (o["crpast"] * 3) + (o["grnsotr"] * 3)
    o["grainfat"] = (o["bkdbrd"] * 5) + (o["grnsotr"] * 5)
    o["grainfiber"] = (o["plainbrd"] * 1) + (o["bkdbrd"] * 1) + (o["crpast"] * 1) + (o["grnsotr"] * 1)
    o["grains"] = o["plainbrd"] + o["bkdbrd"] + o["crpast"] + o["grnsotr"]

    o["legumeskcal"] = (o["legumess"] * 100) / 7
    o["legumescho"] = (o["legumess"] * 15) / 7
    o["legumespro"] = (o["legumess"] * 6) / 7
    o["legumesfiber"] = (o["legumess"] * 5) / 7
    o["legumes"] = o["legumess"] * 0.14 / 2

    o["cornkcal"] = (o["corn"] * 80) / 7
    o["corncho"] = (o["corn"] * 15) / 7
    o["cornpro"] = (o["corn"] * 3) / 7
    o["cornfiber"] = o["corn"] * 1

    o["potatokcal"] = ((o["potatonf"] * 80) / 7) + ((o["potatofr"] * 125) / 7)
    o["potatocho"] = ((o["potatonf"] * 15) / 7) + ((o["potatofr"] * 15) / 7)
    o["potatopro"] = ((o["potatonf"] * 3) / 7) + ((o["potatofr"] * 3) / 7)
    o["potatofat"] = (o["potatofr"] * 5) / 7
    o["potatofiber"] = ((o["potatonf"] * 1) / 7) + ((o["potatofr"] * 1) / 7)
    o["potatototal"] = (o["potatonf"] + o["potatofr"]) * 0.14 / 2

    o["vegskcal"] = o["legumeskcal"] + o["cornkcal"] + o["potatokcal"]
    o["vegscho"] = o["legumescho"] + o["corncho"] + o["potatocho"]
    o["vegspro"] = o["legumespro"] + o["cornpro"] + o["potatopro"]
    o["vegsfat"] = o["potatofat"]
    o["vegsfiber"] = o["legumesfiber"] + o["cornfiber"] + o["potatofiber"]
    o["starchveg"] = (o["legumes"] + o["corn"] + o["potatonf"] + o["potatofr"]) * 0.14 / 2
    o["vegall"] = o["nsveg"] + o["starchveg"]

    o["meatpoultrykcal"] = (o["leanmeat"] * 135) / 7 + (o["fatmeat"] * 262.5) / 7
    o["meatpoultrypro"] = (o["leanmeat"] * 21) / 7 + (o["fatmeat"] * 21) / 7
    o["meatpoultryfat"] = (o["leanmeat"] * 4.5) / 7 + (o["fatmeat"] * 19.5) / 7

    o["fattyfishkcal"] = (o["ftyfish"] * 195) / 7
    o["fattyfishpro"] = (o["ftyfish"] * 21) / 7
    o["fattyfishfat"] = (o["ftyfish"] * 12) / 7

    o["eggskcal"] = (o["whegg"] * 70) / 7 + (o["eggwt"] * 20) / 7
    o["eggspro"] = (o["whegg"] * 6) / 7 + (o["eggwt"] * 4) / 7
    o["eggsfat"] = (o["whegg"] * 5) / 7

    o["fttyfish"] = (o["ftyfish"] * 0.143) / 3
    o["eggs"] = (o["whegg"] * 0.143) + (o["eggwt"] * 0.67) / 7
    o["mtpltry"] = ((o["leanmeat"] + o["fatmeat"]) * 0.143) / 3

    milk_specs = {
        1: (90, 12, 8, 1.5, 168, 34, 8, 0),
        2: (120, 12, 8, 5, 160, 26, 9, 3),
        3: (150, 12, 8, 8, 208, 26, 8, 8),
        4: (100, 8, 7, 4, 154, 24, 6, 4),
        5: (50, 5, 1, 3, 120, 23, 2, 3),
    }
    for code, (mk, mc, mp, mf, fk, fc, fp, ff) in milk_specs.items():
        mask = o["milktype"] == code
        o.loc[mask, "milkkcal"] = (o.loc[mask, "milk"] * mk) / 7
        o.loc[mask, "milkcho"] = (o.loc[mask, "milk"] * mc) / 7
        o.loc[mask, "milkpro"] = (o.loc[mask, "milk"] * mp) / 7
        o.loc[mask, "milkfat"] = (o.loc[mask, "milk"] * mf) / 7
        o.loc[mask, "flvmilkkcal"] = (o.loc[mask, "flvmilk"] * fk) / 7
        o.loc[mask, "flvmilkcho"] = (o.loc[mask, "flvmilk"] * fc) / 7
        o.loc[mask, "flvmilkpro"] = (o.loc[mask, "flvmilk"] * fp) / 7
        o.loc[mask, "flvmilkfat"] = (o.loc[mask, "flvmilk"] * ff) / 7

    yog_specs = {
        1: (120, 16, 11, 0), 2: (150, 17, 13, 4), 3: (150, 11, 9, 8),
        4: (162, 13, 6, 4), 5: (179, 10, 25, 5), 6: (238, 10, 22, 12),
    }
    for code, (k, c, p, f) in yog_specs.items():
        mask = o["yogtype"] == code
        o.loc[mask, "yogkcal"] = (o.loc[mask, "yogurt"] * k) / 7
        o.loc[mask, "yogcho"] = (o.loc[mask, "yogurt"] * c) / 7
        o.loc[mask, "yogpro"] = (o.loc[mask, "yogurt"] * p) / 7
        o.loc[mask, "yogfat"] = (o.loc[mask, "yogurt"] * f) / 7

    flvyog_specs = {
        1: (191, 42, 7, 0), 2: (208, 34, 12, 3), 3: (216, 36, 7, 4), 4: (233, 23, 21, 6), 5: (90, 12, 8, 0),
    }
    for code, (k, c, p, f) in flvyog_specs.items():
        mask = o["flvyogtype"] == code
        o.loc[mask, "flvyogkcal"] = (o.loc[mask, "flvyogurt"] * k) / 7
        o.loc[mask, "flvyogcho"] = (o.loc[mask, "flvyogurt"] * c) / 7
        o.loc[mask, "flvyogpro"] = (o.loc[mask, "flvyogurt"] * p) / 7
        o.loc[mask, "flvyogfat"] = (o.loc[mask, "flvyogurt"] * f) / 7

    cheese_specs = {1: (100, 7, 8, 0), 2: (75, 7, 5, 0), 3: (74, 3, 6, 3)}
    for code, (k, p, f, c) in cheese_specs.items():
        mask = o["cheesetype"] == code
        o.loc[mask, "cheesekcal"] = (o.loc[mask, "cheese"] * k) / 7
        o.loc[mask, "cheesepro"] = (o.loc[mask, "cheese"] * p) / 7
        o.loc[mask, "cheesefat"] = (o.loc[mask, "cheese"] * f) / 7
        o.loc[mask, "cheesecho"] = (o.loc[mask, "cheese"] * c) / 7

    o["cotcheesekcal"] = (o["cotcheese"] * 180) / 7
    o["cotcheesepro"] = (o["cotcheese"] * 24) / 7
    o["cotcheesefat"] = (o["cotcheese"] * 5) / 7
    o["cotcheesecho"] = (o["cotcheese"] * 10) / 7
    o["dairy"] = o["milk"] / 7 + o["flvmilk"] / 7 + o["yogurt"] / 7 + o["flvyogurt"] / 7 + o["cheese"] * 0.67 / 7 + o["cotcheese"] * 0.8 / 7

    dressing_specs = {1: (45, 0, 5), 2: (22.5, 0, 2.5), 3: (20, 5, 0)}
    for code, (k, c, f) in dressing_specs.items():
        mask = o["slddessingtype"] == code
        o.loc[mask, "slddrkcal"] = (o.loc[mask, "slddressing"] * k) / 7
        o.loc[mask, "slddrcho"] = (o.loc[mask, "slddressing"] * c) / 7
        o.loc[mask, "slddrfat"] = (o.loc[mask, "slddressing"] * f) / 7

    o["vegoilkcal"] = (o["vegoil"] * 135) / 7
    o["vegoilfat"] = (o["vegoil"] * 15) / 7
    o["nutbtrkcal"] = (o["nutbtr"] * 94) / 7
    o["nutbtrpro"] = (o["nutbtr"] * 4) / 7
    o["nutbtrfat"] = (o["nutbtr"] * 8) / 7
    o["nutbtrcho"] = (o["nutbtr"] * 3) / 7
    o["nutbtrfiber"] = (o["nutbtr"] * 1) / 7
    o["cocoilbtkcal"] = (o["cocoilbt"] * 120) / 7
    o["cocoilbtfat"] = (o["cocoilbt"] * 14) / 7
    o["butterkcal"] = (o["butter"] * 102) / 7
    o["butterfat"] = (o["butter"] * 12) / 7
    o["lardkcal"] = (o["lard"] * 115) / 7
    o["lardfat"] = (o["lard"] * 13) / 7
    o["srcrmkcal"] = (o["srcrm"] * 22.5) / 7
    o["srcrmfat"] = (o["srcrm"] * 2.5) / 7
    o["crmchskcal"] = (o["crmchs"] * 45) / 7
    o["crmchsfat"] = (o["crmchs"] * 5) / 7
    o["creamkcal"] = (o["cream"] * 45) / 7
    o["creamfat"] = (o["cream"] * 5) / 7
    o["mayokcal"] = (o["mayo"] * 94) / 7
    o["mayofat"] = (o["mayo"] * 10) / 7
    o["mrgrnekcal"] = (o["mrgrne"] * 103) / 7
    o["mrgrnefat"] = (o["mrgrne"] * 11) / 7
    o["hlfhlfkcal"] = (o["hlfhlf"] * 22.5) / 7
    o["hlfhlffat"] = (o["hlfhlf"] * 2.5) / 7
    o["oliveskcal"] = (o["olives"] * 10) / 7
    o["olivesfat"] = (o["olives"] * 1) / 7
    o["nutskcal"] = (o["nuts"] * 199) / 7
    o["nutscho"] = (o["nuts"] * 7.3) / 7
    o["nutspro"] = (o["nuts"] * 6.4) / 7
    o["nutsfat"] = (o["nuts"] * 17.5) / 7
    o["nutsfiber"] = (o["nuts"] * 2.1) / 7
    o["avocadokcal"] = (o["avocado"] * 96) / 7
    o["avocadocho"] = (o["avocado"] * 5) / 7
    o["avocadofat"] = (o["avocado"] * 9) / 7
    o["avocadofiber"] = (o["avocado"] * 3.9) / 7
    o["avocadopro"] = o["avocado"] * 1 / 7

    o["extrafatskcal"] = o["vegoilkcal"] + o["nutbtrkcal"] + o["cocoilbtkcal"] + o["butterkcal"] + o["lardkcal"] + o["srcrmkcal"] + o["crmchskcal"] + o["creamkcal"] + o["mayokcal"] + o["mrgrnekcal"] + o["hlfhlfkcal"] + o["oliveskcal"] + o["nutskcal"] + o["avocadokcal"]
    o["extrafatsfat"] = o["vegoilfat"] + o["nutbtrfat"] + o["cocoilbtfat"] + o["butterfat"] + o["lardfat"] + o["srcrmfat"] + o["crmchsfat"] + o["creamfat"] + o["mayofat"] + o["mrgrnefat"] + o["hlfhlffat"] + o["olivesfat"] + o["nutsfat"] + o["avocadofat"]
    o["extrafatscho"] = o["nutscho"] + o["avocadocho"] + o["nutbtrcho"]
    o["extrafatsfiber"] = o["nutsfiber"] + o["avocadofiber"] + o["nutbtrfiber"]
    o["extrafatspro"] = o["nutspro"] + o["nutbtrpro"] + o["avocadopro"]

    o["choccndykcal"] = (o["choccndy"] * 105) / 7
    o["choccndycho"] = (o["choccndy"] * 15) / 7
    o["choccndyfat"] = (o["choccndy"] * 5) / 7
    o["nonchccndykcal"] = (o["nonchccndy"] * 60) / 7
    o["nonchccndycho"] = (o["nonchccndy"] * 15) / 7
    o["icecrmkcal"] = (o["icecrm"] * 150) / 7
    o["icecrmcho"] = (o["icecrm"] * 15) / 7
    o["icecrmfat"] = (o["icecrm"] * 10) / 7
    o["froyokcal"] = (o["froyo"] * 105) / 7
    o["froyocho"] = (o["froyo"] * 15) / 7
    o["froyofat"] = (o["froyo"] * 5) / 7
    o["bkdgdkcal"] = (o["bkdgd"] * 105) / 7
    o["bkdgdcho"] = (o["bkdgd"] * 15) / 7
    o["bkdgdfat"] = (o["bkdgd"] * 5) / 7

    o["sweetskcal"] = o["choccndykcal"] + o["nonchccndykcal"] + o["icecrmkcal"] + o["froyokcal"] + o["bkdgdkcal"]
    o["sweetsfat"] = o["choccndyfat"] + o["icecrmfat"] + o["froyofat"] + o["bkdgdfat"]
    o["sweetscho"] = o["choccndycho"] + o["nonchccndycho"] + o["icecrmcho"] + o["froyocho"] + o["bkdgdcho"]

    o["swtbvgkcal"] = o["swtbvg"] * 120
    o["swtbvgcho"] = o["swtbvg"] * 30
    o["swttcfeekcal"] = o["swttcfee"] * 75
    o["swttcfeecho"] = o["swttcfee"] * 15
    o["swttcfeepro"] = o["swttcfee"] * 2
    o["swttcfeefat"] = o["swttcfee"] * 1.5
    o["nrgdrnkkcal"] = o["nrgdrnk"] * 110
    o["nrgdrnkcho"] = o["nrgdrnk"] * 29
    o["otrswtbvgkcal"] = o["otrswtbvg"] * 120
    o["otrswtbvgcho"] = o["otrswtbvg"] * 30
    o["chodrnkkcal"] = (o["chodrnk"] * 65) / 7
    o["chodrnkcho"] = (o["chodrnk"] * 15) / 7

    o["drinkskcal"] = o["swtbvgkcal"] + o["swttcfeekcal"] + o["otrswtbvgkcal"] + o["nrgdrnkkcal"] + o["chodrnkkcal"]
    o["drinkscho"] = o["swtbvgcho"] + o["swttcfeecho"] + o["otrswtbvgcho"] + o["nrgdrnkcho"] + o["chodrnkcho"]
    o["drinkspro"] = o["swttcfeepro"]
    o["drinksfat"] = o["swttcfeefat"]

    o["nrgbarkcal"] = (o["nrgbar"] * 225) / 7
    o["nrgbarcho"] = (o["nrgbar"] * 35) / 7
    o["nrgbarpro"] = (o["nrgbar"] * 10) / 7
    o["nrgbarfat"] = (o["nrgbar"] * 5) / 7
    o["nrgbarfiber"] = (o["nrgbar"] * 3) / 7

    o["probarkcal"] = (o["probar"] * 250) / 7
    o["probarcho"] = (o["probar"] * 30) / 7
    o["probarpro"] = (o["probar"] * 20) / 7
    o["probarfat"] = (o["probar"] * 7) / 7
    o["probarfiber"] = (o["probar"] * 2) / 7

    o["gelkcal"] = (o["gel"] * 100) / 7
    o["gelcho"] = (o["gel"] * 27) / 7

    o["barsgelskcal"] = o["nrgbarkcal"] + o["probarkcal"] + o["gelkcal"]
    o["barsgelscho"] = o["nrgbarcho"] + o["probarcho"] + o["gelcho"]
    o["barsgelspro"] = o["nrgbarpro"] + o["probarpro"]
    o["barsgelsfat"] = o["nrgbarfat"] + o["probarfat"]
    o["barsgelsfiber"] = o["nrgbarfiber"] + o["probarfiber"]
    o["gelchewwk"] = o["gel"]

    o["prodrnkkcal"] = (o["prodrnk"] * 286) / 7
    o["prodrnkcho"] = (o["prodrnk"] * 36) / 7
    o["prodrnkpro"] = (o["prodrnk"] * 20) / 7
    o["prodrnkfat"] = (o["prodrnk"] * 8) / 7
    o["prodrnkfiber"] = (o["prodrnk"] * 4) / 7

    o["nrgkcal"] = o["nrgbarkcal"] + o["probarkcal"] + o["gelkcal"] + o["prodrnkkcal"]
    o["nrgcho"] = o["nrgbarcho"] + o["probarcho"] + o["gelcho"] + o["prodrnkcho"]
    o["nrgpro"] = o["nrgbarpro"] + o["probarpro"] + o["prodrnkpro"]
    o["nrgfat"] = o["nrgbarfat"] + o["probarfat"] + o["prodrnkfat"]
    o["nrgfiber"] = o["nrgbarfiber"] + o["probarfiber"] + o["prodrnkfiber"]

    o["swtbvgtotal"] = (o["swtbvg"] + o["swttcfee"] + o["otrswtbvg"] + o["nrgdrnk"] + o["chodrnk"]) * 8 / 7
    o["otrbevtotal"] = (o["zerocaldrnk"] + o["unswttcfee"] + o["water"]) * 8
    o["prodrnktotal"] = (o["prodrnk"] * 11) / 7
    o["prodrnkwk"] = o["prodrnk"]

    o["fruitjuicetotal"] = o["fruitjuice"] * 8 / 7
    o["coconutwatertotal"] = o["coconutwater"] * 8 / 7
    o["milktotal"] = (o["milk"] + o["flvmilk"]) * 8 / 7
    o["vegjuicetotal"] = (o["tomjuice"] * 8) / 7
    o["fluids"] = o["swtbvgtotal"] + o["otrbevtotal"] + o["prodrnktotal"] + o["fruitjuicetotal"] + o["coconutwatertotal"] + o["milktotal"] + o["vegjuicetotal"]

    o["alcoholkcal"] = (o["beer"] * 160 + o["spirits"] * 100 + o["mixed"] * 160 + o["wine"] * 100) / 7
    o["alcoholcho"] = (o["beer"] * 15 + o["mixed"] * 15) / 7

    o["profoods"] = (o["leanmeat"] * 0.143 / 3) + (o["fatmeat"] * 0.143 / 3) + ((o["ftyfish"] * 0.143) / 3) + (o["whegg"] * 0.143) + (o["eggwt"] * 0.67) / 7 + (o["legumess"] * 0.143)

    o["kcaltotal"] = o["fruitkcal"] + o["vegnskcal"] + o["grainkcal"] + o["vegskcal"] + o["meatpoultrykcal"] + o["fattyfishkcal"] + o["eggskcal"] + o["milkkcal"] + o["flvmilkkcal"] + o["yogkcal"] + o["flvyogkcal"] + o["cheesekcal"] + o["cotcheesekcal"] + o["slddrkcal"] + o["extrafatskcal"] + o["sweetskcal"] + o["nrgkcal"] + o["drinkskcal"] + o["coconutwaterkcal"] + o["alcoholkcal"]

    o["cho"] = o["fruitcho"] + o["vegnscho"] + o["graincho"] + o["vegscho"] + o["milkcho"] + o["flvmilkcho"] + o["yogcho"] + o["flvyogcho"] + o["cheesecho"] + o["slddrcho"] + o["extrafatscho"] + o["sweetscho"] + o["nrgcho"] + o["drinkscho"] + o["coconutwatercho"] + o["alcoholcho"]
    o["chokg"] = o["cho"] / o["weightkg"]

    o["fat"] = o["grainfat"] + o["vegsfat"] + o["meatpoultryfat"] + o["fattyfishfat"] + o["eggsfat"] + o["milkfat"] + o["flvmilkfat"] + o["yogfat"] + o["flvyogfat"] + o["cheesefat"] + o["cotcheesefat"] + o["slddrfat"] + o["extrafatsfat"] + o["sweetsfat"] + o["drinksfat"] + o["nrgfat"]
    o["fatkg"] = o["fat"] / o["weightkg"]

    o["pro"] = o["vegnspro"] + o["grainpro"] + o["vegspro"] + o["meatpoultrypro"] + o["fattyfishpro"] + o["eggspro"] + o["milkpro"] + o["flvmilkpro"] + o["yogpro"] + o["flvyogpro"] + o["cheesepro"] + o["cotcheesepro"] + o["extrafatspro"] + o["barsgelspro"] + o["drinkspro"] + o["nrgpro"]
    o["prokg"] = o["pro"] / o["weightkg"]

    o["fiber"] = o["fruitfiber"] + o["vegnsfiber"] + o["grainfiber"] + o["vegsfiber"] + o["extrafatsfiber"] + o["nrgfiber"]

    o["runkcal"] = (o["weightkg"] * o["runmets"] * o["hrsrunning"]) / 7
    o["weightliftkcal"] = (o["weightkg"] * o["weightliftmets"] * o["weightlifthrs"]) / 7
    o["aquajogkcal"] = (o["weightkg"] * o["aquajogmets"] * o["aquajoghrs"]) / 7
    o["bikekcal"] = (o["weightkg"] * o["bikemets"] * o["bikehrs"]) / 7
    o["ellipticalkcal"] = (o["weightkg"] * o["ellipticalmets"] * o["ellipticalhrs"]) / 7

    o["eee"] = o["runkcal"] + o["weightliftkcal"] + o["aquajogkcal"] + o["bikekcal"] + o["ellipticalkcal"]
    o["ea"] = (o["kcaltotal"] - o["eee"]) / o["ffm"]
    o.loc[o["kcaltotal"] == 0, "ea"] = np.nan

    o["ei"] = o["kcaltotal"]
    o.loc[o["ei"] == 0, "ei"] = np.nan
    o["ei_kg"] = o["ei"] / o["weightkg"]

    o["lowea_clinical"] = np.nan
    o["lowea_subclinical"] = np.nan
    male_mask = (o["ismale"] == 1) & o["ea"].notna()
    female_mask = (o["ismale"] == 0) & o["ea"].notna()

    o.loc[male_mask, "lowea_clinical"] = np.where((o.loc[male_mask, "ea"] > 0) & (o.loc[male_mask, "ea"] < 15), 1, 0)
    o.loc[male_mask, "lowea_subclinical"] = np.where((o.loc[male_mask, "ea"] >= 15) & (o.loc[male_mask, "ea"] < 30), 1, 0)
    o.loc[female_mask, "lowea_clinical"] = np.where((o.loc[female_mask, "ea"] > 0) & (o.loc[female_mask, "ea"] < 30), 1, 0)
    o.loc[female_mask, "lowea_subclinical"] = np.where((o.loc[female_mask, "ea"] >= 30) & (o.loc[female_mask, "ea"] < 45), 1, 0)

    o["barswk"] = o["nrgbar"]
    o["probarswk"] = o["probar"]
    o["chodrink"] = o["chodrnk"] * 8 / 7
    o["caffdrnk"] = o["nrgdrnk"] * 8 / 7
    o["id"] = o["Q182"]

    all_food_missing = out[FOOD_COUNT_VARS].fillna(0).sum(axis=1) == 0
    if all_food_missing.any():
        for col in REDCAP_KEEP:
            if col in o.columns:
                o.loc[all_food_missing, col] = np.nan

    redcap_df = o[[col for col in REDCAP_KEEP if col in o.columns]].copy()
    return o.copy(), redcap_df, warnings, df


def dataframe_to_excel_bytes(sheets: List[Tuple[str, pd.DataFrame]]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, frame in sheets:
            frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    output.seek(0)
    return output.getvalue()


st.title("Nutrition FFQ Processor")
st.write(
    "Upload a Qualtrics export and this app will process it into the REDCap nutrition dataset from the SAS code. "
    "Alcohol is included again. If alcohol variables are missing, they are set to 0. "
    "If Q209 (height in inches)/Q210 (weight in lbs) are missing, the app warns you. Add these columns labeled Q209 and Q210."
)

uploaded_file = st.file_uploader("Upload Qualtrics file", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        raw_df = load_input_file(uploaded_file)
        full_df, redcap_df, warnings_list, cleaned_input = process_nutrition_data(raw_df)
    except Exception as exc:
        st.error(f"The file could not be processed: {exc}")
        st.stop()

    st.success(f"Processed {len(redcap_df)} response(s).")

    if warnings_list:
        for warning in warnings_list:
            st.warning(warning)

    st.subheader("Input check")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows in uploaded file", len(raw_df))
    c2.metric("Rows after Qualtrics cleanup", len(cleaned_input))
    c3.metric("Rows in REDCap output", len(redcap_df))

    with st.expander("Preview cleaned input"):
        st.dataframe(cleaned_input.head(10), use_container_width=True)

    st.subheader("REDCap nutrition output")
    st.dataframe(redcap_df, use_container_width=True)

    st.subheader("Downloads")
    redcap_csv = redcap_df.to_csv(index=False).encode("utf-8")
    full_csv = full_df.to_csv(index=False).encode("utf-8")
    workbook = dataframe_to_excel_bytes([
        ("redcapnutrition", redcap_df),
        ("allnutrition", full_df),
    ])

    d1, d2, d3 = st.columns(3)
    d1.download_button(
        "Download redcapnutrition.csv",
        data=redcap_csv,
        file_name="redcapnutrition.csv",
        mime="text/csv",
    )
    d2.download_button(
        "Download allnutrition.csv",
        data=full_csv,
        file_name="allnutrition.csv",
        mime="text/csv",
    )
    d3.download_button(
        "Download Excel workbook",
        data=workbook,
        file_name="nutrition_outputs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
