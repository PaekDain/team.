import calendar
from datetime import datetime, timedelta, timezone
from collections import Counter
import re
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
page_title="학교 급식 찾아보기", page_icon="🍱", layout="centered"
)


# 한국 시간(KST) 기준 오늘 날짜 구하기
def get_today_kst():
kst = timezone(timedelta(hours=9))
return datetime.now(kst).date()


# 1. 학교 정보 검색 함수
def search_school(school_name):
url = "https://open.neis.go.kr/hub/schoolInfo"
params = {"Type": "json", "SCHUL_NM": school_name}

try:
response = requests.get(url, params=params, timeout=5)
data = response.json()

if "schoolInfo" in data:
rows = data["schoolInfo"][1]["row"]
return rows
return []
except Exception:
return []


# 검색어 보완 로직 (약어 변환 후 2차 검색)
def search_school_with_fallback(query):
results = search_school(query)
if results:
return results

fallback_query = query
if "여고" in fallback_query:
fallback_query = fallback_query.replace("여고", "여자고등학교")
elif "고" in fallback_query and not fallback_query.endswith("고등학교"):
fallback_query = re.sub(r"고$", "고등학교", fallback_query)
fallback_query = fallback_query.replace("고 ", "고등학교 ")

if fallback_query != query:
results = search_school(fallback_query)

return results


# 2. 특정 날짜 급식 정보 조회 함수
def get_meal_info(office_code, school_code, date_str):
url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
params = {
"Type": "json",
"ATPT_OFCDC_SC_CODE": office_code,
"SD_SCHUL_CODE": school_code,
"MMEAL_SC_CODE": "2", # 중식
"MLSV_FROM_YMD": date_str,
"MLSV_TO_YMD": date_str,
}

try:
response = requests.get(url, params=params, timeout=5)
data = response.json()

if "mealServiceDietInfo" in data:
return data["mealServiceDietInfo"][1]["row"][0]
return None
except Exception:
return None


# 3. 메뉴 문자열 정제 (알레르기 번호 및 원산지/특수문자 제거)
def clean_dish_name(dish_name):
# 괄호 안의 알레르기
