import io
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Nutrition Survey Processor', layout='wide')

SERVING_VARS = [
    'Q10','Q11','Q12','Q149','Q146','Q1','Q150','Q24','Q165_0001','Q23','Q148','Q161_0001','Q162_0001','Q163','Q164','Q27',
    'Q28','Q29','Q177','Q178','Q33','Q169','Q170','Q168','Q171','Q35','Q261','Q262','Q263','Q264','Q265','Q266','Q267','Q268',
    'Q26','Q270','Q271','Q160_0001','Q158_0001','Q134','Q42','Q61','Q62','Q63','Q43','Q60','Q278','Q279','Q280','Q276','Q257',
    'Q125','Q281','Q282','Q285','Q284','Q273','Q272','Q52','Q269','Q289','Q290','Q291','Q292'
]

REDCAP_KEEP = [
    'id','age','gender','isMale','weightkg','heightm','BMI','FFM','EEE','EI','EI_kg','EA','LowEA_clinical','LowEA_subclinical',
    'miles_wk','fruit','NSVeg','StarchVeg','VegAll','legumes','Grains','Profoods','MtPltry','FttyFish','eggs','dairy','fluids',
    'cho','chokg','pro','prokg','fat','fatkg','fiber','mealsday','snacksday','fasting','skip','vegetarian','vegan','restrict',
    'restrictallergy','housing','foodprep','foodinsecure','percep1','percep2','percep3','percep4','percep5','barswk','probarswk',
    'prodrnkwk','gelchewwk','chodrnk','caffdrnk','supp','vitamin','iron','calcium','vitaminD','caffeine','creatine','prewrkout',
    'wtgainer','wtlosssupp','aasupp','herbotsupp'
]

NUMBER_PATTERNS = [
    ('> THIRTY-FIVE', 36), ('THIRTY-FIVE', 35), ('THIRTY-FOUR', 34), ('THIRTY-THREE', 33), ('THIRTY-TWO', 32),
    ('> THIRTY', 31), ('THIRTY-ONE', 31), ('THIRTY ', 30), ('TWENTY-NINE', 29), ('TWENTY-EIGHT', 28), ('TWENTY-SEVEN', 27),
    ('TWENTY-SIX', 26), ('TWENTY-FIVE', 25), ('TWENTY-FOUR', 24), ('TWENTY-THREE', 23), ('TWENTY-TWO', 22),
    ('TWENTY-ONE', 21), ('TWENTY ', 20), ('NINETEEN', 19), ('EIGHTEEN', 18), ('SEVENTEEN', 17), ('SIXTEEN', 16),
    ('> FIFTEEN', 16), ('FIFTEEN', 15), ('FOURTEEN', 14), ('THIRTEEN', 13), ('TWELVE', 12), ('ELEVEN', 11), ('TEN', 10),
    ('NINE ', 9), ('EIGHT ', 8), ('SEVEN ', 7), ('SIX ', 6), ('FIVE', 5), ('FOUR ', 4), ('THREE', 3), ('TWO', 2), ('ONE', 1)
]

HOUR_PATTERNS = [
    ('FIFTEEN hours', 15), ('FOURTEEN and a HALF', 14.5), ('FOURTEEN hours', 14), ('THIRTEEN and a HALF', 13.5),
    ('THIRTEEN hours', 13), ('TWELVE and a HALF', 12.5), ('TWELVE hours', 12), ('ELEVEN and a HALF', 11.5), ('ELEVEN hours', 11),
    ('TEN and a HALF', 10.5), ('TEN hours', 10), ('NINE and a HALF', 9.5), ('NINE hours', 9), ('EIGHT and a HALF', 8.5),
    ('EIGHT hours', 8), ('SEVEN and a HALF', 7.5), ('SEVEN hours', 7), ('SIX and a HALF', 6.5), ('SIX hours', 6),
    ('FIVE and a HALF', 5.5), ('FIVE hours', 5), ('FOUR and a HALF', 4.5), ('FOUR hours', 4), ('THREE and a HALF', 3.5),
    ('THREE hours', 3), ('TWO and a HALF', 2.5), ('TWO', 2), ('ONE and a HALF', 1.5), ('ONE hour', 1), ('HALF', 0.5)
]


def normalize_columns(df_raw: pd.DataFrame):
    df = df_raw.copy()
    rename_map = {}
    for col in df.columns:
        new_col = re.sub(r'\.(\d+)$', lambda m: f"_{int(m.group(1)):04d}", col)
        rename_map[col] = new_col
    df = df.rename(columns=rename_map)

    first_row = df.iloc[0].astype(str).fillna('') if len(df) else pd.Series(dtype=str)
    for col in df.columns:
        label = str(first_row.get(col, ''))
        if 'Height_in' in label:
            df = df.rename(columns={col: 'Q209'})
        elif 'Weight_lbs' in label:
            df = df.rename(columns={col: 'Q210'})

    # In some exports mixed drinks and wine swapped; fix based on first-row question text.
    for col in ['Q291', 'Q292']:
        if col in df.columns:
            label = str(df[col].iloc[0])
            if col == 'Q291' and 'wine' in label.lower():
                pass
            if col == 'Q292' and 'mixed drinks' in label.lower():
                pass
    return df


def to_upper_text(s: pd.Series) -> pd.Series:
    return s.fillna('').astype(str).str.upper()


def parse_serving_series(s: pd.Series) -> pd.Series:
    txt = to_upper_text(s)
    out = pd.Series(float('nan'), index=s.index, dtype='float64')
    out = pd.to_numeric(txt, errors='coerce')
    txt2 = txt.fillna('')
    out = out.where(~out.isna(), other=pd.NA)
    out = out.astype('float64')
    out = out.mask(txt2.eq('PREFER NOT TO ANSWER'), 0)
    out = out.mask(txt2.str.contains('< ONE|LESS THAN ONE', na=False), 0)
    for pat, val in NUMBER_PATTERNS:
        if pat in ['TWO', 'THREE', 'FIVE', 'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN', 'NINETEEN', 'TWENTY-ONE', 'TWENTY-TWO', 'TWENTY-THREE', 'TWENTY-FOUR', 'TWENTY-FIVE', 'TWENTY-SIX', 'TWENTY-SEVEN', 'TWENTY-EIGHT', 'TWENTY-NINE', 'THIRTY-ONE', 'THIRTY-TWO', 'THIRTY-THREE', 'THIRTY-FOUR']:
            mask = txt2.str.startswith(pat, na=False) if pat in ['TWO', 'THREE', 'FIVE'] else txt2.str.contains(pat, na=False)
        elif pat in ['ONE', 'FOUR ', 'SIX ', 'SEVEN ', 'EIGHT ', 'NINE ', 'FIFTEEN', 'TWENTY ', 'THIRTY ']:
            mask = txt2.str.startswith(pat, na=False)
        else:
            mask = txt2.str.contains(pat, na=False)
        out = out.mask(mask, val)
    return out.fillna(0)


def parse_numeric_first(s: pd.Series) -> pd.Series:
    txt = to_upper_text(s)
    extracted = txt.str.replace(',', '', regex=False).str.extract(r'(-?\d+(?:\.\d+)?)')[0]
    return pd.to_numeric(extracted, errors='coerce')


def parse_hours(s: pd.Series) -> pd.Series:
    txt = to_upper_text(s)
    out = pd.to_numeric(txt, errors='coerce')
    out = out.astype('float64')
    out = out.mask(txt.eq('NONE'), 0)
    for pat, val in HOUR_PATTERNS:
        mask = txt.str.startswith(pat, na=False)
        out = out.mask(mask, val)
    return out.fillna(0)


def contains(s: pd.Series, pattern: str) -> pd.Series:
    return to_upper_text(s).str.contains(pattern.upper(), regex=False, na=False)


def get_col(df, col):
    if col in df.columns:
        return df[col]
    return pd.Series([pd.NA] * len(df), index=df.index)


def issue(report, msg):
    report.append(msg)


def process(df_raw: pd.DataFrame):
    report = []
    df_raw = normalize_columns(df_raw)
    if len(df_raw) < 2:
        raise ValueError('The uploaded file looks too short. It needs the Qualtrics question row plus at least one participant row.')

    header_row = df_raw.iloc[0].astype(str)
    df = df_raw.iloc[1:].copy().reset_index(drop=True)

    # Column aliases for exports that keep the original name instead of the SAS duplicate-name version.
    alias_sources = {'Q161_0001':'Q161','Q162_0001':'Q162','Q160_0001':'Q160','Q165_0001':'Q165'}
    for target, source in alias_sources.items():
        if target not in df.columns and source in df.columns:
            df[target] = df[source]

    for c in SERVING_VARS:
        if c not in df.columns:
            df[c] = pd.NA
            issue(report, f'{c} missing: set to 0 for food/alcohol calculations.')
        df[c] = parse_serving_series(df[c])

    # Direct food mappings
    food_map = {
        'fruits':'Q10','driedfruit':'Q11','fruitjuice':'Q12','vegrlg':'Q149','vegother':'Q146','TomSauc':'Q1','TomJuice':'Q150',
        'plainbrd':'Q24','BkdBrd':'Q165_0001','CRPast':'Q23','GrnsOtr':'Q148','Legumess':'Q161_0001','Corn':'Q162_0001',
        'PotatoNF':'Q163','PotatoFr':'Q164','LeanMeat':'Q27','FatMeat':'Q28','FtyFish':'Q29','WhEgg':'Q177','EggWt':'Q178',
        'milk':'Q33','FlvMilk':'Q169','Yogurt':'Q170','FlvYogurt':'Q168','cheese':'Q171','cotcheese':'Q35','vegoil':'Q261',
        'NutBtr':'Q262','CocOilBt':'Q263','Butter':'Q264','lard':'Q265','SrCrm':'Q266','CrmChs':'Q267','Cream':'Q268',
        'Mayo':'Q269','Mrgrne':'Q270','HlfHlf':'Q271','olives':'Q160_0001','nuts':'Q158_0001','avocado':'Q134','ChocCndy':'Q42',
        'NonChcCndy':'Q61','IceCrm':'Q62','FroYo':'Q63','BkdGd':'Q43','SwtBvg':'Q60','SwtTCfee':'Q278','OtrSwtBvg':'Q280',
        'NrgDrnk':'Q279','coconutwater':'Q276','slddressing':'Q257','NRGbar':'Q125','ProBar':'Q281','chodrnk':'Q282',
        'gel':'Q285','ProDrnk':'Q284','zerocaldrnk':'Q273','unSwtTCfee':'Q272','water':'Q52','beer':'Q289','spirits':'Q290',
        'mixed':'Q292','wine':'Q291'
    }
    # If export has Q291/Q292 labels reversed, detect from first row.
    if 'Q291' in header_row.index and 'mixed drinks' in str(header_row['Q291']).lower():
        food_map['mixed'] = 'Q291'
        food_map['wine'] = 'Q292'
    if 'Q292' in header_row.index and 'wine' in str(header_row['Q292']).lower():
        food_map['mixed'] = 'Q291'
        food_map['wine'] = 'Q292'

    out = pd.DataFrame(index=df.index)
    for new, old in food_map.items():
        out[new] = df[old]

    # type recodes
    q64 = get_col(df, 'Q64')
    q65 = get_col(df, 'Q65')
    q286 = get_col(df, 'Q286')
    q179 = get_col(df, 'Q179')
    q156 = get_col(df, 'Q156_0001')

    milktype = pd.Series(float('nan'), index=df.index, dtype='float64')
    milktype = milktype.mask(contains(q64, 'Non fat'), 1)
    milktype = milktype.mask(contains(q64, 'Low fat'), 2)
    milktype = milktype.mask(contains(q64, 'Regular'), 3)
    milktype = milktype.mask(contains(q64, 'Non-dairy [soy milk]'), 4)
    milktype = milktype.mask(contains(q64, 'Non-dairy [almond milk,'), 5)
    milktype = milktype.fillna(2)
    out['milktype'] = milktype

    yogtype = pd.Series(float('nan'), index=df.index, dtype='float64')
    yogtype = yogtype.mask(contains(q65, 'Non fat yogurt'), 1)
    yogtype = yogtype.mask(contains(q65, 'Low fat yogurt'), 2)
    yogtype = yogtype.mask(contains(q65, 'Regular (full-fat) yogurt'), 3)
    yogtype = yogtype.mask(contains(q65, 'Non-dairy yogurt'), 4)
    yogtype = yogtype.mask(contains(q65, 'Greek yogurt (non fat'), 5)
    yogtype = yogtype.mask(contains(q65, 'Greek yogurt (regular'), 6)
    yogtype = yogtype.fillna(2)
    out['yogtype'] = yogtype

    flvyogtype = pd.Series(float('nan'), index=df.index, dtype='float64')
    flvyogtype = flvyogtype.mask(contains(q286, 'Non fat yogurt'), 1)
    flvyogtype = flvyogtype.mask(contains(q286, 'Low fat yogurt'), 2)
    flvyogtype = flvyogtype.mask(contains(q286, 'Non-dairy yogurt'), 3)
    flvyogtype = flvyogtype.mask(contains(q286, 'Greek yogurt'), 4)
    flvyogtype = flvyogtype.mask(contains(q286, 'Non fat "no sugar added" or "diet" yogurt'), 5)
    flvyogtype = flvyogtype.fillna(2)
    out['flvyogtype'] = flvyogtype

    cheesetype = pd.Series(float('nan'), index=df.index, dtype='float64')
    cheesetype = cheesetype.mask(contains(q179, 'Regular dairy cheese'), 1)
    cheesetype = cheesetype.mask(contains(q179, 'Reduced fat or light'), 2)
    cheesetype = cheesetype.mask(contains(q179, 'Non-dairy cheese'), 3)
    cheesetype = cheesetype.fillna(1)
    out['cheesetype'] = cheesetype

    slddessingtype = pd.Series(float('nan'), index=df.index, dtype='float64')
    slddessingtype = slddessingtype.mask(contains(q156, 'Regular'), 1)
    slddessingtype = slddessingtype.mask(contains(q156, 'Reduced-fat'), 2)
    slddessingtype = slddessingtype.mask(contains(q156, 'Fat-free'), 3)
    slddessingtype = slddessingtype.fillna(1)
    out['slddessingtype'] = slddessingtype

    # demographics
    if 'Q209' not in df.columns:
        issue(report, 'Height column not found. BMI-related variables will be blank.')
    if 'Q210' not in df.columns:
        issue(report, 'Weight column not found. BMI-related variables will be blank.')
    q209 = parse_numeric_first(get_col(df, 'Q209'))
    q210 = parse_numeric_first(get_col(df, 'Q210'))
    out['weightkg'] = q210 / 2.2
    out['heightm'] = q209 * 0.0254
    out['BMI'] = out['weightkg'] / (out['heightm'] * out['heightm'])
    miss_hw = out['weightkg'].isna() | out['heightm'].isna()
    if miss_hw.any():
        issue(report, f'{int(miss_hw.sum())} row(s) missing height and/or weight: BMI, FFM, EA per kg may be blank.')
    out['ismale'] = pd.NA
    out.loc[get_col(df, 'Q230').astype(str).eq('Female'), 'ismale'] = 0
    out.loc[get_col(df, 'Q230').astype(str).eq('Male'), 'ismale'] = 1
    out['gender'] = get_col(df, 'Q230')
    out['age'] = pd.to_numeric(get_col(df, 'Q200'), errors='coerce')

    # run pace and exercise
    q213 = get_col(df, 'Q213').astype(str)
    out['runpace'] = pd.NA
    out['runMETS'] = pd.NA
    pace_map = [('5:30',5.5,16),('6:00',6,14.5),('6:30',6.5,12.8),('7:00',7,12.3),('7:30',7.5,11.8),('8:00',8,11.8),('8:30',8.5,11),('9:00',9,10.5)]
    for pat, pace, mets in pace_map:
        mask = q213.str.contains(pat, regex=False, na=False)
        out.loc[mask, 'runpace'] = pace
        out.loc[mask, 'runMETS'] = mets
    out['miles_wk'] = pd.to_numeric(get_col(df, 'Q212'), errors='coerce').fillna(0)
    out['runpace'] = pd.to_numeric(out['runpace'], errors='coerce').fillna(8)
    out['runMETS'] = pd.to_numeric(out['runMETS'], errors='coerce').fillna(11.8)
    out['hrsrunning'] = (out['miles_wk'] * out['runpace']) / 60

    def intensity_to_mets(series, high, moderate, low, default):
        t = to_upper_text(series)
        vals = pd.Series(float('nan'), index=series.index, dtype='float64')
        vals = vals.mask(t.str.contains('HIGH', na=False), high)
        vals = vals.mask(t.str.contains('MODERATE', na=False), moderate)
        vals = vals.mask(t.str.contains('LOW', na=False), low)
        return vals.fillna(default)

    out['weightliftMETS'] = intensity_to_mets(get_col(df, 'Q215'), 6, 5, 3.5, 5)
    out['aquajogMETS'] = intensity_to_mets(get_col(df, 'Q219'), 9.8, 6.8, 4.8, 6.8)
    out['bikeMETS'] = intensity_to_mets(get_col(df, 'Q224'), 10, 8, 6.8, 8)
    out['ellipticalMETS'] = intensity_to_mets(get_col(df, 'Q225'), 9, 7, 5, 7)
    out['weightlifthrs'] = parse_hours(get_col(df, 'Q70'))
    out['aquajoghrs'] = parse_hours(get_col(df, 'Q218'))
    out['bikehrs'] = parse_hours(get_col(df, 'Q221'))
    out['ellipticalhrs'] = parse_hours(get_col(df, 'Q223'))

    out['BodyFat'] = 1.2 * out['BMI'] + 0.23 * out['age'] - 10.8 * out['ismale'] - 5.4
    out['FFM'] = out['weightkg'] - out['weightkg'] * out['BodyFat'] * 0.01

    # Meals/snacks
    num_word = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5,'Six':6,'Seven':7,'Eight':8,'Nine':9,'Ten':10}
    out['Mealsday'] = get_col(df,'Q152').map(num_word)
    out['Snacksday'] = get_col(df,'Q153').map(num_word)
    out['Fasting'] = get_col(df,'Q154').map({'No':0,'Yes':1})
    out['Skip'] = get_col(df,'Q155').map({'No':0,'Yes':1})

    q157 = get_col(df, 'Q157').astype(str)
    out['Vegetarian'] = 0
    out['Vegan'] = 0
    mask = q157.str.contains('I follow a vegetarian diet', regex=False, na=False)
    out.loc[mask, ['Vegetarian','Vegan']] = [1,0]
    mask = q157.str.contains('I follow a vegan diet', regex=False, na=False)
    out.loc[mask, ['Vegetarian','Vegan']] = [1,1]
    out['Restrict'] = 0
    out.loc[(out['Vegetarian'] == 1) | (out['Vegan'] == 1), 'Restrict'] = 1
    out.loc[(get_col(df,'Q158').astype(str).eq('Yes')) & (get_col(df,'Q232').astype(str).eq('No')), 'Restrict'] = 1
    out['RestrictAllergy'] = get_col(df,'Q232').map({'Yes':1}).fillna(0)

    q240 = get_col(df,'Q240').astype(str)
    out['Housing'] = pd.NA
    out.loc[q240.str.contains('I live in student housing on campus', regex=False, na=False), 'Housing'] = 1
    out.loc[q240.str.contains('I live off campus (alone', regex=False, na=False), 'Housing'] = 2
    out.loc[q240.str.contains('I live off campus with one', regex=False, na=False), 'Housing'] = 3
    out.loc[q240.str.contains('Other', regex=False, na=False), 'Housing'] = 4

    q241 = get_col(df,'Q241').astype(str)
    out['FoodPrep'] = pd.NA
    out.loc[q241.str.contains('A family member', regex=False, na=False), 'FoodPrep'] = 1
    out.loc[q241.str.contains('I am', regex=False, na=False), 'FoodPrep'] = 2
    out.loc[q241.str.contains('Campus', regex=False, na=False), 'FoodPrep'] = 3
    out.loc[q241.str.contains('Another', regex=False, na=False), 'FoodPrep'] = 4

    out['FoodInsecure'] = get_col(df,'Q245').isin(['Often true','Sometimes true']).astype(int)

    # Perception questions were commented out in SAS due to missingness.
    for p in ['Percep1','Percep2','Percep3','Percep4','Percep5']:
        out[p] = pd.NA

    q165 = get_col(df,'Q165').astype(str)
    q166 = get_col(df,'Q166').astype(str)
    out['supp'] = (~((q165.isin(['I do not take vitamins or minerals.', '.'])) & (q166.isin(['None', '.'])))).astype(int)
    out['vitamin'] = q165.str.contains('Multivitamin', regex=False, na=False).astype(int)
    out['vitaminD'] = q165.str.contains('Vitamin D supplement', regex=False, na=False).astype(int)
    out['iron'] = q165.str.contains('Iron', regex=False, na=False).astype(int)
    out['calcium'] = q165.str.contains('Calcium', regex=False, na=False).astype(int)
    out['caffeine'] = q166.str.contains('Caffeine', regex=False, na=False).astype(int)
    out['creatine'] = q166.str.contains('Creatine', regex=False, na=False).astype(int)
    out['prewrkout'] = q166.str.contains('Preworkout', regex=False, na=False).astype(int)
    out['WtGainer'] = q166.str.contains('gain', regex=False, na=False).astype(int)
    out['WtLosssupp'] = q166.str.contains('loss', regex=False, na=False).astype(int)
    out['AAsupp'] = q166.str.contains('acids', regex=False, na=False).astype(int)
    out['HerBotSupp'] = q166.str.contains('botanicals', regex=False, na=False).astype(int)

    # Nutrient calculations
    o = out
    o['fruitkcal']=(o['fruits']*60)+(o['driedfruit']*60)+(o['fruitjuice']*120/7)
    o['FruitCHO']=(o['fruits']*15)+(o['driedfruit']*15)+(o['fruitjuice']*30/7)
    o['FruitFiber']=(o['fruits']*2)+(o['driedfruit']*2)
    o['Fruit']=(o['fruits']/2)+(o['driedfruit']/2)+(o['fruitjuice']/7)
    o['coconutwaterkcal']=o['coconutwater']*45/7
    o['coconutwatercho']=o['coconutwater']*10/7
    o['vegNSkcal']=(o['vegrlg']*25)+(o['vegother']*37.5)+((o['TomSauc']*50)/7)+((o['TomJuice']*50)/7)
    o['vegNSCHO']=(o['vegrlg']*5)+(o['vegother']*7.5)+((o['TomSauc']*10)/7)+((o['TomJuice']*10)/7)
    o['vegNSPRO']=(o['vegrlg']*2)+(o['vegother']*3)+((o['TomSauc']*4)/7)+((o['TomJuice']*4)/7)
    o['vegNSFiber']=(o['vegrlg']*2.5)+(o['vegother']*4)+((o['TomSauc']*4)/7)+((o['TomJuice']*4)/7)
    o['NSVeg']=(o['vegrlg']*0.5)+(o['vegother']*1)+((o['TomSauc']*1)/7)+((o['TomJuice']*1)/7)
    o['Grainkcal']=(o['plainbrd']*80)+(o['BkdBrd']*125)+(o['CRPast']*80)+(o['GrnsOtr']*125)
    o['GrainCHO']=(o['plainbrd']*15)+(o['BkdBrd']*15)+(o['CRPast']*15)+(o['GrnsOtr']*15)
    o['GrainPRO']=(o['plainbrd']*3)+(o['BkdBrd']*3)+(o['CRPast']*3)+(o['GrnsOtr']*3)
    o['GrainFAT']=(o['BkdBrd']*5)+(o['GrnsOtr']*5)
    o['GrainFiber']=(o['plainbrd']*1)+(o['BkdBrd']*1)+(o['CRPast']*1)+(o['GrnsOtr']*1)
    o['Grains']=o['plainbrd']+o['BkdBrd']+o['CRPast']+o['GrnsOtr']
    o['Legumeskcal']=(o['Legumess']*100)/7
    o['LegumesCHO']=(o['Legumess']*15)/7
    o['LegumesPRO']=(o['Legumess']*6)/7
    o['LegumesFiber']=(o['Legumess']*5)/7
    o['Legumes']=o['Legumess']*0.14/2
    o['Cornkcal']=(o['Corn']*80)/7
    o['CornCHO']=(o['Corn']*15)/7
    o['CornPRO']=(o['Corn']*3)/7
    o['CornFiber']=o['Corn']*1
    o['Potatokcal']=(o['PotatoNF']*80)/7 + (o['PotatoFr']*125)/7
    o['PotatoCHO']=(o['PotatoNF']*15)/7 + (o['PotatoFr']*15)/7
    o['PotatoPRO']=(o['PotatoNF']*3)/7 + (o['PotatoFr']*3)/7
    o['PotatoFAT']=(o['PotatoFr']*5)/7
    o['PotatoFiber']=(o['PotatoNF']*1)/7 + (o['PotatoFr']*1)/7
    o['PotatoTotal']=(o['PotatoNF']+o['PotatoFr'])*0.14/2
    o['VegSkcal']=o['Legumeskcal']+o['Cornkcal']+o['Potatokcal']
    o['VegSCHO']=o['LegumesCHO']+o['CornCHO']+o['PotatoCHO']
    o['vegSpro']=o['LegumesPRO']+o['CornPRO']+o['PotatoPRO']
    o['vegSfat']=o['PotatoFAT']
    o['vegSfiber']=o['LegumesFiber']+o['CornFiber']+o['PotatoFiber']
    o['StarchVeg']=(o['Legumes']+o['Corn']+o['PotatoNF']+o['PotatoFr'])*0.14/2
    o['VegAll']=o['NSVeg']+o['StarchVeg']
    o['MeatPoultrykcal']=(o['LeanMeat']*135)/7 + (o['FatMeat']*262.5)/7
    o['MeatPoultryPRO']=(o['LeanMeat']*21)/7 + (o['FatMeat']*21)/7
    o['MeatPoultryFAT']=(o['LeanMeat']*4.5)/7 + (o['FatMeat']*19.5)/7
    o['FattyFishkcal']=(o['FtyFish']*195)/7
    o['FattyFishPRO']=(o['FtyFish']*21)/7
    o['FattyFishFAT']=(o['FtyFish']*12)/7
    o['Eggskcal']=(o['WhEgg']*70)/7 + (o['EggWt']*20)/7
    o['EggsPRO']=(o['WhEgg']*6)/7 + (o['EggWt']*4)/7
    o['EggsFAT']=(o['WhEgg']*5)/7
    o['FttyFish']=(o['FtyFish']*0.143)/3
    o['Eggs']=(o['WhEgg']*0.143) + (o['EggWt']*0.67)/7
    o['MtPltry']=((o['LeanMeat']+o['FatMeat'])*0.143)/3

    # milk block
    for mt, vals in {
        1:(90,12,8,1.5,168,34,8,0),2:(120,12,8,5,160,26,9,3),3:(150,12,8,8,208,26,8,8),
        4:(100,8,7,4,154,24,6,4),5:(50,5,1,3,120,23,2,3)
    }.items():
        mk,mcho,mpro,mfat,fk,fcho,fpro,ffat = vals
        mask = o['milktype'] == mt
        o.loc[mask,'milkkcal'] = (o.loc[mask,'milk']*mk)/7
        o.loc[mask,'milkCHO'] = (o.loc[mask,'milk']*mcho)/7
        o.loc[mask,'milkPRO'] = (o.loc[mask,'milk']*mpro)/7
        o.loc[mask,'milkFAT'] = (o.loc[mask,'milk']*mfat)/7
        o.loc[mask,'FlvMilkkcal'] = (o.loc[mask,'FlvMilk']*fk)/7
        o.loc[mask,'FlvMilkCHO'] = (o.loc[mask,'FlvMilk']*fcho)/7
        o.loc[mask,'FlvMilkPRO'] = (o.loc[mask,'FlvMilk']*fpro)/7
        o.loc[mask,'FlvMilkFAT'] = (o.loc[mask,'FlvMilk']*ffat)/7

    for yt, vals in {1:(120,16,11,0),2:(150,17,13,4),3:(150,11,9,8),4:(162,13,6,4),5:(179,10,25,5),6:(238,10,22,12)}.items():
        k,c,p,f = vals
        mask = o['yogtype'] == yt
        o.loc[mask,'yogkcal']=(o.loc[mask,'Yogurt']*k)/7
        o.loc[mask,'yogCHO']=(o.loc[mask,'Yogurt']*c)/7
        o.loc[mask,'yogPRO']=(o.loc[mask,'Yogurt']*p)/7
        o.loc[mask,'yogFAT']=(o.loc[mask,'Yogurt']*f)/7

    for yt, vals in {1:(191,42,7,0),2:(208,34,12,3),3:(216,36,7,4),4:(233,23,21,6),5:(90,12,8,0)}.items():
        k,c,p,f = vals
        mask = o['flvyogtype'] == yt
        o.loc[mask,'flvyogkcal']=(o.loc[mask,'FlvYogurt']*k)/7
        o.loc[mask,'flvyogcho']=(o.loc[mask,'FlvYogurt']*c)/7
        o.loc[mask,'flvyogpro']=(o.loc[mask,'FlvYogurt']*p)/7
        o.loc[mask,'flvyogfat']=(o.loc[mask,'FlvYogurt']*f)/7

    for ct, vals in {1:(100,7,8,0),2:(75,7,5,0),3:(74,3,6,3)}.items():
        k,p,f,c = vals
        mask = o['cheesetype'] == ct
        o.loc[mask,'cheesekcal']=(o.loc[mask,'cheese']*k)/7
        o.loc[mask,'cheesePRO']=(o.loc[mask,'cheese']*p)/7
        o.loc[mask,'cheeseFAT']=(o.loc[mask,'cheese']*f)/7
        o.loc[mask,'cheesecho']=(o.loc[mask,'cheese']*c)/7

    o['cotcheesekcal']=(o['cotcheese']*180)/7
    o['cotcheesePRO']=(o['cotcheese']*24)/7
    o['cotcheeseFAT']=(o['cotcheese']*5)/7
    o['cotcheesecho']=(o['cotcheese']*10)/7
    o['Dairy']=o['milk']/7 + o['FlvMilk']/7 + o['Yogurt']/7 + o['FlvYogurt']/7 + o['cheese']*0.67/7 + o['cotcheese']*0.8/7

    # SAS has `if slddessingtype then do;` which effectively means nonzero; keep behavior.
    mask = o['slddessingtype'].notna() & (o['slddessingtype'] != 0)
    o.loc[mask,'slddrkcal']=(o.loc[mask,'slddressing']*45)/7
    o.loc[mask,'slddrcho']=0
    o.loc[mask,'slddrfat']=(o.loc[mask,'slddressing']*5)/7
    mask = o['slddessingtype'] == 2
    o.loc[mask,'slddrkcal']=(o.loc[mask,'slddressing']*22.5)/7
    o.loc[mask,'slddrcho']=0
    o.loc[mask,'slddrfat']=(o.loc[mask,'slddressing']*2.5)/7
    mask = o['slddessingtype'] == 3
    o.loc[mask,'slddrkcal']=(o.loc[mask,'slddressing']*20)/7
    o.loc[mask,'slddrcho']=(o.loc[mask,'slddressing']*5)/7
    o.loc[mask,'slddrfat']=0

    o['VegOilkcal']=(o['vegoil']*135)/7; o['VegOilFAT']=(o['vegoil']*15)/7
    o['NutBtrkcal']=(o['NutBtr']*94)/7; o['NutBtrPRO']=(o['NutBtr']*4)/7; o['NutBtrFAT']=(o['NutBtr']*8)/7; o['NutBtrCHO']=(o['NutBtr']*3)/7; o['NutBtrFiber']=(o['NutBtr']*1)/7
    o['CocOilBtkcal']=(o['CocOilBt']*120)/7; o['CocOilBtFAT']=(o['CocOilBt']*14)/7
    o['Butterkcal']=(o['Butter']*102)/7; o['ButterFAT']=(o['Butter']*12)/7
    o['Lardkcal']=(o['lard']*115)/7; o['LardFAT']=(o['lard']*13)/7
    o['SrCrmkcal']=(o['SrCrm']*22.5)/7; o['SrCrmFAT']=(o['SrCrm']*2.5)/7
    o['CrmChskcal']=(o['CrmChs']*45)/7; o['CrmChsFAT']=(o['CrmChs']*5)/7
    o['Creamkcal']=(o['Cream']*45)/7; o['CreamFAT']=(o['Cream']*5)/7
    o['Mayokcal']=(o['Mayo']*94)/7; o['MayoFAT']=(o['Mayo']*10)/7
    o['Mrgrnekcal']=(o['Mrgrne']*103)/7; o['MrgrneFAT']=(o['Mrgrne']*11)/7
    o['HlfHlfkcal']=(o['HlfHlf']*22.5)/7; o['HlfHlfFAT']=(o['HlfHlf']*2.5)/7
    o['Oliveskcal']=(o['olives']*10)/7; o['OlivesFAT']=(o['olives']*1)/7
    o['Nutskcal']=(o['nuts']*199)/7; o['NutsCHO']=(o['nuts']*7.3)/7; o['NutsPRO']=(o['nuts']*6.4)/7; o['NutsFAT']=(o['nuts']*17.5)/7; o['NutsFiber']=(o['nuts']*2.1)/7
    o['Avocadokcal']=(o['avocado']*96)/7; o['AvocadoCHO']=(o['avocado']*5)/7; o['AvocadoFAT']=(o['avocado']*9)/7; o['AvocadoFiber']=(o['avocado']*3.9)/7; o['AvocadoPRO']=(o['avocado']*1/7)
    o['extrafatskcal']=o['VegOilkcal']+o['NutBtrkcal']+o['CocOilBtkcal']+o['Butterkcal']+o['Lardkcal']+o['SrCrmkcal']+o['CrmChskcal']+o['Creamkcal']+o['Mayokcal']+o['Mrgrnekcal']+o['HlfHlfkcal']+o['Oliveskcal']+o['Nutskcal']+o['Avocadokcal']
    o['extrafatsfat']=o['VegOilFAT']+o['NutBtrFAT']+o['CocOilBtFAT']+o['ButterFAT']+o['LardFAT']+o['SrCrmFAT']+o['CrmChsFAT']+o['CreamFAT']+o['MayoFAT']+o['MrgrneFAT']+o['HlfHlfFAT']+o['OlivesFAT']+o['NutsFAT']+o['AvocadoFAT']
    o['extrafatscho']=o['NutsCHO']+o['AvocadoCHO']+o['NutBtrCHO']
    o['extrafatsfiber']=o['NutsFiber']+o['AvocadoFiber']+o['NutBtrFiber']
    o['extrafatspro']=o['NutsPRO']+o['NutBtrPRO']+o['AvocadoPRO']
    o['ChocCndykcal']=(o['ChocCndy']*105)/7; o['ChocCndyCHO']=(o['ChocCndy']*15)/7; o['ChocCndyFAT']=(o['ChocCndy']*5)/7
    o['NonChcCndykcal']=(o['NonChcCndy']*60)/7; o['NonChcCndyCHO']=(o['NonChcCndy']*15)/7
    o['IceCrmkcal']=(o['IceCrm']*150)/7; o['IceCrmCHO']=(o['IceCrm']*15)/7; o['IceCrmFAT']=(o['IceCrm']*10)/7
    o['FroYokcal']=(o['FroYo']*105)/7; o['FroYoCHO']=(o['FroYo']*15)/7; o['FroYoFAT']=(o['FroYo']*5)/7
    o['BkdGdkcal']=(o['BkdGd']*105)/7; o['BkdGdCHO']=(o['BkdGd']*15)/7; o['BkdGdFAT']=(o['BkdGd']*5)/7
    o['sweetskcal']=o['ChocCndykcal']+o['NonChcCndykcal']+o['IceCrmkcal']+o['FroYokcal']+o['BkdGdkcal']
    o['sweetsfat']=o['ChocCndyFAT']+o['IceCrmFAT']+o['FroYoFAT']+o['BkdGdFAT']
    o['sweetscho']=o['ChocCndyCHO']+o['NonChcCndyCHO']+o['IceCrmCHO']+o['FroYoCHO']+o['BkdGdCHO']
    o['SwtBvgkcal']=o['SwtBvg']*120; o['SwtBvgCHO']=o['SwtBvg']*30
    o['SwtTCfeekcal']=o['SwtTCfee']*75; o['SwtTCfeeCHO']=o['SwtTCfee']*15; o['SwtTCfeePRO']=o['SwtTCfee']*2; o['SwtTCfeeFAT']=o['SwtTCfee']*1.5
    o['NrgDrnkkcal']=o['NrgDrnk']*110; o['NrgDrnkcho']=o['NrgDrnk']*29
    o['OtrSwtBvgkcal']=o['OtrSwtBvg']*120; o['OtrSwtBvgCHO']=o['OtrSwtBvg']*30
    o['chodrnkkcal']=(o['chodrnk']*65)/7; o['chodrnkcho']=(o['chodrnk']*15)/7
    o['drinkskcal']=o['SwtBvgkcal']+o['SwtTCfeekcal']+o['OtrSwtBvgkcal']+o['NrgDrnkkcal']+o['chodrnkkcal']
    o['drinkscho']=o['SwtBvgCHO']+o['SwtTCfeeCHO']+o['OtrSwtBvgCHO']+o['NrgDrnkcho']+o['chodrnkcho']
    o['drinkspro']=o['SwtTCfeePRO']; o['drinksfat']=o['SwtTCfeeFAT']
    o['NRGbarkcal']=(o['NRGbar']*225)/7; o['NRGbarCHO']=(o['NRGbar']*35)/7; o['NRGbarPRO']=(o['NRGbar']*10)/7; o['NRGbarFAT']=(o['NRGbar']*5)/7; o['NRGbarFiber']=(o['NRGbar']*3)/7
    o['ProBarkcal']=(o['ProBar']*250)/7; o['ProBarCHO']=(o['ProBar']*30)/7; o['ProBarPRO']=(o['ProBar']*20)/7; o['ProBarFAT']=(o['ProBar']*7)/7; o['ProBarFiber']=(o['ProBar']*2)/7
    o['gelkcal']=(o['gel']*100)/7; o['gelcho']=(o['gel']*27)/7
    o['barsgelskcal']=o['NRGbarkcal']+o['ProBarkcal']+o['gelkcal']
    o['barsgelscho']=o['NRGbarCHO']+o['ProBarCHO']+o['gelcho']
    o['barsgelspro']=o['NRGbarPRO']+o['ProBarPRO']
    o['barsgelsfat']=o['NRGbarFAT']+o['ProBarFAT']
    o['barsgelsfiber']=o['NRGbarFiber']+o['ProBarFiber']
    o['GelChewWk']=o['gel']
    o['ProDrnkkcal']=(o['ProDrnk']*286)/7; o['ProDrnkCHO']=(o['ProDrnk']*36)/7; o['ProDrnkPRO']=(o['ProDrnk']*20)/7; o['ProDrnkFAT']=(o['ProDrnk']*8)/7; o['ProDrnkFiber']=(o['ProDrnk']*4)/7
    o['nrgkcal']=o['NRGbarkcal']+o['ProBarkcal']+o['gelkcal']+o['ProDrnkkcal']
    o['nrgcho']=o['NRGbarCHO']+o['ProBarCHO']+o['gelcho']+o['ProDrnkCHO']
    o['nrgpro']=o['NRGbarPRO']+o['ProBarPRO']+o['ProDrnkPRO']
    o['nrgfat']=o['NRGbarFAT']+o['ProBarFAT']+o['ProDrnkFAT']
    o['nrgfiber']=o['NRGbarFiber']+o['ProBarFiber']+o['ProDrnkFiber']
    o['swtbvgtotal']=(o['SwtBvg']+o['SwtTCfee']+o['OtrSwtBvg']+o['NrgDrnk']+o['chodrnk'])*8/7
    o['otrbevtotal']=(o['zerocaldrnk']+o['unSwtTCfee']+o['water'])*8
    o['prodrnktotal']=(o['ProDrnk']*11)/7
    o['ProDrnkWk']=o['ProDrnk']
    o['fruitjuicetotal']=o['fruitjuice']*8/7
    o['coconutwatertotal']=o['coconutwater']*8/7
    o['milktotal']=(o['milk']+o['FlvMilk'])*8/7
    o['vegjuicetotal']=(o['TomJuice']*8)/7
    o['fluids']=o['swtbvgtotal']+o['otrbevtotal']+o['prodrnktotal']+o['fruitjuicetotal']+o['coconutwatertotal']+o['milktotal']+o['vegjuicetotal']
    o['alcoholkcal']=(o['beer']*160 + o['spirits']*100 + o['mixed']*160 + o['wine']*100)/7
    o['alcoholCHO']=(o['beer']*15 + o['mixed']*15)/7
    o['ProFoods']=(o['LeanMeat']*0.143/3)+(o['FatMeat']*0.143/3)+((o['FtyFish']*0.143)/3)+(o['WhEgg']*0.143)+(o['EggWt']*0.67)/7+(o['Legumess']*0.143)
    o['KcalTotal']=o['fruitkcal']+o['vegNSkcal']+o['Grainkcal']+o['VegSkcal']+o['MeatPoultrykcal']+o['FattyFishkcal']+o['Eggskcal']+o['milkkcal']+o['FlvMilkkcal']+o['yogkcal']+o['flvyogkcal']+o['cheesekcal']+o['cotcheesekcal']+o['slddrkcal']+o['extrafatskcal']+o['sweetskcal']+o['nrgkcal']+o['drinkskcal']+o['coconutwaterkcal']+o['alcoholkcal']
    o['CHO']=o['FruitCHO']+o['vegNSCHO']+o['GrainCHO']+o['VegSCHO']+o['milkCHO']+o['FlvMilkCHO']+o['yogCHO']+o['flvyogcho']+o['cheesecho']+o['slddrcho']+o['extrafatscho']+o['sweetscho']+o['nrgcho']+o['drinkscho']+o['coconutwatercho']+o['alcoholCHO']
    o['CHOkg']=o['CHO']/o['weightkg']
    o['FAT']=o['GrainFAT']+o['vegSfat']+o['MeatPoultryFAT']+o['FattyFishFAT']+o['EggsFAT']+o['milkFAT']+o['FlvMilkFAT']+o['yogFAT']+o['flvyogfat']+o['cheeseFAT']+o['cotcheeseFAT']+o['slddrfat']+o['extrafatsfat']+o['sweetsfat']+o['drinksfat']+o['nrgfat']
    o['FATkg']=o['FAT']/o['weightkg']
    o['PRO']=o['vegNSPRO']+o['GrainPRO']+o['vegSpro']+o['MeatPoultryPRO']+o['FattyFishPRO']+o['EggsPRO']+o['milkPRO']+o['FlvMilkPRO']+o['yogPRO']+o['flvyogpro']+o['cheesePRO']+o['cotcheesePRO']+o['extrafatspro']+o['barsgelspro']+o['drinkspro']+o['nrgpro']
    o['PROkg']=o['PRO']/o['weightkg']
    o['Fiber']=o['FruitFiber']+o['vegNSFiber']+o['GrainFiber']+o['vegSfiber']+o['extrafatsfiber']+o['nrgfiber']
    o['runkcal']=(o['weightkg']*o['runMETS']*o['hrsrunning'])/7
    o['weightliftkcal']=(o['weightkg']*o['weightliftMETS']*o['weightlifthrs'])/7
    o['aquajogkcal']=(o['weightkg']*o['aquajogMETS']*o['aquajoghrs'])/7
    o['bikekcal']=(o['weightkg']*o['bikeMETS']*o['bikehrs'])/7
    o['ellipticalkcal']=(o['weightkg']*o['ellipticalMETS']*o['ellipticalhrs'])/7
    o['EEE']=o['runkcal']+o['weightliftkcal']+o['aquajogkcal']+o['bikekcal']+o['ellipticalkcal']
    o['EA']=(o['KcalTotal']-o['EEE'])/o['FFM']
    o.loc[o['KcalTotal']==0, 'EA'] = pd.NA
    o['EI']=o['KcalTotal']
    o.loc[o['EI']==0, 'EI'] = pd.NA
    o['EI_kg']=o['EI']/o['weightkg']
    o['LowEA_clinical'] = pd.NA
    o['LowEA_subclinical'] = pd.NA
    male = o['ismale'] == 1
    female = o['ismale'] == 0
    o.loc[male & o['EA'].notna(), 'LowEA_clinical'] = ((o.loc[male & o['EA'].notna(), 'EA'] > 0) & (o.loc[male & o['EA'].notna(), 'EA'] < 15)).astype(int)
    o.loc[male & o['EA'].notna(), 'LowEA_subclinical'] = ((o.loc[male & o['EA'].notna(), 'EA'] >= 15) & (o.loc[male & o['EA'].notna(), 'EA'] < 30)).astype(int)
    o.loc[female & o['EA'].notna(), 'LowEA_clinical'] = ((o.loc[female & o['EA'].notna(), 'EA'] > 0) & (o.loc[female & o['EA'].notna(), 'EA'] < 30)).astype(int)
    o.loc[female & o['EA'].notna(), 'LowEA_subclinical'] = ((o.loc[female & o['EA'].notna(), 'EA'] >= 30) & (o.loc[female & o['EA'].notna(), 'EA'] < 45)).astype(int)
    o['BarsWk']=o['NRGbar']
    o['ProBarsWk']=o['ProBar']
    o['chodrink']=o['chodrnk']*8/7
    o['CaffDrnk']=o['NrgDrnk']*8/7
    o['id'] = get_col(df, 'Q182')

    # Case/label aliases so the REDCap output matches the SAS keep list exactly.
    o['isMale'] = o['ismale']
    o['fruit'] = o['Fruit']
    o['legumes'] = o['Legumes']
    o['Profoods'] = o['ProFoods']
    o['dairy'] = o['Dairy']
    o['eggs'] = o['Eggs']
    o['cho'] = o['CHO']
    o['chokg'] = o['CHOkg']
    o['pro'] = o['PRO']
    o['prokg'] = o['PROkg']
    o['fat'] = o['FAT']
    o['fatkg'] = o['FATkg']
    o['fiber'] = o['Fiber']
    o['mealsday'] = o['Mealsday']
    o['snacksday'] = o['Snacksday']
    o['fasting'] = o['Fasting']
    o['skip'] = o['Skip']
    o['vegetarian'] = o['Vegetarian']
    o['vegan'] = o['Vegan']
    o['restrict'] = o['Restrict']
    o['restrictallergy'] = o['RestrictAllergy']
    o['housing'] = o['Housing']
    o['foodprep'] = o['FoodPrep']
    o['foodinsecure'] = o['FoodInsecure']
    o['percep1'] = o['Percep1']; o['percep2'] = o['Percep2']; o['percep3'] = o['Percep3']; o['percep4'] = o['Percep4']; o['percep5'] = o['Percep5']
    o['barswk'] = o['BarsWk']
    o['probarswk'] = o['ProBarsWk']
    o['prodrnkwk'] = o['ProDrnkWk']
    o['gelchewwk'] = o['GelChewWk']
    o['caffdrnk'] = o['CaffDrnk']
    o['wtgainer'] = o['WtGainer']
    o['wtlosssupp'] = o['WtLosssupp']
    o['aasupp'] = o['AAsupp']
    o['herbotsupp'] = o['HerBotSupp']

    # Merge raw participant rows with outputs for full processed dataset.
    processed = pd.concat([df.reset_index(drop=True), o.reset_index(drop=True)], axis=1)

    # REDCap slim output: if missing columns like percep, keep blank.
    redcap = pd.DataFrame(index=processed.index)
    for c in REDCAP_KEEP:
        if c in processed.columns:
            redcap[c] = processed[c]
        elif c in o.columns:
            redcap[c] = o[c]
        else:
            redcap[c] = pd.NA
            issue(report, f'{c} not created: left blank in REDCap output.')

    return processed, redcap, report


def make_workbook(full_df, redcap_df, report):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        full_df.to_excel(writer, index=False, sheet_name='processed_full')
        redcap_df.to_excel(writer, index=False, sheet_name='redcap_output')
        report_df = pd.DataFrame({'message': report if report else ['No issues detected']})
        report_df.to_excel(writer, index=False, sheet_name='data_quality_report')
    buffer.seek(0)
    return buffer


st.title('Nutrition Survey Processor')
st.write('Upload the raw Qualtrics Excel file. The app will process it using the SAS logic, create a full processed dataset, create the smaller REDCap-style output, and list any data issues it found.')

uploaded = st.file_uploader('Upload Excel file', type=['xlsx'])
if uploaded is not None:
    try:
        raw = pd.read_excel(uploaded)
        full_df, redcap_df, report = process(raw)
        workbook = make_workbook(full_df, redcap_df, report)
        st.success(f'Processing complete. {len(full_df)} participant row(s) processed.')
        st.download_button(
            'Download results workbook',
            data=workbook,
            file_name='nutrition_processed_output.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        st.subheader('Data quality report')
        if report:
            for msg in report:
                st.write(f'• {msg}')
        else:
            st.write('No issues detected.')
        st.subheader('Preview: REDCap output')
        st.dataframe(redcap_df.head(10), use_container_width=True)
    except Exception as e:
        st.error(f'The file could not be processed: {e}')
