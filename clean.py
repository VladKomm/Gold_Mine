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

def is_null(string: str) -> str | None:
    pass


# -------- Количество ячеек в столбцах с пробелами по сторонам от текста
def check_cell_spaces(dataframe: pd.DataFrame) -> dict:
    """Подсчитывает кол-во ячеек, в которых есть пробелы в начале и в конце строки и выводит отчет по колонкам датафрейма

    Args:
        dataframe (pd.DataFrame): Датафрейм для анализа

    Returns:
        dict: словарь с именами колонок и кол-вом ячеек, в которых есть пробелы по сторонам
    """

    dict_output = {}
    def check_cell_spaces(cell_string: str) -> bool:
        if isinstance(cell_string, str):
            return True if len(cell_string) > len(cell_string.strip()) else False
    for column in dataframe.columns:
        dict_output[column] = dataframe[column].map(check_cell_spaces).sum()
    return dict_output


# -------- Кроме букв английского алфавита
def except_for_english(cell_string) -> bool:
    """Возвращает кол-во символов, которые не включены в английский алфавит

    Args:
        cell_string ([type]): строка для проверки
    """

    count_letters = 0
    if not isinstance(cell_string, str): return False
    lst_words = re.findall(r'[a-z ]', cell_string.strip().lower())
    if not lst_words: return False
    for i in lst_words:
        count_letters += len(i)
    return len(cell_string) - count_letters


df_raw_log['cargo_weight_tonnes'] = df_raw_log['cargo_weight_tonnes'].map(cwt)

df_raw_log["departure_date"] = pd.to_datetime(df_raw_log["departure_date"])
df_raw_log["arrival_date"] = pd.to_datetime(df_raw_log["arrival_date"])
df_raw_log.dtypes
