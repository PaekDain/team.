import os
import sys
import requests
from datetime import datetime

# 송탄고등학교 기본 설정
ATPT_OFCDC_SC_CODE = "J10"  # 경기도교육청
SD_SCHUL_CODE = "7530480"    # 송탄고등학교
DEFAULT_MEAL_CODE = "2"     # 중식

# API 키 설정 (오픈API 환경변수가 없을 경우 공백 처리로 호출 가능)
API_KEY = os.getenv("NEIS_API_KEY", "")

# 조회 가능 범위 설정 (2010년 1월 1일 ~ 2026년 9월 30일)
MIN_DATE = datetime(2010, 1, 1)
MAX_DATE = datetime(2026, 9, 30)

def format_info_text(raw_text: str) -> str:
    """NEIS API에서 <br/> 태그로 구분되어 넘어오는 텍스트를 줄바꿈으로 정제합니다."""
    if not raw_text:
        return "정보 없음"
    cleaned = raw_text.replace("<br/>", "\n").replace("<br>", "\n")
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    return "\n".join(lines)

def validate_date(date_str: str) -> bool:
    """입력된 날짜가 YYYYMMDD 형식이며, 2010.01.01 ~ 2026.09.30 범위 내에 있는지 검증합니다."""
    try:
        input_date = datetime.strptime(date_str, "%Y%m%d")
        if MIN_DATE <= input_date <= MAX_DATE:
            return True
        else:
            print(f"⚠️ 날짜 범위 오류: 2010년 01월 01일부터 2026년 09월 30일 사이의 날짜만 입력 가능합니다.")
            return False
    except ValueError:
        print("⚠️ 입력 형식 오류: YYYYMMDD 형식(예: 20230515)으로 8자리 숫자를 입력해 주세요.")
        return False

def get_meal_info(target_date: str):
    """송탄고등학교의 특정 날짜 급식 정보를 조회하여 출력합니다."""
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    
    params = {
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MMEAL_SC_CODE": DEFAULT_MEAL_CODE,
        "MLSV_YMD": target_date
    }
    
    if API_KEY:
        params["KEY"] = API_KEY

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "mealServiceDietInfo" in data:
            row = data["mealServiceDietInfo"][1]["row"][0]

            schul_nm = row.get("SCHUL_NM", "송탄고등학교")
            mlsv_ymd = row.get("MLSV_YMD", target_date)
            dish_nm = format_info_text(row.get("DDISH_NM", ""))
            orplc_info = format_info_text(row.get("ORPLC_INFO", ""))
            cal_info = row.get("CAL_INFO", "정보 없음")
            ntr_info = format_info_text(row.get("NTR_INFO", ""))

            print("\n" + "=" * 50)
            print(f"🏫 학교명: {schul_nm}")
            print(f"📅 급식일자: {mlsv_ymd[:4]}년 {mlsv_ymd[4:6]}월 {mlsv_ymd[6:]}일")
            print("=" * 50)
            
            print("\n[ 🍱 식단 (메뉴) ]")
            print(dish_nm)
            
            print(f"\n[ 🔥 칼로리 정보 ]\n{cal_info}")
            
            print("\n[ 🥗 영양 정보 ]")
            print(ntr_info)
            
            print("\n[ 🥩 원산지 정보 ]")
            print(orplc_info)
            print("=" * 50 + "\n")

        elif "RESULT" in data:
            print(f"\n❌ 조회 실패: {data['RESULT']['MESSAGE']}\n")
        else:
            print("\n❌ 해당 날짜에는 급식 정보(주말/방학/급식 미실시 등)가 없습니다.\n")

    except requests.exceptions.RequestException as e:
        print(f"\n⚠️ API 요청 중 오류가 발생했습니다: {e}\n")

def main():
    # 명령행 인자가 전달된 경우 (예: python main.py 20240401)
    if len(sys.argv) > 1:
        target_date = sys.argv[1].strip()
        if validate_date(target_date):
            get_meal_info(target_date)
        return

    # 대화형 프롬프트 실행
    print("=" * 50)
    print(" 🍱 송탄고등학교 급식 정보 조회 시스템 (2010.01 ~ 2026.09)")
    print("=" * 50)

    while True:
        user_input = input("조회할 날짜를 입력하세요 (YYYYMMDD 형식, 종료는 'q'): ").strip()
        
        if user_input.lower() in ["q", "quit", "exit"]:
            print("프로그램을 종료합니다.")
            break
        
        if validate_date(user_input):
            get_meal_info(user_input)

if __name__ == "__main__":
    main()
