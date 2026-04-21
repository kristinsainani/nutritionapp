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

    required_cols = [
        "Q10","Q11","Q12","Q149","Q146","Q1","Q150","Q24","Q165_0001","Q23","Q148","Q161_0001","Q162_0001","Q163","Q164","Q27",
        "Q28","Q29","Q177","Q178","Q33","Q169","Q170","Q168","Q171","Q35","Q261","Q262","Q263","Q264","Q265","Q266","Q267","Q268",
        "Q26","Q270","Q271","Q160_0001","Q158_0001","Q134","Q42","Q61","Q62","Q63","Q43","Q60","Q278","Q279","Q280","Q276","Q257",
        "Q125","Q281","Q282","Q285","Q284","Q273","Q272","Q52","Q269","Q289","Q290","Q291","Q292",
        "Q64","Q65","Q286","Q179","Q156_0001","Q209","Q210","Q230","Q200","Q213","Q212","Q215","Q219","Q224","Q225",
        "Q70","Q218","Q221","Q223","Q152","Q153","Q154","Q155","Q157","Q158","Q232","Q240","Q241","Q245",
        "Q250","Q251","Q252","Q253","Q254","Q165","Q166"
    ]

    df = clean_missing_strings(df)
    df = ensure_columns(df, required_cols)

    food_vars = [
        "Q10","Q11","Q12","Q149","Q146","Q1","Q150","Q24","Q165_0001","Q23","Q148","Q161_0001","Q162_0001","Q163","Q164","Q27",
        "Q28","Q29","Q177","Q178","Q33","Q169","Q170","Q168","Q171","Q35","Q261","Q262","Q263","Q264","Q265","Q266","Q267","Q268",
        "Q26","Q270","Q271","Q160_0001","Q158_0001","Q134","Q42","Q61","Q62","Q63","Q43","Q60","Q278","Q279","Q280","Q276","Q257",
        "Q125","Q281","Q282","Q285","Q284","Q273","Q272","Q52","Q269","Q289","Q290","Q291","Q292"
    ]

    for col in food_vars:
        df[col] = df[col].apply(convert_food_frequency)

    df["fruits"] = pd.to_numeric(df["Q10"], errors="coerce").fillna(0)
    df["driedfruit"] = pd.to_numeric(df["Q11"], errors="coerce").fillna(0)
    df["fruitjuice"] = pd.to_numeric(df["Q12"], errors="coerce").fillna(0)
    df["vegrlg"] = pd.to_numeric(df["Q149"], errors="coerce").fillna(0)
    df["vegother"] = pd.to_numeric(df["Q146"], errors="coerce").fillna(0)
    df["TomSauc"] = pd.to_numeric(df["Q1"], errors="coerce").fillna(0)
    df["TomJuice"] = pd.to_numeric(df["Q150"], errors="coerce").fillna(0)
    df["plainbrd"] = pd.to_numeric(df["Q24"], errors="coerce").fillna(0)
    df["BkdBrd"] = pd.to_numeric(df["Q165_0001"], errors="coerce").fillna(0)
    df["CRPast"] = pd.to_numeric(df["Q23"], errors="coerce").fillna(0)
    df["GrnsOtr"] = pd.to_numeric(df["Q148"], errors="coerce").fillna(0)
    df["Legumess"] = pd.to_numeric(df["Q161_0001"], errors="coerce").fillna(0)
    df["Corn"] = pd.to_numeric(df["Q162_0001"], errors="coerce").fillna(0)
    df["PotatoNF"] = pd.to_numeric(df["Q163"], errors="coerce").fillna(0)
    df["PotatoFr"] = pd.to_numeric(df["Q164"], errors="coerce").fillna(0)
    df["LeanMeat"] = pd.to_numeric(df["Q27"], errors="coerce").fillna(0)
    df["FatMeat"] = pd.to_numeric(df["Q28"], errors="coerce").fillna(0)
    df["FtyFish"] = pd.to_numeric(df["Q29"], errors="coerce").fillna(0)
    df["WhEgg"] = pd.to_numeric(df["Q177"], errors="coerce").fillna(0)
    df["EggWt"] = pd.to_numeric(df["Q178"], errors="coerce").fillna(0)
    df["milk"] = pd.to_numeric(df["Q33"], errors="coerce").fillna(0)
    df["FlvMilk"] = pd.to_numeric(df["Q169"], errors="coerce").fillna(0)
    df["Yogurt"] = pd.to_numeric(df["Q170"], errors="coerce").fillna(0)
    df["FlvYogurt"] = pd.to_numeric(df["Q168"], errors="coerce").fillna(0)
    df["cheese"] = pd.to_numeric(df["Q171"], errors="coerce").fillna(0)
    df["cotcheese"] = pd.to_numeric(df["Q35"], errors="coerce").fillna(0)
    df["vegoil"] = pd.to_numeric(df["Q261"], errors="coerce").fillna(0)
    df["nutbtr"] = pd.to_numeric(df["Q262"], errors="coerce").fillna(0)
    df["CocOilBt"] = pd.to_numeric(df["Q263"], errors="coerce").fillna(0)
    df["Butter"] = pd.to_numeric(df["Q264"], errors="coerce").fillna(0)
    df["lard"] = pd.to_numeric(df["Q265"], errors="coerce").fillna(0)
    df["SrCrm"] = pd.to_numeric(df["Q266"], errors="coerce").fillna(0)
    df["CrmChs"] = pd.to_numeric(df["Q267"], errors="coerce").fillna(0)
    df["Cream"] = pd.to_numeric(df["Q268"], errors="coerce").fillna(0)
    df["Mayo"] = pd.to_numeric(df["Q269"], errors="coerce").fillna(0)
    df["Mrgrne"] = pd.to_numeric(df["Q270"], errors="coerce").fillna(0)
    df["HlfHlf"] = pd.to_numeric(df["Q271"], errors="coerce").fillna(0)
    df["olives"] = pd.to_numeric(df["Q160_0001"], errors="coerce").fillna(0)
    df["nuts"] = pd.to_numeric(df["Q158_0001"], errors="coerce").fillna(0)
    df["avocado"] = pd.to_numeric(df["Q134"], errors="coerce").fillna(0)
    df["ChocCndy"] = pd.to_numeric(df["Q42"], errors="coerce").fillna(0)
    df["NonChcCndy"] = pd.to_numeric(df["Q61"], errors="coerce").fillna(0)
    df["IceCrm"] = pd.to_numeric(df["Q62"], errors="coerce").fillna(0)
    df["FroYo"] = pd.to_numeric(df["Q63"], errors="coerce").fillna(0)
    df["BkdGd"] = pd.to_numeric(df["Q43"], errors="coerce").fillna(0)
    df["SwtBvg"] = pd.to_numeric(df["Q60"], errors="coerce").fillna(0)
    df["SwtTCfee"] = pd.to_numeric(df["Q278"], errors="coerce").fillna(0)
    df["OtrSwtBvg"] = pd.to_numeric(df["Q280"], errors="coerce").fillna(0)
    df["NrgDrnk"] = pd.to_numeric(df["Q279"], errors="coerce").fillna(0)
    df["coconutwater"] = pd.to_numeric(df["Q276"], errors="coerce").fillna(0)
    df["slddressing"] = pd.to_numeric(df["Q257"], errors="coerce").fillna(0)
    df["nrgbar"] = pd.to_numeric(df["Q125"], errors="coerce").fillna(0)
    df["probar"] = pd.to_numeric(df["Q281"], errors="coerce").fillna(0)
    df["chodrnk"] = pd.to_numeric(df["Q282"], errors="coerce").fillna(0)
    df["gel"] = pd.to_numeric(df["Q285"], errors="coerce").fillna(0)
    df["prodrnk"] = pd.to_numeric(df["Q284"], errors="coerce").fillna(0)
    df["zerocaldrnk"] = pd.to_numeric(df["Q273"], errors="coerce").fillna(0)
    df["unSwtTCfee"] = pd.to_numeric(df["Q272"], errors="coerce").fillna(0)
    df["water"] = pd.to_numeric(df["Q52"], errors="coerce").fillna(0)
    df["beer"] = pd.to_numeric(df["Q289"], errors="coerce").fillna(0)
    df["spirits"] = pd.to_numeric(df["Q290"], errors="coerce").fillna(0)
    df["mixed"] = pd.to_numeric(df["Q291"], errors="coerce").fillna(0)
    df["wine"] = pd.to_numeric(df["Q292"], errors="coerce").fillna(0)

    df["milktype"] = np.nan
    df.loc[df["Q64"].str.contains("Non fat", na=False), "milktype"] = 1
    df.loc[df["Q64"].str.contains("Low fat", na=False), "milktype"] = 2
    df.loc[df["Q64"].str.contains("Regular", na=False), "milktype"] = 3
    df.loc[df["Q64"].str.contains("Non-dairy \\[soy milk\\]", regex=True, na=False), "milktype"] = 4
    df.loc[df["Q64"].str.contains("Non-dairy \\[almond milk,", regex=True, na=False), "milktype"] = 5
    df["milktype"] = df["milktype"].fillna(2)

    df["yogtype"] = np.nan
    df.loc[df["Q65"].str.contains("Non fat yogurt", na=False), "yogtype"] = 1
    df.loc[df["Q65"].str.contains("Low fat yogurt", na=False), "yogtype"] = 2
    df.loc[df["Q65"].str.contains("Regular \\(full-fat\\) yogurt", regex=True, na=False), "yogtype"] = 3
    df.loc[df["Q65"].str.contains("Non-dairy yogurt", na=False), "yogtype"] = 4
    df.loc[df["Q65"].str.contains("Greek yogurt \\(non fat", regex=True, na=False), "yogtype"] = 5
    df.loc[df["Q65"].str.contains("Greek yogurt \\(regular", regex=True, na=False), "yogtype"] = 6
    df["yogtype"] = df["yogtype"].fillna(2)

    df["flvyogtype"] = np.nan
    df.loc[df["Q286"].str.contains("Non fat yogurt", na=False), "flvyogtype"] = 1
    df.loc[df["Q286"].str.contains("Low fat yogurt", na=False), "flvyogtype"] = 2
    df.loc[df["Q286"].str.contains("Non-dairy yogurt", na=False), "flvyogtype"] = 3
    df.loc[df["Q286"].str.contains("Greek yogurt", na=False), "flvyogtype"] = 4
    df.loc[df["Q286"].str.contains('Non fat "no sugar added" or "diet" yogurt', regex=False, na=False), "flvyogtype"] = 5
    df["flvyogtype"] = df["flvyogtype"].fillna(2)

    df["cheesetype"] = np.nan
    df.loc[df["Q179"].str.contains("Regular dairy cheese", na=False), "cheesetype"] = 1
    df.loc[df["Q179"].str.contains("Reduced fat or light", na=False), "cheesetype"] = 2
    df.loc[df["Q179"].str.contains("Non-dairy cheese", na=False), "cheesetype"] = 3
    df["cheesetype"] = df["cheesetype"].fillna(1)

    df["slddessingtype"] = np.nan
    df.loc[df["Q156_0001"].str.contains("Regular", na=False), "slddessingtype"] = 1
    df.loc[df["Q156_0001"].str.contains("Reduced-fat", na=False), "slddessingtype"] = 2
    df.loc[df["Q156_0001"].str.contains("Fat-free", na=False), "slddessingtype"] = 3
    df["slddessingtype"] = df["slddessingtype"].fillna(1)

    df["Q209"] = df["Q209"].apply(first_numeric_from_string)
    df["Q210"] = df["Q210"].apply(first_numeric_from_string)
    df["Q209"] = pd.to_numeric(df["Q209"], errors="coerce")
    df["Q210"] = pd.to_numeric(df["Q210"], errors="coerce")

    df["weightkg"] = df["Q210"] / 2.2
    df["heightm"] = df["Q209"] * 0.0254
    df["bmi"] = df["weightkg"] / (df["heightm"] * df["heightm"])

    df["ismale"] = np.nan
    df.loc[df["Q230"] == "Female", "ismale"] = 0
    df.loc[df["Q230"] == "Male", "ismale"] = 1
    df["gender"] = df["Q230"]
    df["age"] = pd.to_numeric(df["Q200"], errors="coerce").fillna(0)

    df["runpace"] = np.nan
    df["runMETS"] = np.nan
    df.loc[df["Q213"].str.contains("5:30", na=False), ["runpace", "runMETS"]] = [5.5, 16]
    df.loc[df["Q213"].str.contains("6:00", na=False), ["runpace", "runMETS"]] = [6, 14.5]
    df.loc[df["Q213"].str.contains("6:30", na=False), ["runpace", "runMETS"]] = [6.5, 12.8]
    df.loc[df["Q213"].str.contains("7:00", na=False), ["runpace", "runMETS"]] = [7, 12.3]
    df.loc[df["Q213"].str.contains("7:30", na=False), ["runpace", "runMETS"]] = [7.5, 11.8]
    df.loc[df["Q213"].str.contains("8:00", na=False), ["runpace", "runMETS"]] = [8, 11.8]
    df.loc[df["Q213"].str.contains("8:30", na=False), ["runpace", "runMETS"]] = [8.5, 11]
    df.loc[df["Q213"].str.contains("9:00", na=False), ["runpace", "runMETS"]] = [9, 10.5]

    df["miles_wk"] = pd.to_numeric(df["Q212"], errors="coerce")
    df["miles_wk"] = df["miles_wk"].fillna(0)

    df["runpace"] = df["runpace"].fillna(8)
    df["runMETS"] = df["runMETS"].fillna(11.8)
    df["hrsrunning"] = (df["miles_wk"] * df["runpace"]) / 60

    df["weightliftMETS"] = np.nan
    df.loc[df["Q215"].str.contains("High", na=False), "weightliftMETS"] = 6
    df.loc[df["Q215"].str.contains("Moderate", na=False), "weightliftMETS"] = 5
    df.loc[df["Q215"].str.contains("Low", na=False), "weightliftMETS"] = 3.5
    df["weightliftMETS"] = df["weightliftMETS"].fillna(5)

    df["aquajogMETS"] = np.nan
    df.loc[df["Q219"].str.contains("High", na=False), "aquajogMETS"] = 9.8
    df.loc[df["Q219"].str.contains("Moderate", na=False), "aquajogMETS"] = 6.8
    df.loc[df["Q219"].str.contains("Low", na=False), "aquajogMETS"] = 4.8
    df["aquajogMETS"] = df["aquajogMETS"].fillna(6.8)

    df["bikeMETS"] = np.nan
    df.loc[df["Q224"].str.contains("High", na=False), "bikeMETS"] = 10
    df.loc[df["Q224"].str.contains("Moderate", na=False), "bikeMETS"] = 8
    df.loc[df["Q224"].str.contains("Low", na=False), "bikeMETS"] = 6.8
    df["bikeMETS"] = df["bikeMETS"].fillna(8)

    df["ellipticalMETS"] = np.nan
    df.loc[df["Q225"].str.contains("High", na=False), "ellipticalMETS"] = 9
    df.loc[df["Q225"].str.contains("Moderate", na=False), "ellipticalMETS"] = 7
    df.loc[df["Q225"].str.contains("Low", na=False), "ellipticalMETS"] = 5
    df["ellipticalMETS"] = df["ellipticalMETS"].fillna(7)

    for col in ["Q70", "Q218", "Q221", "Q223"]:
        df[col] = df[col].apply(convert_hours_text)

    df["weightlifthrs"] = pd.to_numeric(df["Q70"], errors="coerce").fillna(0)
    df["aquajoghrs"] = pd.to_numeric(df["Q218"], errors="coerce").fillna(0)
    df["bikehrs"] = pd.to_numeric(df["Q221"], errors="coerce").fillna(0)
    df["ellipticalhrs"] = pd.to_numeric(df["Q223"], errors="coerce").fillna(0)

    df["BodyFat"] = 1.2 * df["bmi"] + 0.23 * df["age"] - 10.8 * df["ismale"] - 5.4
    df["FFM"] = df["weightkg"] - df["weightkg"] * df["BodyFat"] * 0.01

    meals_map = {
        "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5,
        "Six": 6, "Seven": 7, "Eight": 8, "Nine": 9, "Ten": 10
    }
    df["Mealsday"] = df["Q152"].map(meals_map)
    df["SnacksDay"] = df["Q153"].map(meals_map)

    df["Fasting"] = np.nan
    df.loc[df["Q154"] == "No", "Fasting"] = 0
    df.loc[df["Q154"] == "Yes", "Fasting"] = 1

    df["Skip"] = np.nan
    df.loc[df["Q155"] == "No", "Skip"] = 0
    df.loc[df["Q155"] == "Yes", "Skip"] = 1

    df["Vegetarian"] = np.nan
    df["Vegan"] = np.nan
    mask_other = df["Q157"].str.contains("Other \\(please describe\\)", regex=True, na=False)
    mask_none = df["Q157"].str.contains("I do not follow", na=False)
    mask_veg = df["Q157"].str.contains("I follow a vegetarian diet", na=False)
    mask_vegan = df["Q157"].str.contains("I follow a vegan diet", na=False)

    df.loc[mask_other | mask_none, ["Vegetarian", "Vegan"]] = [0, 0]
    df.loc[mask_veg, ["Vegetarian", "Vegan"]] = [1, 0]
    df.loc[mask_vegan, ["Vegetarian", "Vegan"]] = [1, 1]

    df["Restrict"] = 0
    df.loc[(df["Vegetarian"] == 1) | (df["Vegan"] == 1), "Restrict"] = 1
    df.loc[(df["Q158"] == "Yes") & (df["Q232"] == "No"), "Restrict"] = 1

    df["RestrictAllergy"] = 0
    df.loc[df["Q232"] == "Yes", "RestrictAllergy"] = 1

    df["Housing"] = np.nan
    df.loc[df["Q240"].str.contains("I live in student housing on campus", na=False), "Housing"] = 1
    df.loc[df["Q240"].str.contains("I live off campus \\(alone", regex=True, na=False), "Housing"] = 2
    df.loc[df["Q240"].str.contains("I live off campus with one", na=False), "Housing"] = 3
    df.loc[df["Q240"].str.contains("Other", na=False), "Housing"] = 4

    df["FoodPrep"] = np.nan
    df.loc[df["Q241"].str.contains("A family member", na=False), "FoodPrep"] = 1
    df.loc[df["Q241"].str.contains("I am", na=False), "FoodPrep"] = 2
    df.loc[df["Q241"].str.contains("Campus", na=False), "FoodPrep"] = 3
    df.loc[df["Q241"].str.contains("Another", na=False), "FoodPrep"] = 4

    df["FoodInsecure"] = 0
    df.loc[(df["Q245"] == "Often true") | (df["Q245"] == "Sometimes true"), "FoodInsecure"] = 1

    df["supp"] = np.where(
        ((df["Q165"] == "I do not take vitamins or minerals.") | (df["Q165"] == ".")) &
        ((df["Q166"] == "None") | (df["Q166"] == ".")),
        0,
        1
    )

    df["vitamin"] = np.where(df["Q165"].str.contains("Multivitamin", na=False), 1, 0)
    df["vitamind"] = np.where(df["Q165"].str.contains("Vitamin D supplement", na=False), 1, 0)
    df["iron"] = np.where(df["Q165"].str.contains("Iron", na=False), 1, 0)
    df["calcium"] = np.where(df["Q165"].str.contains("Calcium", na=False), 1, 0)
    df["caffeine"] = np.where(df["Q166"].str.contains("Caffeine", na=False), 1, 0)
    df["creatine"] = np.where(df["Q166"].str.contains("Creatine", na=False), 1, 0)
    df["prewrkout"] = np.where(df["Q166"].str.contains("Preworkout", na=False), 1, 0)
    df["WtGainer"] = np.where(df["Q166"].str.contains("gain", na=False), 1, 0)
    df["WtLosssupp"] = np.where(df["Q166"].str.contains("loss", na=False), 1, 0)
    df["AAsupp"] = np.where(df["Q166"].str.contains("acids", na=False), 1, 0)
    df["HerBotSupp"] = np.where(df["Q166"].str.contains("botanicals", na=False), 1, 0)

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

    st.success("Chunk 1 complete: nutrition1 created from the first SAS DATA step.")
    st.write("nutrition1 preview")
    st.dataframe(nutrition1.head())

    nutrition1_csv = nutrition1.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download nutrition1.csv",
        data=nutrition1_csv,
        file_name="nutrition1.csv",
        mime="text/csv"
    )

    nutrition1_xlsx = to_excel_bytes({"nutrition1": nutrition1})
    st.download_button(
        "Download nutrition1.xlsx",
        data=nutrition1_xlsx,
        file_name="nutrition1.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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

    df["total_grains"] = (
        df["plainbrd"] + df["BkdBrd"] + df["CRPast"] + df["GrnsOtr"]
    )

    df["total_protein"] = (
        df["LeanMeat"] + df["FatMeat"] + df["FtyFish"] +
        df["WhEgg"] + df["EggWt"]
    )

    df["total_dairy"] = (
        df["milk"] + df["FlvMilk"] + df["Yogurt"] +
        df["FlvYogurt"] + df["cheese"] + df["cotcheese"]
    )

    df["total_fat_sources"] = (
        df["vegoil"] + df["nutbtr"] + df["CocOilBt"] + df["Butter"] +
        df["lard"] + df["SrCrm"] + df["CrmChs"] + df["Cream"] +
        df["Mayo"] + df["Mrgrne"] + df["HlfHlf"] +
        df["olives"] + df["nuts"] + df["avocado"]
    )

    df["total_sweets"] = (
        df["ChocCndy"] + df["NonChcCndy"] + df["IceCrm"] +
        df["FroYo"] + df["BkdGd"]
    )

    df["total_sweet_bev"] = (
        df["SwtBvg"] + df["SwtTCfee"] + df["OtrSwtBvg"] + df["NrgDrnk"]
    )

    df["total_beverages"] = (
        df["total_sweet_bev"] +
        df["coconutwater"] + df["zerocaldrnk"] +
        df["unSwtTCfee"] + df["water"]
    )

    df["total_alcohol"] = (
        df["beer"] + df["spirits"] + df["mixed"] + df["wine"]
    )

    df["total_sports_nutrition"] = (
        df["nrgbar"] + df["probar"] + df["chodrnk"] +
        df["gel"] + df["prodrnk"]
    )

    # -------------------------
    # DIET QUALITY / PATTERNS
    # -------------------------
    df["plant_foods"] = df["total_fruit"] + df["total_veg"] + df["nuts"] + df["Legumess"]
    df["animal_foods"] = df["total_protein"] + df["total_dairy"]

    df["ultra_processed"] = (
        df["total_sweets"] +
        df["total_sweet_bev"] +
        df["prodrnk"] +
        df["gel"]
    )

    # -------------------------
    # ACTIVITY ENERGY (METS)
    # -------------------------
    df["run_MET_min"] = df["hrsrunning"] * df["runMETS"] * 60
    df["lift_MET_min"] = df["weightlifthrs"] * df["weightliftMETS"] * 60
    df["bike_MET_min"] = df["bikehrs"] * df["bikeMETS"] * 60
    df["elliptical_MET_min"] = df["ellipticalhrs"] * df["ellipticalMETS"] * 60
    df["aquajog_MET_min"] = df["aquajoghrs"] * df["aquajogMETS"] * 60

    df["total_MET_min"] = (
        df["run_MET_min"] +
        df["lift_MET_min"] +
        df["bike_MET_min"] +
        df["elliptical_MET_min"] +
        df["aquajog_MET_min"]
    )

    # -------------------------
    # ENERGY NEED ESTIMATE (very literal SAS-style)
    # -------------------------
    df["est_cal_need"] = (
        22 * df["FFM"] + (df["total_MET_min"] / 1440) * df["FFM"]
    )

    # -------------------------
    # FINAL FLAGS
    # -------------------------
    df["low_energy_flag"] = np.where(
        df["est_cal_need"] > 0,
        np.where(df["total_sports_nutrition"] < (0.1 * df["est_cal_need"]), 1, 0),
        0
    )

    df["high_sugar_flag"] = np.where(df["total_sweet_bev"] > 7, 1, 0)

    df["low_fruit_veg_flag"] = np.where(
        (df["total_fruit"] + df["total_veg"]) < 14,
        1, 0
    )

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
