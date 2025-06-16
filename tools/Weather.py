from pathlib import Path
import requests
import json

from datetime import date, timedelta

import pandas as pd


def average(lst):
    return round((sum(lst) / len(lst)), 0)

url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
params = {
    'serviceKey': key,
    'pageNo': '1',
    'numOfRows': '1000',
    'dataType': 'JSON',
    'base_date': Today,
    'base_time': '0500',
    'nx': '55',
    'ny': '127'
}

response = requests.get(url, params=params)
weather = json.loads(response.text)
print(response)

data = weather['response']['body']['items']['item']

pd.set_option('display.max_rows', None)
dataframe = pd.json_normalize(data)
today_data = dataframe[dataframe["fcstDate"] == Today]
print(today_data)


def termo():
    today_temp = today_data[today_data["category"] == "TMP"]
    temperatures = today_temp['fcstValue'].values.tolist()
    temperatures = list(map(int, temperatures))
    max_temp = max(temperatures)
    min_temp = min(temperatures)
    avg_temp = average(temperatures)
    return [max_temp, min_temp, avg_temp]

def rains():
    today_rains = today_data[today_data["category"] == "POP"]
    return today_rains


def graph():
    # 시간별 기온,강수확률,습도 이미지로
    return 1


if __name__ == '__main__':
    # 키값, 패스워드등 저장파일
    config = Path(__file__).parent
    absolute_keyfile_path = (config / "./config.json").resolve()
    config_file = Path(absolute_keyfile_path)
    # weather api, weather-key 수집
    if config_file.is_file():
        with open(absolute_keyfile_path, 'r') as file:
            key = json.load(file)
        weather_key = key['weather-key']
    key = weather_key

    Today = date.today().strftime("%Y%m%d")
    Tomorrow = (date.today() + timedelta(1)).strftime("%Y%m%d")
