import pandas as pd
import re
import datetime as dt

df_raw_log = pd.read_csv('logistics.csv')
df_raw_sale = pd.read_csv("sales.csv")
df_raw_prod = pd.read_csv("production.csv")

for col_name in df_raw_log.columns:
    print(col_name, '-', df_raw_log[col_name].nunique())

df_raw_log['mine_name'].unique()

for cn in df_raw_log.columns:
    print(cn, '-', df_raw_log[cn].isna().sum(), '-', 'Nan')

df_raw_log['distance_km'] = df_raw_log['distance_km'].fillna(0).astype(int)
df_raw_log["cargo_weight_tonnes"]

def cwt(str_cwt):
    cwt_str = re.search(r'\d+', str_cwt)
    if cwt_str: return int(cwt_str.group())
    else: return None

df_raw_log['cargo_weight_tonnes'] = df_raw_log['cargo_weight_tonnes'].map(cwt)

df_raw_log["departure_date"] = pd.to_datetime(df_raw_log["departure_date"])
df_raw_log["arrival_date"] = pd.to_datetime(df_raw_log["arrival_date"])
df_raw_log.dtypes