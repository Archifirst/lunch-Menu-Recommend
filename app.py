import streamlit as st
import random
import time
import requests
import urllib.parse
import re
import folium
from streamlit_folium import st_folium

# API Key 보안 처리: st.secrets 우선 로드, 없을 시 기본값 fallback
KAKAO_REST_KEY = st.secrets.get("KAKAO_REST_KEY", "bb9c8bfabfc3d5a4c0dbdb3312d8ca30").strip()

st.set_page_config(page_title="오늘 점심 뭐 먹지?", page_icon="🍱", layout="centered")

# --- UI/UX 전체 톤앤매너 커스텀 CSS ---
st.markdown(
    """
    <style>
    /* 전체 배경 및 폰트 렌더링 */
    .stApp {
        background-color: #FAF8F5;
        font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Apple SD Gothic Neo", sans-serif;
    }
    
    /* 입력창 디자인 */
    div[data-baseweb="input"] {
        border-radius: 12px !important;
        border: 1.5px solid #E6DFD5 !important;
        background-color: #FFFFFF !important;
        height: 42px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #E86A3E !important;
        box-shadow: 0 0 0 2px rgba(232, 106, 62, 0.15) !important;
    }
    
    /* 탭 디자인: 5:5 반반 균등 분할 및 캡슐 세그먼트 */
    div[data-testid="stTabs"] {
        background-color: #F1ECE6;
        padding: 5px;
        border-radius: 16px;
        margin-bottom: 14px;
    }
    div[data-testid="stTabs"] div[role="tablist"] {
        display: flex !important;
        width: 100% !important;
        gap: 6px !important;
        border-bottom: none !important;
    }
    button[data-baseweb="tab"] {
        flex: 1 1 0% !important;
        width: 50% !important;
        text-align: center !important;
        justify-content: center !important;
        border-radius: 12px !important;
        padding: 10px 0 !important;
        font-size: 14.5px !important;
        font-weight: 700 !important;
        color: #7A6F66 !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 0.25s ease !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2E1C10 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    }
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* 반경 선택창 부드러운 노출 애니메이션 */
    @keyframes fadeSlideDown {
        from {
            opacity: 0;
            transform: translateY(-8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .radius-wrapper {
        animation: fadeSlideDown 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    
    /* 메인 룰렛 돌리기 버튼 커스텀 */
    div.stButton > button[kind="primary"] {
        background-color: #E86A3E !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        height: 48px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(232, 106, 62, 0.25) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #D65A2F !important;
        box-shadow: 0 6px 16px rgba(232, 106, 62, 0.35) !important;
        transform: translateY(-1px);
    }
    
    /* 일반 버튼 및 기분 버튼 디자인 통일 */
    div.stButton > button[kind="secondary"] {
        border-radius: 14px !important;
        border: 1.5px solid #EDE4DC !important;
        background-color: #FFFFFF !important;
        color: #3E3228 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 10px 14px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #E86A3E !important;
        color: #E86A3E !important;
        background-color: #FFFDF9 !important;
        box-shadow: 0 4px 12px rgba(232, 106, 62, 0.12) !important;
        transform: translateY(-1px);
    }
    
    /* 반경 토글 버튼 전용 크기 */
    div[data-testid="stColumn"] > div > div > div.stButton > button {
        height: 42px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 세션 초기화
if "selected_radius_preset" not in st.session_state:
    st.session_state.selected_radius_preset = "🚲"
if "saved_result" not in st.session_state:
    st.session_state.saved_result = None
if "spin_count" not in st.session_state:
    st.session_state.spin_count = 0
if "gps_coords" not in st.session_state:
    st.session_state.gps_coords = None
if "region_input_val" not in st.session_state:
    st.session_state.region_input_val = ""

PRESET_RADIUS = {
    "🚶": 0.7,
    "🚲": 1.8,
    "🚗": 3.5,
    "직접 입력": None
}

# --- 1. 술집 / 유흥업종 제외 ---
EXCLUDED_CATEGORIES = [
    "술집", "주점", "호프", "포차", "이자카야", "바(BAR)", "요리주점", "와인바",
    "칵테일바", "민속주점", "맥주", "룸살롱", "단란주점", "유흥주점", "라이브카페", "나이트클럽"
]

EXCLUDED_NAME_KEYWORDS = [
    "포차", "주점", "호프", "이자카야", "술집", "맥주", "와인", "펍", "PUB", "비어",
    "BEER", "라운지", "BAR", "룸", "노래방", "포장마차", "야시장", "소주"
]

# --- 2. 전류 / 주막 / 막걸리집 제외 (육전 허용) ---
JEON_KEYWORDS = [
    "파전", "빈대떡", "모듬전", "부침개", "지짐이", "지짐", "전집", 
    "전나라", "전마을", "전선생", "종로전", "원조전", "전골목", "주막", 
    "막걸리", "동동주", "산울림", "탁주"
]

# --- 3. 늦은 시간 / 심야 / 야식 운영 키워드 제외 ---
LATE_NIGHT_KEYWORDS = [
    "심야", "야식", "야간", "새벽", "올나잇", "달빛", "24시", "24시간", 
    "밤식당", "야포", "야한", "불밤", "야시장", "심야식당"
]

# --- 4. 점심 부적합 업종 (구이류, 고깃집, 치킨, 꼬치, 닭발 등) 제외 ---
NON_LUNCH_CATEGORIES = [
    "삼겹살", "갈비", "육류,고기구이", "곱창,막창", "양꼬치", "조개구이",
    "치킨", "닭요리 > 치킨", "닭꼬치", "꼬치구이", "전,빈대떡", "닭발"
]

NON_LUNCH_NAME_KEYWORDS = [
    "닭발", "불닭발", "국물닭발", "통닭발", "무뼈닭발", "신닭발", "한신포차",
    "숯불", "연탄", "화로", "짚불", "구이", "삼겹살", "오겹살", "목살", "뒷고기", "생고기",
    "차돌", "대패", "정육식당", "갈비", "갈매기", "소고기", "한우", "곱창", "막창",
    "대창", "특양", "양꼬치", "양갈비", "조개구이", "장어구이",
    "꼬치", "닭꼬치", "수제꼬치", "야키토리", "쿠시카츠",
    "치킨", "통닭", "닭강정", "켄터키", "BHC", "BBQ", "교촌", "굽네", "처갓집", "노랑통닭"
]

# --- 5. 술 안주 메뉴 키워드 ---
DRINK_SNACK_KEYWORDS = [
    "황도", "과일안주", "과일화채", "화채", "마른안주", "먹태", "노가리", "한치", 
    "쥐포", "육포", "골뱅이소면", "골뱅이무침", "두부김치", "어묵탕", "오뎅탕", 
    "번데기탕", "모듬소시지", "소세지야채볶음", "견과류", "모둠견과", 
    "나초", "모듬포", "문어숙회", "오징어숙회", "골뱅이"
]

# --- 6. 저녁 위주 횟집/수산시장 제외 키워드 ---
EVENING_RAW_FISH_KEYWORDS = [
    "횟집", "회센타", "회센터", "수산", "회타운", "활어", "선어", "막회", "숙성회",
    "모듬회", "물회마차", "포차회", "바다마차", "해물포차", "해산물포차", "참치정육점"
]

# --- 7. 종합 다메뉴 프랜차이즈 ---
MULTI_MENU_FRANCHISES = [
    "국수나무", "미소야", "역전우동", "한솥", "도시락",
    "김밥천국", "고봉민", "김가네", "얌샘", "싸다김밥", "종로김밥", 
    "선비꼬마김밥", "마녀김밥", "바르다김선생", "밥버거", "토마토김밥",
    "분식천국", "나드리김밥", "소풍김밥"
]

# --- 8. 프랜차이즈 판별용 키워드 ---
KNOWN_FRANCHISE_BRANDS = [
    "김밥천국", "고봉민", "김가네", "얌샘", "싸다김밥", "종로김밥", "선비꼬마김밥",
    "마녀김밥", "바르다김선생", "밥버거", "토마토김밥", "국수나무", "미소야", "역전우동",
    "한솥", "본죽", "신전떡볶이", "동대문엽기", "죠스떡볶이", "청년다방", "두끼",
    "홍콩반점", "교동짬뽕", "백소정", "카츠젠", "봉구스", "롤링파스타", "서브웨이",
    "맥도날드", "롯데리아", "버거킹", "노브랜드버거", "맘스터치", "KFC",
    "상무초밥", "쿠우쿠우", "스시로", "갓덴스시", "미카도스시"
]

BUNSIK_ALLOW_MENUS = {"김밥", "떡볶이", "라면", "분식"}

STRICT_SPECIALTY_NAME_RULES = {
    "칼국수": ["칼국수"],
    "막국수": ["막국수"],
    "순대국": ["순대", "순댓국"],
    "뼈해장국": ["해장국", "감자탕", "뼈"],
    "초밥": ["스시", "초밥"],
    "김밥": ["김밥"]
}

TONKATSU_NAME_INDICATORS = [
    "돈까스", "돈가스", "카츠", "카쯔", "가츠", "돈카츠", "돈카쯔", "포크커틀릿"
]

# --- 9. 전국 점심 대표 메뉴 풀 (65종) ---
DEFAULT_FOODS = [
    ("김치찌개", "🥘🔥", "김치찌개 전문점", ["찌개", "한식", "백반"]),
    ("된장찌개", "🍲🫕", "된장찌개 백반", ["찌개", "한식", "백반"]),
    ("순두부찌개", "🍲✨", "순두부찌개 전문점", ["순두부", "찌개", "한식"]),
    ("부대찌개", "🥘🥓", "부대찌개 전문점", ["부대찌개", "찌개"]),
    ("청국장", "🫕🌱", "청국장 전문점", ["청국장", "한식", "백반"]),
    ("동태탕", "🐟🍲", "동태탕 전문점", ["동태탕", "찌개", "한식"]),
    ("순대국", "🍲🥣", "순대국 전문점", ["순대", "국밥", "한식"]),
    ("뼈해장국", "🍖🍲", "뼈해장국", ["감자탕", "해장국", "국밥"]),
    ("설렁탕", "🥣🥛", "설렁탕 전문점", ["설렁탕", "곰탕", "국밥"]),
    ("곰탕", "🥣🥩", "곰탕 전문점", ["곰탕", "설렁탕", "국밥"]),
    ("갈비탕", "🍖🥢", "갈비탕 전문점", ["갈비탕", "한식"]),
    ("삼계탕", "🍗🌾", "삼계탕 전문점", ["삼계탕", "한식"]),
    ("추어탕", "🍲🌿", "추어탕 전문점", ["추어탕", "한식"]),
    ("육개장", "🌶️🥩", "육개장 전문점", ["육개장", "국밥", "한식"]),
    ("콩나물국밥", "🍲🥚", "콩나물국밥 전문점", ["콩나물국밥", "국밥"]),
    ("황태해장국", "🥣🐟", "황태해장국 전문점", ["해장국", "한식"]),
    ("선지해장국", "🥘🩸", "선지해장국 전문점", ["해장국", "국밥"]),
    ("도가니탕", "🥣🦴", "도가니탕 전문점", ["도가니탕", "곰탕"]),
    ("백반", "🍱🥢", "백반 가정식", ["백반", "가정식", "한식", "기사식당"]),
    ("제육볶음", "🔥🥩", "제육볶음 정식", ["한식", "백반", "식당"]),
    ("오징어볶음", "🦑🌶️", "오징어볶음 백반", ["한식", "백반"]),
    ("낙지볶음", "🐙🔥", "낙지볶음 전문점", ["낙지", "한식"]),
    ("쭈꾸미볶음", "🐙🌶️", "쭈꾸미 전문점", ["쭈꾸미", "한식"]),
    ("돌솥비빔밥", "🍳🥘", "비빔밥 전문점", ["비빔밥", "한식"]),
    ("보리밥정식", "🥣🥬", "보리밥 정식", ["보리밥", "한식"]),
    ("쌈밥정식", "🥬🥩", "쌈밥 정식", ["쌈밥", "한식"]),
    ("생선구이백반", "🐟🔥", "생선구이 백반", ["생선구이", "백반"]),
    ("닭갈비", "🥘🍗", "닭갈비 전문점", ["닭갈비", "한식"]),
    ("찜닭", "🍗🥔", "찜닭 전문점", ["찜닭", "한식"]),
    ("코다리조림", "🐟🌶️", "코다리조림 전문점", ["코다리", "한식"]),
    ("간장게장백반", "🦀🍚", "게장 정식", ["게장", "한식"]),
    ("칼국수", "🍜🥢", "칼국수 전문점", ["칼국수", "국수", "한식"]),
    ("수제비", "🥣🥄", "수제비 전문점", ["수제비", "칼국수", "한식"]),
    ("막국수", "🍜🧊", "막국수 전문점", ["막국수", "국수", "한식"]),
    ("냉면", "🧊🥢", "함흥 평양 냉면 전문점", ["냉면", "한식"]),
    ("잔치국수", "🍜🥚", "국수 전문점", ["국수", "한식"]),
    ("비빔국수", "🌶️🥢", "비빔국수 전문점", ["국수", "분식"]),
    ("소바", "🥢🧊", "메밀소바 모밀 전문점", ["일식", "소바"]),
    ("전복죽", "🥣✨", "전복죽 전문점", ["죽", "한식"]),
    ("돈까스", "🍛🍱", "돈까스 카츠 전문점", ["돈가스", "일식", "경양식", "양식"]),
    ("초밥", "🍣🥢", "스시 초밥 전문점", ["일식", "초밥"]),
    ("일본라멘", "🍜🥚", "일본라멘 전문점", ["라멘", "일식"]),
    ("우동", "🍜🍥", "사누키 우동 전문점", ["우동", "일식"]),
    ("사케동", "🍣🍚", "연어덮밥 사케동", ["일식", "덮밥"]),
    ("가츠동", "🍱🥚", "돈부리 덮밥 전문점", ["일식", "덮밥"]),
    ("텐동", "🍤🍚", "텐동 전문점", ["텐동", "일식"]),
    ("회덮밥", "🥗🐟", "활어 회덮밥", ["일식", "한식"]),
    ("카레라이스", "🍛🥄", "일본카레 전문점", ["카레", "일식"]),
    ("짜장면", "🥢🧅", "짜장면", ["중식", "중화요리", "중국집"]),
    ("짬뽕", "🌶🍜", "짬뽕", ["중식", "중화요리", "중국집"]),
    ("볶음밥", "🍚🍳", "중화 볶음밥", ["중식", "중국집"]),
    ("마파두부밥", "🍛🌶️", "마파두부", ["중식", "중화요리"]),
    ("마라탕", "🌶️🍲", "마라탕 전문점", ["중식", "마라탕"]),
    ("파스타", "🍝🍅", "파스타 레스토랑", ["양식", "이탈리안", "패밀리레스토랑"]),
    ("피자", "🍕🧀", "화덕피자", ["피자", "양식", "이탈리안"]),
    ("수제버거", "🍔🍟", "수제버거 전문점", ["햄버거", "패스트푸드"]),
    ("스테이크덮밥", "🥩🍚", "스테이크 덮밥", ["양식", "일식"]),
    ("리조또", "🥘🧀", "이탈리안 리조또", ["양식", "이탈리안"]),
    ("쌀국수", "🍜🌿", "베트남 쌀국수", ["아시아음식", "베트남음식", "쌀국수"]),
    ("팟타이", "🥢🥜", "태국음식 팟타이", ["아시아음식", "태국음식"]),
    ("나시고랭", "🍛🍳", "인도네시아 나시고랭", ["아시아음식"]),
    ("타코", "🌮🥑", "멕시칸 타코", ["남미음식", "멕시칸"]),
    ("포케", "🥗🥑", "하와이안 포케", ["샐러드", "다이어트"]),
    ("샌드위치", "🥪🥪", "수제 샌드위치", ["샌드위치", "샐러드"]),
    ("떡볶이", "🌶️🍢", "떡볶이 전문점", ["분식", "떡볶이"]),
    ("김밥", "🍙🥢", "김밥 전문점", ["김밥"])
]

MOOD_DATA = {
    "🥳 기분좋음": (
        "양식·일식·특식", 
        ["파스타", "피자", "수제버거", "초밥", "돈까스", "텐동", "스테이크덮밥", "타코"]
    ),
    "🤯 스트레스": (
        "화끈·얼큰·매콤", 
        ["짬뽕", "마라탕", "떡볶이", "낙지볶음", "쭈꾸미볶음", "제육볶음", "닭갈비", "육개장"]
    ),
    "😴 피곤·보양": (
        "든든한 국밥·보양 뚝배기", 
        ["순대국", "뼈해장국", "설렁탕", "갈비탕", "삼계탕", "추어탕", "백반", "곰탕"]
    ),
    "☔ 흐림·비": (
        "따끈한 국물과 면 요리", 
        ["칼국수", "수제비", "김치찌개", "부대찌개", "일본라멘", "우동", "쌀국수", "짬뽕"]
    ),
    "🫠 입맛없음": (
        "산뜻·시원한 별미", 
        ["막국수", "냉면", "소바", "포케", "비빔국수", "회덮밥", "돌솥비빔밥", "샌드위치"]
    ),
    "🤢 속편한식사": (
        "부드럽고 순한 국·죽", 
        ["순두부찌개", "콩나물국밥", "황태해장국", "전복죽", "보리밥정식", "된장찌개"]
    )
}

# --- 점심시간(10:00~14:00) 영업 & 술안주 미판매 검증 함수 ---
def verify_place_details(place_id: str) -> bool:
    try:
        url = f"https://place.map.kakao.com/main/v/{place_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=1.8)
        if res.status_code != 200:
            return True

        data = res.json()

        menu_info = data.get("menuInfo", {})
        menu_list = menu_info.get("menuList", [])
        for m in menu_list:
            m_name = m.get("menu", "").replace(" ", "")
            if any(snack in m_name for snack in DRINK_SNACK_KEYWORDS):
                return False

        basic_info = data.get("basicInfo", {})
        open_hour_info = basic_info.get("openHour", {})
        period_list = open_hour_info.get("periodList", [])
        
        if period_list:
            for period in period_list:
                time_list = period.get("timeList", [])
                for t in time_list:
                    time_se = t.get("timeSE", "")
                    if not time_se:
                        continue
                    times = re.findall(r"(\d{1,2}):(\d{2})", time_se)
                    if len(times) >= 2:
                        start_h = int(times[0][0]) + int(times[0][1]) / 60.0
                        end_h = int(times[1][0]) + int(times[1][1]) / 60.0
                        if end_h < start_h:
                            end_h += 24.0
                        
                        if end_h <= 10.0 or start_h >= 14.0:
                            return False

        return True
    except Exception:
        return True


# --- 점심 전문 식당 판정 엔진 ---
def is_valid_specialized_restaurant(menu_name: str, place_name: str, category_name: str) -> bool:
    clean_name = place_name.replace(" ", "").upper()

    if any(ex in category_name for ex in EXCLUDED_CATEGORIES):
        return False
    if any(bad in clean_name for bad in [k.upper() for k in EXCLUDED_NAME_KEYWORDS]):
        return False

    if any(jeon in clean_name for jeon in JEON_KEYWORDS):
        return False
    if any(c in category_name for c in ["전,빈대떡", "빈대떡", "민속주점"]):
        return False

    if any(late in clean_name for late in LATE_NIGHT_KEYWORDS):
        return False
    if any(late in category_name for late in ["심야", "야식"]):
        return False

    if any(c in category_name for c in ["카페", "디저트", "제과,베이커리"]):
        return False

    if any(non in category_name for non in NON_LUNCH_CATEGORIES):
        return False
    if any(bad in clean_name for bad in [k.upper() for k in NON_LUNCH_NAME_KEYWORDS]):
        return False

    if menu_name not in BUNSIK_ALLOW_MENUS:
        if any(brand in clean_name for brand in MULTI_MENU_FRANCHISES):
            return False
        if "분식" in category_name and not any(k in category_name for k in ["일식", "양식", "한식", "중식", "아시아음식"]):
            return False

    if menu_name == "초밥":
        if any(fish in clean_name for fish in EVENING_RAW_FISH_KEYWORDS):
            return False
        if "해물,생선 > 회" in category_name and not any(k in clean_name for k in ["스시", "초밥"]):
            return False

    if menu_name == "돈까스":
        is_tonkatsu_name = any(k in clean_name for k in TONKATSU_NAME_INDICATORS)
        is_tonkatsu_category = any(c in category_name for c in ["돈가스", "돈까스"])
        if not (is_tonkatsu_name or is_tonkatsu_category):
            return False
        return True

    if menu_name in STRICT_SPECIALTY_NAME_RULES:
        required_words = STRICT_SPECIALTY_NAME_RULES[menu_name]
        if not any(req in clean_name for req in required_words):
            return False

    return True


def calculate_restaurant_priority(place: dict, menu_name: str) -> float:
    p_name = place["name"]
    category = place["category"]
    dist = place["dist"]

    score = dist

    is_franchise = any(f_name in p_name for f_name in KNOWN_FRANCHISE_BRANDS)
    if any(p_name.strip().endswith(sfx) for sfx in ["점", "호점", "직영점"]):
        is_franchise = True

    if is_franchise:
        score += 3.0
        place["is_personal"] = False
    else:
        score -= 0.5
        place["is_personal"] = True

    if menu_name == "돈까스":
        if any(k in p_name for k in TONKATSU_NAME_INDICATORS):
            score -= 2.5

    if menu_name == "김밥":
        is_gimbap_specialist = ("김밥" in p_name) or ("김밥" in category)
        is_bunsik_general = ("분식" in category) and not is_gimbap_specialist
        if is_gimbap_specialist:
            score -= 2.0
        elif is_bunsik_general:
            score += 4.0

    if menu_name == "초밥":
        is_sushi_specialist = any(k in p_name for k in ["스시", "초밥", "SUSHI"]) or ("초밥" in category)
        is_raw_fish = ("회" in category) or ("수산" in category) or ("회" in p_name)
        if is_sushi_specialist:
            score -= 3.5
        elif is_raw_fish:
            score += 3.0

    if menu_name in ["칼국수", "막국수"]:
        if menu_name in p_name:
            score -= 2.5

    return score


# --- 카카오 공식 API 연동 함수 ---

def kakao_get_coordinates(query: str):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {"query": query.strip(), "size": 1}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=4.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                return float(docs[0]["y"]), float(docs[0]["x"])
    except Exception:
        pass
    return None, None


def kakao_reverse_geocode(lat: float, lng: float) -> str:
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {"x": str(lng), "y": str(lat)}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=3.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            for d in docs:
                if d.get("region_type") == "H":
                    return f"{d.get('region_2depth_name', '')} {d.get('region_3depth_name', '')}".strip()
            if docs:
                return docs[0].get("address_name", "내 위치")
    except Exception:
        pass
    return "내 위치"


def kakao_search_places(lat: float, lng: float, menu_name: str, search_query: str, radius_km: float = 1.8):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    radius_meters = int(radius_km * 1000)

    params = {
        "query": search_query,
        "category_group_code": "FD6",
        "x": str(lng),
        "y": str(lat),
        "radius": min(radius_meters, 20000),
        "sort": "distance",
        "size": 15
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=4.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            places = []
            
            for d in docs:
                p_id = d.get("id", "")
                p_name = d.get("place_name", "")
                cat_name = d.get("category_name", "")

                if not is_valid_specialized_restaurant(menu_name, p_name, cat_name):
                    continue

                if p_id and not verify_place_details(p_id):
                    continue

                dist_m = float(d.get("distance", 0))
                place_dict = {
                    "name": p_name,
                    "category": cat_name.split(">")[-1].strip() if ">" in cat_name else cat_name,
                    "lat": float(d.get("y")),
                    "lng": float(d.get("x")),
                    "dist": round(dist_m / 1000, 2) if dist_m > 0 else 0.1,
                    "address": d.get("road_address_name") or d.get("address_name", ""),
                    "place_url": d.get("place_url", "")
                }

                place_dict["priority_score"] = calculate_restaurant_priority(place_dict, menu_name)
                places.append(place_dict)

            places.sort(key=lambda x: x["priority_score"])
            return places
    except Exception:
        pass
    return []


# 브라우저 GPS 수신 처리 (안전하게 clear() 처리)
qp = st.query_params
if qp.get("action") == "gps" and "lat" in qp and "lng" in qp:
    try:
        lat_f = float(qp.get("lat"))
        lng_f = float(qp.get("lng"))
        if st.session_state.gps_coords != (lat_f, lng_f):
            st.session_state.gps_coords = (lat_f, lng_f)
            detected_name = kakao_reverse_geocode(lat_f, lng_f)
            st.session_state.region_input_val = detected_name
            st.toast(f"현재 위치: '{detected_name}' 감지 완료!", icon="✅")
    except Exception:
        pass
    st.query_params.clear()


# --- 화면 레이아웃 상단부 ---
st.markdown("<h1 style='color: #2E1C10; font-size: 28px; font-weight: 800; margin-bottom: 2px;'>🍱 오늘 점심 뭐 먹지?</h1>", unsafe_allow_html=True)
st.markdown("<div style='color: #8C827A; font-size: 13.5px; margin-bottom: 20px;'>점심에 집중하는 근처 로컬 밥집만 쏙 골라 추천합니다.</div>", unsafe_allow_html=True)

# 1. 위치 입력창
st.markdown("<div style='margin-bottom: 6px; font-size: 14px; font-weight: 600; color: #4A4036;'>📍 위치</div>", unsafe_allow_html=True)

col_input, col_gps = st.columns([3.5, 1.2], vertical_alignment="center")

with col_input:
    region = st.text_input(
        "위치입력",
        value=st.session_state.region_input_val,
        placeholder="예시) 강남구, 서울역, 코엑스 등",
        key="main_region_input",
        label_visibility="collapsed"
    )
    if region != st.session_state.region_input_val:
        st.session_state.gps_coords = None

with col_gps:
    st.markdown(
        """
        <button onclick="
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(pos) {
                    const url = new URL(window.location.href);
                    url.searchParams.set('action', 'gps');
                    url.searchParams.set('lat', pos.coords.latitude);
                    url.searchParams.set('lng', pos.coords.longitude);
                    window.location.href = url.href;
                }, function(err) {
                    alert('위치 권한을 허용해 주세요!');
                });
            } else {
                alert('GPS를 지원하지 않는 브라우저입니다.');
            }
        " style="width:100%; height:42px; background-color:#E86A3E; color:white; border:none; border-radius:12px; font-size:13.5px; font-weight:700; cursor:pointer; box-shadow: 0 2px 8px rgba(232, 106, 62, 0.2); transition: background-color 0.2s ease;">
            내 위치 찾기
        </button>
        """,
        unsafe_allow_html=True
    )

# 2. 지명 vs 건물/역 판별
clean_region = region.strip()
is_admin_region = False
if clean_region:
    if any(clean_region.endswith(sfx) for sfx in ["구", "동", "읍", "면", "리", "시", "군", "가"]):
        is_admin_region = True

# 건물이거나 역, 랜드마크일 때만 탐색반경 노출
if not is_admin_region:
    st.markdown("<div class='radius-wrapper'>", unsafe_allow_html=True)
    st.markdown("<div style='margin: 18px 0 6px 0; font-size: 14px; font-weight: 600; color: #4A4036;'>📏 탐색 반경</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.0, 1.5], vertical_alignment="center")

    with c1:
        btn_type = "primary" if st.session_state.selected_radius_preset == "🚶" else "secondary"
        if st.button("🚶", key="rbtn_walk", type=btn_type, use_container_width=True):
            st.session_state.selected_radius_preset = "🚶"
            st.rerun()

    with c2:
        btn_type = "primary" if st.session_state.selected_radius_preset == "🚲" else "secondary"
        if st.button("🚲", key="rbtn_bike", type=btn_type, use_container_width=True):
            st.session_state.selected_radius_preset = "🚲"
            st.rerun()

    with c3:
        btn_type = "primary" if st.session_state.selected_radius_preset == "🚗" else "secondary"
        if st.button("🚗", key="rbtn_car", type=btn_type, use_container_width=True):
            st.session_state.selected_radius_preset = "🚗"
            st.rerun()

    with c4:
        btn_type = "primary" if st.session_state.selected_radius_preset == "직접 입력" else "secondary"
        if st.button("직접 입력", key="rbtn_custom", type=btn_type, use_container_width=True):
            st.session_state.selected_radius_preset = "직접 입력"
            st.rerun()

    selected_preset = st.session_state.selected_radius_preset
    if selected_preset == "직접 입력":
        manual_radius = st.number_input("희망 반경 (단위: km)", min_value=0.2, max_value=10.0, value=2.0, step=0.2)
        radius_km = float(manual_radius)
        radius_display_text = f"직접 입력 {radius_km:.1f}km"
    else:
        radius_km = PRESET_RADIUS[selected_preset]
        name_map = {"🚶": "도보 700m", "🚲": "자전거 1.8km", "🚗": "차량 3.5km"}
        radius_display_text = name_map[selected_preset]
    st.markdown("</div>", unsafe_allow_html=True)
else:
    radius_km = 1.8
    radius_display_text = "지역 인근"

# 3. 위치 미입력 경고 영역
region_warning_spot = st.empty()
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# 4. 룰렛 탭
tab1, tab2 = st.tabs(["🎲 랜덤 룰렛", "✨ 기분 & 상황별 룰렛"])

spin_triggered = False
selected_candidates = []

def show_location_warning():
    region_warning_spot.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; gap: 8px;
                    width: 100%; height: 48px; margin: 8px 0 12px 0;
                    background-color: #FFFDF7; border: 1.5px solid #F7D488; border-radius: 14px;
                    box-shadow: 0 3px 10px rgba(247, 212, 136, 0.2);">
            <span style="font-size: 18px; line-height: 1;">⚠️</span>
            <span style="color: #6C4D0A; font-size: 14px; font-weight: 700; line-height: 1;">
                위치를 입력하거나 '내 위치 찾기'를 눌러주세요!
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

with tab1:
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    if st.button("🎲 룰렛 돌리기", use_container_width=True, type="primary", key="btn_random"):
        if not region.strip() and not st.session_state.gps_coords:
            show_location_warning()
        else:
            region_warning_spot.empty()
            selected_candidates = DEFAULT_FOODS.copy()
            spin_triggered = True

with tab2:
    selected_mood = None
    st.markdown(
        """
        <div style='text-align: center; color: #7A6F66; font-size: 13px; font-weight: 500; margin-bottom: 12px;'>
            지금 기분이나 컨디션에 딱 맞는 한 끼를 골라보세요
        </div>
        """,
        unsafe_allow_html=True
    )
    col_m1, col_m2 = st.columns(2)
    mood_keys = list(MOOD_DATA.keys())

    with col_m1:
        for k in mood_keys[:3]:
            desc, _ = MOOD_DATA[k]
            btn_label = f"{k}\n({desc})"
            if st.button(btn_label, use_container_width=True, key=f"btn_{k}"):
                selected_mood = k

    with col_m2:
        for k in mood_keys[3:]:
            desc, _ = MOOD_DATA[k]
            btn_label = f"{k}\n({desc})"
            if st.button(btn_label, use_container_width=True, key=f"btn_{k}"):
                selected_mood = k

    if selected_mood:
        if not region.strip() and not st.session_state.gps_coords:
            show_location_warning()
        else:
            region_warning_spot.empty()
            _, allowed_names = MOOD_DATA[selected_mood]
            filtered = [f for f in DEFAULT_FOODS if f[0] in allowed_names]
            selected_candidates = filtered if filtered else DEFAULT_FOODS
            spin_triggered = True

card_spot = st.empty()
detail_spot = st.empty()

# 5. 탐색 및 추첨 실행
if spin_triggered and selected_candidates:
    detail_spot.empty()

    if st.session_state.gps_coords:
        c_lat, c_lng = st.session_state.gps_coords
    else:
        with st.spinner(f"카카오맵에서 '{region}' 위치를 확인하고 있습니다..."):
            c_lat, c_lng = kakao_get_coordinates(region)

    if not c_lat:
        region_warning_spot.error(f"⚠️ '{region}' 위치를 찾지 못했습니다. 지명이나 동 이름을 입력해 보세요.")
    else:
        final_menu = None
        places = []

        shuffled = selected_candidates.copy()
        random.shuffle(shuffled)

        with st.spinner("점심 전문 식당을 엄선 중입니다..."):
            for m_name, m_emoji, m_kw, m_tags in shuffled:
                found = kakao_search_places(c_lat, c_lng, m_name, m_kw, radius_km=radius_km)
                if found:
                    final_menu = (m_name, m_emoji)
                    places = found
                    break

            if not places:
                fallback_found = kakao_search_places(c_lat, c_lng, "백반", "백반 가정식", radius_km=radius_km)
                if fallback_found:
                    final_menu = ("백반·가정식", "🍱🥢")
                    places = fallback_found

        if final_menu and places:
            for i in range(7):
                temp = random.choice(selected_candidates)
                card_spot.markdown(
                    f"""
                    <div style="text-align: center; margin: 24px 0 16px 0; padding: 26px 20px; 
                                background: #FFFDF9; border-radius: 22px; border: 1.5px solid #F5D5B8;
                                box-shadow: 0 4px 18px rgba(245, 213, 184, 0.35);">
                        <div style="font-size: 65px; margin-bottom: 4px;">{temp[1]}</div>
                        <div style="color: #2E1C10; font-size: 26px; font-weight: 800; margin: 6px 0;">{temp[0]}</div>
                        <p style="color: #8C827A; font-size: 13px; margin: 0;">{radius_display_text} 기준 순수 밥집 찾는 중... 🎲</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                time.sleep(0.04 + (i * 0.015))

            # spin_count 1씩 증가시켜 지도 고유 Key 리프레시 보장
            st.session_state.spin_count += 1
            st.session_state.saved_result = {
                "menu": final_menu[0],
                "emoji": final_menu[1],
                "places": places,
                "region": region or "내 위치",
                "radius_text": radius_display_text,
                "center_lat": c_lat,
                "center_lng": c_lng,
                "id": st.session_state.spin_count
            }
        else:
            region_warning_spot.warning(f"⚠️ '{region}' 반경 내에 순수 점심 식사 매장을 찾지 못했습니다. 탐색 반경을 넓혀보세요!")

# 6. 결과 화면 출력
res = st.session_state.saved_result
if res is not None and res.get("places"):
    card_spot.markdown(
        f"""
        <div style="text-align: center; margin: 20px 0 16px 0; padding: 30px 20px; 
                    background: #FFFDF9; border-radius: 24px; border: 1.5px solid #F5D5B8; 
                    box-shadow: 0 4px 20px rgba(245, 213, 184, 0.35);">
            <div style="font-size: 78px; line-height: 1; margin-bottom: 12px;">{res['emoji']}</div>
            <div style="display: flex; justify-content: center; align-items: center; gap: 8px; width: 100%; margin: 8px 0 6px 0;">
                <span style="font-size: 26px; line-height: 1;">🎉</span>
                <span style="color: #2E1C10; font-size: 30px; font-weight: 800; letter-spacing: -0.5px;">{res['menu']} 당첨!</span>
                <span style="font-size: 26px; line-height: 1;">🎉</span>
            </div>
            <div style="color: #7A6F66; font-size: 13.5px; font-weight: 500; margin-top: 6px;">
                '{res['region']}' 주변 점심 밥집 추천 결과
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with detail_spot.container():
        places = res["places"]
        top_pick = places[0]

        tag_text = "개인 전문점" if top_pick.get("is_personal", True) else "프랜차이즈"
        tag_bg = "#FCEFE6" if top_pick.get("is_personal", True) else "#F7E6D2"
        tag_color = "#C85A32" if top_pick.get("is_personal", True) else "#8A532B"

        st.markdown(
            f"""
            <div style="margin-bottom: 22px; padding: 24px 20px; 
                        background: #FFFDF9; border: 1.5px solid #F5D5B8; border-radius: 24px; 
                        box-shadow: 0 4px 20px rgba(245, 213, 184, 0.35); text-align: center;">
                <div style="display: flex; justify-content: center; align-items: center; gap: 6px; margin-bottom: 10px;">
                    <span style="font-size: 13px; color: #E86A3E; font-weight: 700;">⭐ 오늘의 1픽 추천 점심</span>
                    <span style="font-size: 11px; background: {tag_bg}; color: {tag_color}; padding: 2px 8px; border-radius: 6px; font-weight: 700;">
                        {tag_text}
                    </span>
                    <span style="font-size: 11px; background: #F3ECE4; color: #6E5F55; padding: 2px 8px; border-radius: 6px; font-weight: 600;">
                        {top_pick.get('category', '전문음식점')}
                    </span>
                </div>
                <div style="margin: 6px 0 4px 0;">
                    <a href="{top_pick.get('place_url', '#')}" target="_blank" 
                       style="text-decoration: none; color: #2E1C10; font-size: 26px; font-weight: 900; letter-spacing: -0.5px; display: inline-block;">
                        {top_pick['name']}
                    </a>
                </div>
                <div style="font-size: 13px; color: #7A6F66; margin-top: 6px;">
                    📍 {top_pick['address']} (약 {top_pick['dist']}km)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if len(places) > 1:
            st.markdown(
                f"<div style='font-size: 14px; font-weight: 700; color: #2E1C10; margin-bottom: 10px;'>"
                f"근처 다른 점심 후보 ({len(places)-1}곳)"
                f"</div>",
                unsafe_allow_html=True
            )

            other_candidates = places[1:11]
            col_left, col_right = st.columns(2)

            for idx, p in enumerate(other_candidates, start=1):
                p_tag = "개인" if p.get("is_personal", True) else "체인"
                short_cat = p.get('category', '식당').split('/')[-1].strip()
                target_col = col_left if idx % 2 != 0 else col_right

                with target_col:
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; 
                                    background: #FFFFFF; border: 1px solid #ECE7E1; border-radius: 12px; 
                                    padding: 10px 14px; margin-bottom: 9px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                            <div style="display: flex; align-items: center; gap: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                <span style="display: inline-flex; justify-content: center; align-items: center; width: 20px; height: 20px; background: #F3EFEA; color: #555; border-radius: 6px; font-size: 11px; font-weight: 700;">
                                    {idx}
                                </span>
                                <a href="{p.get('place_url', '#')}" target="_blank" style="text-decoration: none; color: #111; font-size: 13.5px; font-weight: 700; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                    {p['name']}
                                </a>
                                <span style="font-size: 10.5px; background: #F7F5F2; color: #777; padding: 2px 5px; border-radius: 4px;">
                                    {p_tag}·{short_cat}
                                </span>
                            </div>
                            <div style="font-size: 12px; color: #555; font-weight: 500; margin-left: 6px; white-space: nowrap;">
                                {p['dist']}km
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-bottom: 4px; font-size: 18px; font-weight: 800; color: #2E1C10;'>🗺️ 추천 식당 위치 지도</h3>", unsafe_allow_html=True)
        st.caption("🔴 빨간 핀: 1픽 전문점 / 🔵 파란 핀: 주변 후보 (클릭 시 카카오맵 정보)")

        m = folium.Map(location=[top_pick["lat"], top_pick["lng"]], zoom_start=15, control_scale=True)

        folium.Marker(
            location=[top_pick["lat"], top_pick["lng"]],
            popup=folium.Popup(f"<b>⭐ {top_pick['name']}</b><br>{top_pick['address']}<br><a href='{top_pick['place_url']}' target='_blank'>카카오맵 열기</a>", max_width=250),
            tooltip=f"⭐ 1픽: {top_pick['name']}",
            icon=folium.Icon(color="red", icon="star", prefix="fa")
        ).add_to(m)

        for idx, p in enumerate(places[1:10], start=2):
            folium.Marker(
                location=[p["lat"], p["lng"]],
                popup=folium.Popup(f"<b>{idx}. {p['name']}</b><br>{p['address']}<br><a href='{p['place_url']}' target='_blank'>카카오맵 열기</a>", max_width=250),
                tooltip=f"{idx}. {p['name']}",
                icon=folium.Icon(color="blue", icon="utensils", prefix="fa")
            ).add_to(m)

        unique_map_key = f"map_{res['id']}_{int(top_pick['lat'] * 10000)}"
        st_folium(m, width="100%", height=420, key=unique_map_key, returned_objects=[])

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        kakao_map_url = f"https://map.kakao.com/link/search/{urllib.parse.quote(res['region'] + ' ' + res['menu'])}"
        st.link_button("🧭 카카오맵 길찾기 바로가기", kakao_map_url, use_container_width=True)
