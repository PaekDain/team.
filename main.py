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

# 식약처 지정 19가지 알레르기 유발물질 번호 매핑
ALLERGY_MAP = {
    "1": "난류", "2": "우유", "3": "메밀", "4": "땅콩", "5": "대두",
    "6": "밀", "7": "고등어", "8": "게", "9": "새우", "10": "돼지고기",
    "11": "복숭아", "12": "토마토", "13": "아황산류", "14": "호두", "15": "닭고기",
    "16": "쇠고기", "17": "오징어", "18": "조개류(굴,전복,홍합 포함)", "19": "잣"
}

def extract_allergy_info(dish_name):
    if not dish_name:
        return "알레르기 정보가 없습니다."
    
    # 괄호 안의 숫자.숫자 패턴 찾기 (예: (1.5.6))
    raw_numbers = re.findall(r"\(([\d\.]+)\)", dish_name)
    
    found_codes = set()
    for group in raw_numbers:
        # 점(.)으로 구분된 숫자들을 분리
        codes = group.split(".")
        for c in codes:
            if c in ALLERGY_MAP:
                found_codes.add(int(c))
                
    if not found_codes:
        return "표시된 알레르기 유발물질이 없습니다."
    
    # 번호순 정렬 후 식품명 변환
    sorted_codes = sorted(list(found_codes))
    allergy_names = [f"{c}.{ALLERGY_MAP[str(c)]}" for c in sorted_codes]
    
    return ", ".join(allergy_names)
