import streamlit as st
import random
import time
import requests
import urllib.parse
import re
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="오늘 점심 뭐 먹지?", page_icon="🍱", layout="centered")

# --- UI/UX 전체 톤앤매너 및 간격 정돈 커스텀 CSS ---
st.markdown(
    """
    <style>
    :root, .stApp, [data-testid="stAppViewContainer"] {
        --primary-color: #E86A3E !important;
        --primary: #E86A3E !important;
    }

    .stApp {
        background-color: #FAF8F5;
        font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Apple SD Gothic Neo", sans-serif;
    }
    
    .block-container {
        padding-top: 4.0rem !important;
        padding-bottom: 3.6rem !important;
        max-width: 620px !important;
    }

    .section-title {
        font-size: 14.5px !important;
        font-weight: 700 !important;
        color: #3E3228 !important;
        margin-top: 0px !important;
        margin-bottom: 8px !important;
        letter-spacing: -0.3px !important;
        display: flex;
        align-items: center;
        gap: 6px;
    }

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

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px !important;
        border: 1.8px solid #EAE3DB !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.02) !important;
        padding: 16px 16px 16px 16px !important;
        margin-bottom: 14px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] div.stButton > button {
        height: 40px !important;
        border-radius: 11px !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }
    
    button[data-testid*="primary"],
    button[kind="primary"],
    .stButton > button[data-testid*="primary"],
    div[data-testid="stVerticalBlockBorderWrapper"] button[data-testid*="primary"],
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="primary"],
    div[data-testid="stVerticalBlockBorderWrapper"] div.stButton > button[kind="primary"] {
        background-color: #E86A3E !important;
        background: #E86A3E !important;
        border: none !important;
        border-color: transparent !important;
        color: #FFFFFF !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(232, 106, 62, 0.25) !important;
    }

    button[data-testid*="primary"]:hover,
    button[kind="primary"]:hover,
    .stButton > button[data-testid*="primary"]:hover,
    div[data-testid="stVerticalBlockBorderWrapper"] button[data-testid*="primary"]:hover,
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="primary"]:hover {
        background-color: #D65A2F !important;
        background: #D65A2F !important;
        border-color: transparent !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }

    button[data-testid*="primary"] *,
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="primary"] * {
        color: #FFFFFF !important;
    }

    button[data-testid*="primary"]:focus,
    button[data-testid*="primary"]:active {
        background-color: #E86A3E !important;
        background: #E86A3E !important;
        border-color: #E86A3E !important;
        box-shadow: 0 0 0 2px rgba(232, 106, 62, 0.3) !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="secondary"],
    div[data-testid="stVerticalBlockBorderWrapper"] button[data-testid*="secondary"],
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid*="secondary"] > button {
        border: 1.2px solid #EDE4DC !important;
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        color: #3E3228 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        padding: 6px 8px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.02) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="secondary"]:hover,
    div[data-testid="stVerticalBlockBorderWrapper"] button[data-testid*="secondary"]:hover {
        border-color: #E86A3E !important;
        color: #E86A3E !important;
        background: #FFFDF9 !important;
        background-color: #FFFDF9 !important;
        transform: translateY(-1px);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="secondary"] * {
        color: #3E3228 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="secondary"]:hover * {
        color: #E86A3E !important;
    }

    div[data-testid="stColumn"] {
        padding: 0 3px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] div.stButton:not([data-testid="stColumn"] *) {
        margin-top: 6px !important;
        margin-bottom: 0px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] div.stButton:not([data-testid="stColumn"] *) > button {
        margin-bottom: 0px !important;
    }

    @keyframes roulettePulse {
        0% {
            transform: scale(1);
            box-shadow: 0 4px 16px rgba(232, 106, 62, 0.35), 0 0 0 0 rgba(232, 106, 62, 0.5);
        }
        50% {
            transform: scale(1.015);
            box-shadow: 0 8px 24px rgba(232, 106, 62, 0.5), 0 0 0 8px rgba(232, 106, 62, 0);
        }
        100% {
            transform: scale(1);
            box-shadow: 0 4px 16px rgba(232, 106, 62, 0.35), 0 0 0 0 rgba(232, 106, 62, 0);
        }
    }

    /* 룰렛 버튼 컨테이너: 상단 마진을 0으로 맞춤 */
    div.block-container > div[data-testid="stVerticalBlock"] > div.stElementContainer:not(div[data-testid="stVerticalBlockBorderWrapper"] *) div.stButton:has(button[key="btn_trigger_random"]) {
        margin-top: 0px !important;
        margin-bottom: 14px !important;
    }

    div.block-container > div[data-testid="stVerticalBlock"] > div.stElementContainer:not(div[data-testid="stVerticalBlockBorderWrapper"] *) div.stButton > button[key="btn_trigger_random"] {
        height: 64px !important;
        min-height: 64px !important;
        background: linear-gradient(135deg, #FF7B47 0%, #E85A2A 50%, #D84A1A 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 16px !important;
        animation: roulettePulse 2.2s infinite ease-in-out !important;
        cursor: pointer !important;
        box-shadow: 0 4px 16px rgba(232, 106, 62, 0.35) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    div.block-container > div[data-testid="stVerticalBlock"] > div.stElementContainer:not(div[data-testid="stVerticalBlockBorderWrapper"] *) div.stButton > button[key="btn_trigger_random"] p,
    div.block-container > div[data-testid="stVerticalBlock"] > div.stElementContainer:not(div[data-testid="stVerticalBlockBorderWrapper"] *) div.stButton > button[key="btn_trigger_random"] span {
        font-size: 18px !important;
        font-weight: 700 !important;
        letter-spacing: -0.4px !important;
        color: #FFFFFF !important;
        line-height: 1.2 !important;
    }

    div.block-container > div[data-testid="stVerticalBlock"] > div.stElementContainer:not(div[data-testid="stVerticalBlockBorderWrapper"] *) div.stButton > button[key="btn_trigger_random"]:hover {
        background: linear-gradient(135deg, #FF662A 0%, #D64716 100%) !important;
        transform: scale(1.015) !important;
    }

    /* 안내 경고 박스 */
    .warning-box {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        width: 100%;
        min-height: 44px;
        padding: 6px 12px;
        margin: 0 0 14px 0 !important;
        background-color: #FFFDF7;
        border: 1.5px solid #F7D488;
        border-radius: 12px;
        box-sizing: border-box;
    }

    /* [결과 화면] 지도 하단 여백 및 버튼 간격 축소 */
    div.stElementContainer:has(iframe) {
        margin-bottom: -4px !important;
    }

    div.stElementContainer:has(a[kind="secondaryFormSubmit"]),
    div.stElementContainer:has(.stLinkButton) {
        margin-top: 0px !important;
        margin-bottom: 5px !important;
    }

    div.stElementContainer:has(button[key="btn_reset_bottom"]) {
        margin-top: 0px !important;
    }

    @keyframes smoothFadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in-content {
        animation: smoothFadeIn 0.35s ease-out forwards;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- API 키 로드 ---
has_key = "KAKAO_REST_KEY" in st.secrets and bool(st.secrets["KAKAO_REST_KEY"].strip())
KAKAO_REST_KEY = st.secrets["KAKAO_REST_KEY"].strip() if has_key else ""

has_google_key = "GOOGLE_MAPS_KEY" in st.secrets and bool(st.secrets["GOOGLE_MAPS_KEY"].strip())
GOOGLE_MAPS_KEY = st.secrets["GOOGLE_MAPS_KEY"].strip() if has_google_key else ""

PRESET_RADIUS = {
    "인근": 0.7,
    "근거리": 1.8,
    "원거리": 3.5,
    "직접 입력": None
}

if "selected_radius_preset" not in st.session_state or st.session_state.selected_radius_preset not in PRESET_RADIUS:
    st.session_state.selected_radius_preset = "근거리"
if "custom_radius_val" not in st.session_state:
    st.session_state.custom_radius_val = 2.0
if "selected_cuisine" not in st.session_state:
    st.session_state.selected_cuisine = None
if "selected_price" not in st.session_state:
    st.session_state.selected_price = "상관없음"
if "selected_parking" not in st.session_state:
    st.session_state.selected_parking = "주차 불필요"
if "saved_result" not in st.session_state:
    st.session_state.saved_result = None
if "spin_count" not in st.session_state:
    st.session_state.spin_count = 0
if "gps_coords" not in st.session_state:
    st.session_state.gps_coords = None
if "region_input_val" not in st.session_state:
    st.session_state.region_input_val = ""

# --- GPS 좌표 캐싱 및 역지오코딩 처리 ---
@st.cache_data(ttl=86400, show_spinner=False)
def kakao_reverse_geocode(lat: float, lng: float) -> str:
    if not KAKAO_REST_KEY:
        return "내 위치"
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

qp = st.query_params
if qp.get("action") == "gps" and "lat" in qp and "lng" in qp:
    try:
        lat_f = float(qp.get("lat"))
        lng_f = float(qp.get("lng"))
        if st.session_state.gps_coords != (lat_f, lng_f):
            st.session_state.gps_coords = (lat_f, lng_f)
            detected_name = kakao_reverse_geocode(lat_f, lng_f)
            st.session_state.region_input_val = detected_name
            st.session_state.saved_result = None
            st.toast(f"현재 위치 감지: '{detected_name}'", icon="📍")
    except Exception:
        pass
    st.query_params.clear()

# --- 필터링 기준 (유흥/성인업소 및 비식사 시설만 차단) ---
HARD_EXCLUDED_CATEGORIES = [
    "룸살롱", "단란주점", "유흥주점", "나이트클럽", "성인용품", "마사지", "안마", "노래방", "가라오케"
]
CAFE_EXCLUDED_CATEGORIES = [
    "카페", "디저트", "제과,베이커리", "떡,한과", "도넛", "아이스크림"
]
SUSPECT_NIGHT_KEYWORDS = [
    "실내포차", "소주방", "룸호프", "노가리", "맥주창고"
]

# --- 스테이크 검색 시 원천 배제할 분식/도시락/돈까스/패스트푸드 브랜드 및 키워드 ---
STEAK_EXCLUDED_KEYWORDS = [
    "한솥", "도시락", "김밥", "천국", "돈까스", "돈가스", "카츠", "가츠", "카쯔",
    "함박", "함바그", "버거", "맥도날드", "롯데리아", "맘스터치", "버거킹", "토마토김밥",
    "얌샘", "고봉민", "싸다김밥", "분식", "포장마차", "국수나무", "역전우동"
]

# --- 카카오 검색 적중률을 극대화한 메뉴 및 키워드 데이터셋 ---
DEFAULT_FOODS = [
    # 한식
    ("김치찌개", "🥘", "김치찌개", "한식", "low"),
    ("된장찌개", "🍲", "된장찌개", "한식", "low"),
    ("순두부찌개", "🥚", "순두부찌개", "한식", "low"),
    ("부대찌개", "🥓", "부대찌개", "한식", "mid"),
    ("청국장", "🍲", "청국장", "한식", "low"),
    ("동태탕", "🐟", "동태탕", "한식", "mid"),
    ("국밥", "🥣", "국밥", "한식", "low"),
    ("뼈해장국", "🍖", "뼈해장국", "한식", "low"),
    ("설렁탕", "🥣", "설렁탕", "한식", "mid"),
    ("곰탕", "🥩", "곰탕", "한식", "mid"),
    ("갈비탕", "🍖", "갈비탕", "한식", "mid"),
    ("삼계탕", "🍗", "삼계탕", "한식", "mid"),
    ("추어탕", "🍲", "추어탕", "한식", "mid"),
    ("육개장", "🌶", "육개장", "한식", "low"),
    ("콩나물국밥", "🌱", "콩나물국밥", "한식", "low"),
    ("황태해장국", "🐟", "황태해장국", "한식", "low"),
    ("선지해장국", "🥘", "선지해장국", "한식", "low"),
    ("도가니탕", "🥣", "도가니탕", "한식", "high"),
    ("백반", "🍱", "백반", "한식", "low"),
    ("제육볶음", "🔥", "제육볶음", "한식", "low"),
    ("오징어볶음", "🦑", "오징어볶음", "한식", "mid"),
    ("낙지볶음", "🐙", "낙지볶음", "한식", "mid"),
    ("쭈꾸미볶음", "🐙", "쭈꾸미", "한식", "mid"),
    ("비빔밥", "🍳", "비빔밥", "한식", "low"),
    ("보리밥", "🌾", "보리밥", "한식", "low"),
    ("쌈밥", "🥬", "쌈밥", "한식", "mid"),
    ("생선구이", "🐟", "생선구이", "한식", "mid"),
    ("닭갈비", "🍗", "닭갈비", "한식", "mid"),
    ("찜닭", "🥔", "찜닭", "한식", "mid"),
    ("코다리조림", "🐟", "코다리조림", "한식", "mid"),
    ("간장게장", "🦀", "게장", "한식", "high"),
    ("칼국수", "🍜", "칼국수", "한식", "low"),
    ("수제비", "🥣", "수제비", "한식", "low"),
    ("막국수", "🥢", "막국수", "한식", "low"),
    ("냉면", "🧊", "냉면", "한식", "mid"),
    ("잔치국수", "🍜", "잔치국수", "한식", "low"),
    ("비빔국수", "🌶", "비빔국수", "한식", "low"),
    ("떡볶이", "🍢", "떡볶이", "한식", "low"),
    ("김밥", "🍙", "김밥", "한식", "low"),

    # 중식
    ("짜장면", "🥢", "짜장면", "중식", "low"),
    ("짬뽕", "🔥", "짬뽕", "중식", "low"),
    ("중화볶음밥", "🍚", "중국집", "중식", "low"),
    ("마파두부밥", "🍛", "중식당", "중식", "low"),
    ("마라탕", "🌶️", "마라탕", "중식", "mid"),
    ("탕수육정식", "🥟", "중화요리", "중식", "mid"),
    ("딤섬", "🥟", "딤섬", "중식", "high"),

    # 일식
    ("돈까스", "🍱", "돈까스", "일식", "mid"),
    ("초밥", "🍣", "초밥", "일식", "mid"),
    ("일본라멘", "🍜", "라멘", "일식", "mid"),
    ("소바", "🥢", "메밀소바", "일식", "low"),
    ("우동", "🍢", "우동", "일식", "low"),
    ("사케동", "🍣", "사케동", "일식", "mid"),
    ("가츠동", "🍛", "돈부리", "일식", "low"),
    ("텐동", "🍤", "텐동", "일식", "mid"),
    ("회덮밥", "🥗", "회덮밥", "일식", "mid"),
    ("일본카레", "🍛", "카레", "일식", "low"),
    ("오마카세", "🍣", "스시", "일식", "high"),

    # 양식 (스테이크 검색 쿼리를 전문 레스토랑 중심 키워드로 정교화)
    ("파스타", "🍝", "파스타", "양식", "mid"),
    ("피자", "🍕", "화덕피자", "양식", "mid"),
    ("수제버거", "🍔", "수제버거", "양식", "mid"),
    ("스테이크", "🥩", "스테이크 전문점", "양식", "high"),
    ("리조또", "🧀", "이탈리안", "양식", "mid"),
    ("샌드위치", "🥪", "샌드위치", "양식", "low"),
    ("브런치", "🥞", "브런치", "양식", "mid"),

    # 동남아식
    ("쌀국수", "🍜", "쌀국수", "동남아식", "low"),
    ("팟타이", "🥢", "팟타이", "동남아식", "mid"),
    ("나시고랭", "🍳", "나시고랭", "동남아식", "mid"),
    ("분짜", "🥗", "분짜", "동남아식", "mid"),
    ("반미", "🥖", "반미", "동남아식", "low"),
    ("똠얌꿍", "🍲", "태국음식", "동남아식", "high"),

    # 인도식
    ("인도커리", "🍛", "인도커리", "인도식", "mid"),
    ("인도난커리", "🫓", "인도요리", "인도식", "mid"),
    ("탄두리치킨", "🍗", "인도음식", "인도식", "high"),
    ("카레라이스", "🍛", "커리", "인도식", "low"),

    # 멕시코식
    ("타코", "🌮", "타코", "멕시코식", "mid"),
    ("부리또", "🌯", "부리또", "멕시코식", "low"),
    ("퀘사디아", "🫓", "멕시칸", "멕시코식", "mid"),
    ("파히타", "🥘", "멕시코요리", "멕시코식", "high")
]

# --- Google Places API (New) 기반 영업시간 및 상세 정보 분석 ---
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_google_place_details(place_name: str, lat: float, lng: float) -> dict:
    default_res = {
        "found": False,
        "is_lunch_open": None,
        "open_now": None,
        "today_hours_text": "",
        "price_level_text": "",
        "parking_info": "",
        "primary_type": "",
        "rating": None,
        "user_rating_count": None
    }

    if not GOOGLE_MAPS_KEY:
        return default_res

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_KEY,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.primaryTypeDisplayName,"
            "places.regularOpeningHours,places.currentOpeningHours,"
            "places.priceLevel,places.parkingOptions,places.rating,places.userRatingCount"
        )
    }

    clean_name = place_name.split()[0]
    payload = {
        "textQuery": clean_name,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": 400.0
            }
        },
        "maxResultCount": 1,
        "languageCode": "ko"
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=2.5)
        if res.status_code == 200:
            places = res.json().get("places", [])
            if not places:
                return default_res

            p = places[0]
            default_res["found"] = True
            default_res["rating"] = p.get("rating")
            default_res["user_rating_count"] = p.get("userRatingCount")

            if "primaryTypeDisplayName" in p:
                default_res["primary_type"] = p["primaryTypeDisplayName"].get("text", "")

            price_map = {
                "PRICE_LEVEL_INEXPENSIVE": "1만원 이하",
                "PRICE_LEVEL_MODERATE": "1~2만원대",
                "PRICE_LEVEL_EXPENSIVE": "2~3만원대",
                "PRICE_LEVEL_VERY_EXPENSIVE": "3만원 이상"
            }
            default_res["price_level_text"] = price_map.get(p.get("priceLevel", ""), "")

            parking_opts = p.get("parkingOptions", {})
            if parking_opts.get("freeParkingLot") or parking_opts.get("freeGarageParking"):
                default_res["parking_info"] = "무료 주차 가능"
            elif parking_opts.get("paidParkingLot") or parking_opts.get("paidGarageParking"):
                default_res["parking_info"] = "유료 주차 가능"
            elif parking_opts.get("streetParking"):
                default_res["parking_info"] = "노상 주차 가능"

            hours_data = p.get("currentOpeningHours") or p.get("regularOpeningHours")
            if hours_data:
                default_res["open_now"] = hours_data.get("openNow")

                today_idx = datetime.now().weekday()
                today_google_day = (today_idx + 1) % 7

                weekday_texts = hours_data.get("weekdayDescriptions", [])
                if weekday_texts and today_idx < len(weekday_texts):
                    raw_text = weekday_texts[today_idx]
                    if ":" in raw_text:
                        default_res["today_hours_text"] = raw_text.split(":", 1)[-1].strip()

                periods = hours_data.get("periods", [])
                today_periods = [per for per in periods if per.get("open", {}).get("day") == today_google_day]

                if today_periods:
                    is_24h = any(per.get("open", {}).get("hour") == 0 and not per.get("close") for per in today_periods)
                    if is_24h:
                        default_res["is_lunch_open"] = True
                    else:
                        earliest_open_hour = min(per.get("open", {}).get("hour", 0) for per in today_periods)
                        latest_close_hour = max(per.get("close", {}).get("hour", 24) for per in today_periods if per.get("close"))

                        # 14시 이전에 문을 열고 12시 이후까지 영업하면 점심 영업 인정
                        if earliest_open_hour <= 13 and latest_close_hour >= 12:
                            default_res["is_lunch_open"] = True
                        else:
                            default_res["is_lunch_open"] = False
                else:
                    default_res["is_lunch_open"] = False

    except Exception:
        pass

    return default_res

def is_valid_lunch_restaurant_smart(menu_name: str, place_name: str, category_name: str, g_details: dict) -> bool:
    clean_name = place_name.replace(" ", "").upper()
    cat_full = category_name.replace(" ", "")

    # 1. 유흥/성인업소 차단
    if any(hard in cat_full for hard in HARD_EXCLUDED_CATEGORIES):
        return False
    if any(hard in clean_name for hard in ["룸살롱", "단란주점", "유흥주점", "나이트클럽"]):
        return False

    # 2. 비식사 카페/디저트 차단
    if any(cafe in cat_full for cafe in CAFE_EXCLUDED_CATEGORIES):
        return False

    # 3. [스테이크 전문점 엄격 필터링]
    if menu_name == "스테이크":
        # 도시락, 돈까스, 분식, 햄버거 등 부메뉴로 취급하는 업태 원천 배제
        if any(bad in clean_name for bad in STEAK_EXCLUDED_KEYWORDS):
            return False
        if any(bad_cat in cat_full for bad_cat in ["도시락", "분식", "돈가스", "돈까스", "패스트푸드"]):
            return False
        
        # 진짜 스테이크 전문 레스토랑인지 검증 (상호명 또는 카테고리에 스테이크/양식/레스토랑/이탈리안 명시 필수)
        is_real_steakhouse = (
            any(k in clean_name for k in ["스테이크", "STEAK", "립하우스", "그릴", "OUTBACK", "아웃백", "빕스", "VIPS"]) or
            any(k in cat_full for k in ["스테이크,립", "패밀리레스토랑", "이탈리안", "양식"])
        )
        if not is_real_steakhouse:
            return False

    # 4. Google Places 영업시간 데이터 기준 (점심 운영 여부 최우선)
    if g_details.get("found") and g_details.get("is_lunch_open") is not None:
        return g_details["is_lunch_open"]

    # 5. Google 영업시간이 없을 때 보수적 야간 키워드 필터링
    if any(bad in clean_name for bad in SUSPECT_NIGHT_KEYWORDS):
        return False
    if any(c in cat_full for c in ["유흥주점", "룸살롱", "단란주점"]):
        return False

    return True

def has_nearby_parking_kakao(lat: float, lng: float, place_name: str) -> bool:
    if any(k in place_name for k in ["주차", "타워", "빌딩", "스퀘어", "몰", "프라자", "센터"]):
        return True
    
    if not KAKAO_REST_KEY:
        return False

    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {
        "category_group_code": "PK6",
        "x": str(lng),
        "y": str(lat),
        "radius": 300,
        "size": 1
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=1.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            return len(docs) > 0
    except Exception:
        pass
    return False

def calculate_priority(place: dict, menu_name: str, has_parking: bool = False, need_parking: bool = False) -> float:
    score = place["dist"]
    p_name = place["name"]
    is_franchise = any(p_name.strip().endswith(sfx) for sfx in ["점", "호점", "직영점"])
    
    place["is_personal"] = not is_franchise
    score += (1.5 if is_franchise else -0.5)

    if menu_name in p_name:
        score -= 2.5

    if need_parking:
        score -= (3.5 if has_parking else 0.0)

    return score

@st.cache_data(ttl=86400, show_spinner=False)
def kakao_get_coordinates(query: str):
    if not KAKAO_REST_KEY or not query.strip():
        return None, None
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    clean_q = query.strip()

    addr_url = "https://dapi.kakao.com/v2/local/search/address.json"
    try:
        res = requests.get(addr_url, headers=headers, params={"query": clean_q, "size": 1}, timeout=3.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                return float(docs[0]["y"]), float(docs[0]["x"])
    except Exception:
        pass

    kw_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    try:
        res = requests.get(kw_url, headers=headers, params={"query": clean_q, "size": 1}, timeout=3.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                return float(docs[0]["y"]), float(docs[0]["x"])
    except Exception:
        pass

    return None, None

def kakao_search_places(lat: float, lng: float, menu_name: str, search_query: str, radius_km: float = 1.8, need_parking: bool = False):
    """카카오 검색 및 카테고리별 2단계 스마트 폴백 엔진"""
    if not KAKAO_REST_KEY:
        return []
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    radius_meters = int(radius_km * 1000)

    # 카테고리별 스마트 대체 검색어 사전
    CUISINE_FALLBACK_MAP = {
        # 양식 (스테이크는 패밀리레스토랑/스테이크하우스로 정교화)
        "스테이크": ["스테이크하우스", "스테이크 레스토랑", "패밀리레스토랑"],
        "리조또": ["이탈리안", "파스타", "양식당"],
        "브런치": ["브런치", "양식", "카페거리"],
        # 멕시코식
        "타코": ["타코", "멕시칸", "멕시코요리"],
        "부리또": ["부리또", "브리또", "멕시칸"],
        "퀘사디아": ["멕시칸", "멕시코", "타코"],
        "파히타": ["멕시코", "남미음식", "멕시칸"],
        # 인도식
        "인도커리": ["인도커리", "인도음식", "인도요리"],
        "인도난커리": ["인도요리", "인도음식", "커리"],
        "탄두리치킨": ["인도음식", "인도요리", "커리"],
        "카레라이스": ["커리", "카레", "인도음식"],
        # 동남아식
        "팟타이": ["태국음식", "아시아음식", "쌀국수"],
        "나시고랭": ["아시아음식", "동남아", "베트남"],
        "분짜": ["베트남음식", "쌀국수", "베트남"],
        "반미": ["베트남", "샌드위치", "쌀국수"],
        "똠얌꿍": ["태국음식", "아시아음식", "동남아"],
        # 일식
        "사케동": ["연어덮밥", "일식덮밥", "일식당"],
        "가츠동": ["돈부리", "일식덮밥", "일식"],
        "텐동": ["텐동", "일식덮밥", "일식당"],
        "일본라멘": ["라멘", "일본라멘", "일식당"],
        "오마카세": ["스시", "초밥", "일식당"]
    }

    params = {
        "query": search_query,
        "category_group_code": "FD6",
        "x": str(lng),
        "y": str(lat),
        "radius": max(200, min(radius_meters, 20000)),
        "sort": "distance",
        "size": 15
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=3.0)
        docs = res.json().get("documents", []) if res.status_code == 200 else []

        # 단품 검색 실패 시 스마트 폴백 검색 시도
        if not docs and menu_name in CUISINE_FALLBACK_MAP:
            for fallback_query in CUISINE_FALLBACK_MAP[menu_name]:
                params["query"] = fallback_query
                res = requests.get(url, headers=headers, params=params, timeout=2.5)
                docs = res.json().get("documents", []) if res.status_code == 200 else []
                if docs:
                    break

        if docs:
            candidates = []
            for d in docs:
                p_name = d.get("place_name", "")
                cat_name = d.get("category_name", "")
                p_lat = float(d.get("y"))
                p_lng = float(d.get("x"))

                g_details = fetch_google_place_details(p_name, p_lat, p_lng)

                # 스테이크 전문점 엄격 필터링 및 스마트 점심 판별 적용
                if not is_valid_lunch_restaurant_smart(menu_name, p_name, cat_name, g_details):
                    continue

                kakao_parking = has_nearby_parking_kakao(p_lat, p_lng, p_name) if need_parking else False
                google_parking = bool(g_details["parking_info"])
                parking_available = google_parking or kakao_parking

                clean_cat = cat_name.split(">")[-1].strip() if ">" in cat_name else cat_name
                if g_details["primary_type"] and g_details["primary_type"] not in clean_cat:
                    final_cat = f"{clean_cat} · {g_details['primary_type']}"
                else:
                    final_cat = clean_cat

                dist_m = float(d.get("distance", 0))
                p_dict = {
                    "id": d.get("id", ""),
                    "name": p_name,
                    "category": final_cat,
                    "lat": p_lat,
                    "lng": p_lng,
                    "dist": round(dist_m / 1000, 2) if dist_m > 0 else 0.1,
                    "address": d.get("road_address_name") or d.get("address_name", ""),
                    "place_url": d.get("place_url", ""),
                    "has_parking": parking_available,
                    "parking_desc": g_details["parking_info"] or ("인근 주차 가능" if kakao_parking else ""),
                    "price_level": g_details["price_level_text"],
                    "today_hours": g_details["today_hours_text"],
                    "open_now": g_details["open_now"],
                    "rating": g_details["rating"],
                    "user_rating_count": g_details["user_rating_count"]
                }
                p_dict["priority_score"] = calculate_priority(p_dict, menu_name, has_parking=parking_available, need_parking=need_parking)
                candidates.append(p_dict)
            
            if need_parking:
                candidates.sort(key=lambda x: (not x["has_parking"], x["priority_score"]))
            else:
                candidates.sort(key=lambda x: x["priority_score"])

            return candidates
    except Exception:
        pass
    return []

def reset_to_selection():
    st.session_state.saved_result = None
    st.rerun()

# --- 화면 상단 헤더 ---
st.markdown("<h1 style='color: #2E1C10; font-size: 28px; font-weight: 800; margin: 0 0 10px 0; letter-spacing: -0.6px;'>🍱 오늘 점심 뭐 먹지?</h1>", unsafe_allow_html=True)
st.markdown("<div style='color: #8C827A; font-size: 13.5px; margin-bottom: 22px; line-height: 1.5;'>고민되는 점심 메뉴와 검증된 주변 밥집을 랜덤으로 골라드립니다.</div>", unsafe_allow_html=True)

if not has_key:
    st.warning("⚠️ **카카오 API 키 설정 필요**: `.streamlit/secrets.toml`에 `KAKAO_REST_KEY`를 설정해주세요.")

# ============================================================
# [뷰 분기 1]: 룰렛 결과 화면
# ============================================================
res = st.session_state.saved_result

if res is not None and res.get("places"):
    card_html = (
        f'<div class="fade-in-content" style="text-align: center; margin: 14px 0 14px 0; padding: 24px 20px; '
        f'background: #FFFDF9; border-radius: 22px; border: 1.5px solid #F5D5B8; '
        f'box-shadow: 0 4px 18px rgba(245, 213, 184, 0.35);">'
        f'<div style="font-size: 68px; line-height: 1; margin-bottom: 8px;">{res["emoji"]}</div>'
        f'<div style="display: flex; justify-content: center; align-items: center; gap: 8px; width: 100%; margin: 4px 0;">'
        f'<span style="font-size: 22px;">🎉</span>'
        f'<span style="color: #2E1C10; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">{res["menu"]} 당첨!</span>'
        f'<span style="font-size: 22px;">🎉</span>'
        f'</div>'
        f'<div style="color: #7A6F66; font-size: 13px; font-weight: 500; margin-top: 4px;">'
        f'점심 메뉴 추천 결과 ({res["radius_text"]})'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    places = res["places"]
    top_pick = places[0]

    tag_text = "개인 전문점" if top_pick.get("is_personal", True) else "프랜차이즈"
    tag_bg = "#FCEFE6" if top_pick.get("is_personal", True) else "#F7E6D2"
    tag_color = "#C85A32" if top_pick.get("is_personal", True) else "#8A532B"

    badges = []
    if top_pick.get("open_now") is True:
        badges.append('<span style="font-size: 11px; background: #E8F4EA; color: #2E7D32; padding: 2px 7px; border-radius: 6px; font-weight: 700;">🟢 지금 영업중</span>')
    elif top_pick.get("open_now") is False:
        badges.append('<span style="font-size: 11px; background: #FDE8E8; color: #C5221F; padding: 2px 7px; border-radius: 6px; font-weight: 700;">🔴 영업 준비중</span>')

    if top_pick.get("has_parking", False):
        p_desc = top_pick.get("parking_desc") or "주차 편리"
        badges.append(f'<span style="font-size: 11px; background: #E8F0FE; color: #1A73E8; padding: 2px 7px; border-radius: 6px; font-weight: 700;">🅿️ {p_desc}</span>')

    if top_pick.get("price_level"):
        badges.append(f'<span style="font-size: 11px; background: #FEF7E0; color: #B06000; padding: 2px 7px; border-radius: 6px; font-weight: 600;">💵 {top_pick["price_level"]}</span>')

    if top_pick.get("rating"):
        badges.append(f'<span style="font-size: 11px; background: #FFF0EB; color: #E86A3E; padding: 2px 7px; border-radius: 6px; font-weight: 700;">⭐ {top_pick["rating"]} ({top_pick["user_rating_count"]})</span>')

    badges_html = " ".join(badges)

    hours_line = ""
    if top_pick.get("today_hours"):
        hours_line = f'<div style="font-size: 12.5px; color: #5D534A; margin-top: 5px;">🕒 오늘 운영: <b>{top_pick["today_hours"]}</b></div>'

    top_pick_html = (
        f'<div class="fade-in-content" style="margin-bottom: 20px; padding: 22px 18px; '
        f'background: #FFFDF9; border-radius: 22px; border: 1.5px solid #F5D5B8; '
        f'box-shadow: 0 4px 18px rgba(245, 213, 184, 0.35); text-align: center;">'
        f'<div style="display: flex; justify-content: center; align-items: center; gap: 6px; margin-bottom: 8px; flex-wrap: wrap;">'
        f'<span style="font-size: 12.5px; color: #E86A3E; font-weight: 700;">⭐ 오늘의 1픽 추천 밥집</span>'
        f'<span style="font-size: 11px; background: {tag_bg}; color: {tag_color}; padding: 2px 7px; border-radius: 6px; font-weight: 700;">{tag_text}</span>'
        f'<span style="font-size: 11px; background: #F3ECE4; color: #6E5F55; padding: 2px 7px; border-radius: 6px; font-weight: 600;">{top_pick.get("category", "식당")}</span>'
        f'{badges_html}'
        f'</div>'
        f'<div style="margin: 4px 0;">'
        f'<a href="{top_pick.get("place_url", "#")}" target="_blank" style="text-decoration: none; color: #2E1C10; font-size: 23px; font-weight: 900; display: inline-block;">'
        f'{top_pick["name"]}'
        f'</a>'
        f'</div>'
        f'{hours_line}'
        f'<div style="font-size: 13px; color: #7A6F66; margin-top: 5px;">'
        f'📍 {top_pick["address"]} (약 {top_pick["dist"]}km)'
        f'</div>'
        f'</div>'
    )
    st.markdown(top_pick_html, unsafe_allow_html=True)

    if len(places) > 1:
        st.markdown(f"<div class='fade-in-content' style='font-size: 14.5px; font-weight: 700; color: #2E1C10; margin-bottom: 8px;'>📋 근처 다른 후보 ({len(places)-1}곳)</div>", unsafe_allow_html=True)
        other_candidates = places[1:11]
        col_left, col_right = st.columns(2)

        for idx, p in enumerate(other_candidates, start=1):
            p_tag = "개인" if p.get("is_personal", True) else "체인"
            short_cat = p.get('category', '식당').split('/')[-1].split('·')[0].strip()
            target_col = col_left if idx % 2 != 0 else col_right

            with target_col:
                cand_html = (
                    f'<div class="fade-in-content" style="display: flex; justify-content: space-between; align-items: center; '
                    f'background: #FFFFFF; border: 1px solid #ECE7E1; border-radius: 12px; '
                    f'padding: 9px 12px; margin-bottom: 8px;">'
                    f'<div style="display: flex; align-items: center; gap: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">'
                    f'<span style="display: inline-flex; justify-content: center; align-items: center; width: 18px; height: 18px; background: #F3EFEA; color: #555; border-radius: 5px; font-size: 11px; font-weight: 700;">{idx}</span>'
                    f'<a href="{p.get("place_url", "#")}" target="_blank" style="text-decoration: none; color: #111; font-size: 13px; font-weight: 700; max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{p["name"]}</a>'
                    f'<span style="font-size: 10px; background: #F7F5F2; color: #777; padding: 2px 5px; border-radius: 4px;">{p_tag}·{short_cat}</span>'
                    f'</div>'
                    f'<div style="font-size: 11.5px; color: #666; font-weight: 500; margin-left: 6px; white-space: nowrap;">{p["dist"]}km</div>'
                    f'</div>'
                )
                st.markdown(cand_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🗺 식당 위치 지도</div>", unsafe_allow_html=True)
    st.caption("🔴 빨간 핀: 1픽 매장 / 🔵 파란 핀: 주변 후보")

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
            icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
        ).add_to(m)

    unique_map_key = f"map_{res['id']}_{int(top_pick['lat'] * 10000)}"
    st_folium(m, width="100%", height=380, key=unique_map_key, returned_objects=[])

    kakao_directions_url = f"https://map.kakao.com/link/to/{urllib.parse.quote(top_pick['name'])},{top_pick['lat']},{top_pick['lng']}"
    st.link_button(f"🧭 '{top_pick['name']}' 길찾기 바로가기", kakao_directions_url, use_container_width=True)

    if st.button("🔄 다시 뽑기", use_container_width=True, key="btn_reset_bottom"):
        reset_to_selection()

# ============================================================
# [뷰 분기 2]: 선택 옵션 박스 및 룰렛 실행 루프
# ============================================================
else:
    main_view = st.empty()

    with main_view.container():
        # --- 1. 위치 입력 ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>📍 위치</div>", unsafe_allow_html=True)
            col_input, col_gps = st.columns([3.5, 1.2], vertical_alignment="center")

            with col_input:
                region = st.text_input(
                    "위치입력",
                    value=st.session_state.region_input_val,
                    placeholder="예시) 테헤란로 152, 역삼동 737, 홍대입구역",
                    key="main_region_input",
                    label_visibility="collapsed"
                )
                if region != st.session_state.region_input_val:
                    st.session_state.region_input_val = region
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
                    " style="width:100%; height:42px; background-color:#E86A3E; color:white; border:none; border-radius:12px; font-size:13px; font-weight:700; cursor:pointer; box-shadow: 0 2px 8px rgba(232, 106, 62, 0.2);">
                        내 위치 찾기
                    </button>
                    """,
                    unsafe_allow_html=True
                )

        # --- 2. 탐색 반경 ---
        clean_region = region.strip()
        is_admin_region = False

        if clean_region:
            is_spot = bool(re.search(r"(역|출구|거리|센터|스퀘어|타워|빌딩|공원|마트|백화점)$", clean_region))
            is_pure_admin = bool(re.search(r"([시군구읍면동]|\b\w+[0-9]*가)$", clean_region))
            if is_pure_admin and not is_spot:
                is_admin_region = True

        should_show_radius = bool(clean_region and not is_admin_region)

        if should_show_radius:
            with st.container(border=True):
                st.markdown("<div class='section-title'>📏 탐색 반경</div>", unsafe_allow_html=True)
                
                c1, c2, c3, c4 = st.columns(4, vertical_alignment="center")
                current_preset = st.session_state.selected_radius_preset

                with c1:
                    if st.button("🚶 인근", key="rbtn_walk", type="primary" if current_preset == "인근" else "secondary", use_container_width=True):
                        if st.session_state.selected_radius_preset != "인근":
                            st.session_state.selected_radius_preset = "인근"
                            st.rerun()

                with c2:
                    if st.button("🚲 근거리", key="rbtn_bike", type="primary" if current_preset == "근거리" else "secondary", use_container_width=True):
                        if st.session_state.selected_radius_preset != "근거리":
                            st.session_state.selected_radius_preset = "근거리"
                            st.rerun()

                with c3:
                    if st.button("🚗 원거리", key="rbtn_car", type="primary" if current_preset == "원거리" else "secondary", use_container_width=True):
                        if st.session_state.selected_radius_preset != "원거리":
                            st.session_state.selected_radius_preset = "원거리"
                            st.rerun()

                with c4:
                    if st.button("직접 입력", key="rbtn_custom", type="primary" if current_preset == "직접 입력" else "secondary", use_container_width=True):
                        if st.session_state.selected_radius_preset != "직접 입력":
                            st.session_state.selected_radius_preset = "직접 입력"
                            st.rerun()

                if st.session_state.selected_radius_preset == "직접 입력":
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                    manual_radius = st.number_input(
                        "희망 반경 (단위: km)", 
                        min_value=0.2, 
                        max_value=10.0, 
                        value=st.session_state.custom_radius_val, 
                        step=0.2, 
                        key="custom_radius_num",
                        label_visibility="collapsed"
                    )
                    if manual_radius != st.session_state.custom_radius_val:
                        st.session_state.custom_radius_val = manual_radius
                    radius_km = float(manual_radius)
                    radius_display_text = f"직접 입력 {radius_km:.1f}km"
                else:
                    radius_km = PRESET_RADIUS.get(st.session_state.selected_radius_preset, 1.8)
                    radius_display_text = f"{st.session_state.selected_radius_preset} ({radius_km}km)"
        else:
            radius_km = 1.8
            radius_display_text = "지역 인근"

        # --- 3. 음식 종류 선택 ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>🍽 음식 종류</div>", unsafe_allow_html=True)

            cu1, cu2, cu3, cu4 = st.columns(4)
            current_cuisine = st.session_state.selected_cuisine

            with cu1:
                if st.button("한식", key="cbtn_korean", type="primary" if current_cuisine == "한식" else "secondary", use_container_width=True):
                    if st.session_state.selected_cuisine != "한식":
                        st.session_state.selected_cuisine = "한식"
                        st.rerun()
            with cu2:
                if st.button("중식", key="cbtn_chinese", type="primary" if current_cuisine == "중식" else "secondary", use_container_width=True):
                    if st.session_state.selected_cuisine != "중식":
                        st.session_state.selected_cuisine = "중식"
                        st.rerun()
            with cu3:
                if st.button("일식", key="cbtn_japanese", type="primary" if current_cuisine == "일식" else "secondary", use_container_width=True):
                    if st.session_state.selected_cuisine != "일식":
                        st.session_state.selected_cuisine = "일식"
                        st.rerun()
            with cu4:
                if st.button("양식", key="cbtn_western", type="primary" if current_cuisine == "양식" else "secondary", use_container_width=True):
                    if st.session_state.selected_cuisine != "양식":
                        st.session_state.selected_cuisine = "양식"
                        st.rerun()

            cu5, cu6, cu7, cu8 = st.columns(4)
            with cu5:
                if st.button("동남아식", key="cbtn_asian", type="primary" if current_cuisine == "동남아식" else "secondary", use_container_width=True):
                    if st.session_state.selected_cuisine != "동남아식":
                        st.session_state.selected_cuisine = "동남아식"
                        st.rerun()
            with cu6:
                if st.button("인도식", key="cbtn_indian", type="primary" if current_cuisine == "인도식" else "secondary", use_container_width=True):
                    if st.session_state.selected_cuisine != "인도식":
                        st.session_state.selected_cuisine = "인도식"
                        st.rerun()
            with cu7:
                if st.button("멕시코식", key="cbtn_mexican", type="primary" if current_cuisine == "멕시코식" else "secondary", use_container_width=True):
                    if st.session_state.selected_cuisine != "멕시코식":
                        st.session_state.selected_cuisine = "멕시코식"
                        st.rerun()
            with cu8:
                if st.button("상관없음", key="cbtn_any", type="primary" if current_cuisine == "상관없음" else "secondary", use_container_width=True):
                    if st.session_state.selected_cuisine != "상관없음":
                        st.session_state.selected_cuisine = "상관없음"
                        st.rerun()

        # --- 4. 음식 가격 선택 ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>💵 음식 가격(식사 기준)</div>", unsafe_allow_html=True)

            p1, p2, p3, p4 = st.columns(4)
            current_price = st.session_state.selected_price

            with p1:
                if st.button("1만원 이하", key="pbtn_low", type="primary" if current_price == "1만원 이하" else "secondary", use_container_width=True):
                    if st.session_state.selected_price != "1만원 이하":
                        st.session_state.selected_price = "1만원 이하"
                        st.rerun()
            with p2:
                if st.button("1~2만원", key="pbtn_mid", type="primary" if current_price == "1~2만원" else "secondary", use_container_width=True):
                    if st.session_state.selected_price != "1~2만원":
                        st.session_state.selected_price = "1~2만원"
                        st.rerun()
            with p3:
                if st.button("2만원 이상", key="pbtn_high", type="primary" if current_price == "2만원 이상" else "secondary", use_container_width=True):
                    if st.session_state.selected_price != "2만원 이상":
                        st.session_state.selected_price = "2만원 이상"
                        st.rerun()
            with p4:
                if st.button("상관없음", key="pbtn_any", type="primary" if current_price == "상관없음" else "secondary", use_container_width=True):
                    if st.session_state.selected_price != "상관없음":
                        st.session_state.selected_price = "상관없음"
                        st.rerun()

        # --- 5. 주차 가능 여부 선택 ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>🅿️ 주차 가능 여부</div>", unsafe_allow_html=True)
            pk1, pk2 = st.columns(2)
            current_parking = st.session_state.selected_parking

            with pk1:
                if st.button("식당 주차장 혹은 인근 주차장 있음", key="pkbtn_yes", type="primary" if current_parking == "식당 주차장 혹은 인근 주차장 있음" else "secondary", use_container_width=True):
                    if st.session_state.selected_parking != "식당 주차장 혹은 인근 주차장 있음":
                        st.session_state.selected_parking = "식당 주차장 혹은 인근 주차장 있음"
                        st.rerun()
            with pk2:
                if st.button("주차 불필요", key="pkbtn_any", type="primary" if current_parking == "주차 불필요" else "secondary", use_container_width=True):
                    if st.session_state.selected_parking != "주차 불필요":
                        st.session_state.selected_parking = "주차 불필요"
                        st.rerun()

        region_warning_spot = st.empty()

        def show_location_warning():
            region_warning_spot.markdown(
                """
                <div class="warning-box">
                    <span style="font-size: 16px;">⚠️</span>
                    <span style="color: #6C4D0A; font-size: 13.5px; font-weight: 700;">
                        위치를 입력하거나 '내 위치 찾기'를 눌러주세요!
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

        def show_cuisine_warning():
            region_warning_spot.markdown(
                """
                <div class="warning-box">
                    <span style="font-size: 16px;">⚠️</span>
                    <span style="color: #6C4D0A; font-size: 13.5px; font-weight: 700;">
                        음식 종류를 선택해 주세요!
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

        def show_location_not_found_warning(target_region: str):
            region_warning_spot.markdown(
                f"""
                <div class="warning-box">
                    <span style="font-size: 16px;">⚠️</span>
                    <span style="color: #6C4D0A; font-size: 13.5px; font-weight: 700;">
                        '{target_region}' 위치를 찾지 못했습니다. 도로명/지번 주소 또는 주요 건물·역 이름을 확인해 주세요!
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

        # --- 6. 메인 룰렛 버튼 ---
        spin_clicked = st.button("🎲 오늘 점심 랜덤 룰렛 돌리기!", use_container_width=True, type="primary", key="btn_trigger_random")

    # 버튼 클릭 시 즉시 롤링 및 결과 표출 파이프라인
    if spin_clicked:
        if not region.strip() and not st.session_state.gps_coords:
            show_location_warning()
        elif not st.session_state.selected_cuisine:
            show_cuisine_warning()
        else:
            if st.session_state.gps_coords:
                c_lat, c_lng = st.session_state.gps_coords
            else:
                c_lat, c_lng = kakao_get_coordinates(region)

            if not c_lat:
                show_location_not_found_warning(region)
            else:
                region_warning_spot.empty()

                cu = st.session_state.selected_cuisine
                pr = st.session_state.selected_price
                price_map = {"1만원 이하": "low", "1~2만원": "mid", "2만원 이상": "high"}
                target_pr = price_map.get(pr, None)

                if cu == "상관없음":
                    candidates_pool = [f for f in DEFAULT_FOODS if f[0] != "죽"]
                else:
                    candidates_pool = [f for f in DEFAULT_FOODS if f[3] == cu and f[0] != "죽"]

                if not candidates_pool:
                    candidates_pool = [f for f in DEFAULT_FOODS if f[0] != "죽"]

                if target_pr:
                    selected_candidates = [f for f in candidates_pool if f[4] == target_pr]
                    if not selected_candidates:
                        selected_candidates = candidates_pool
                else:
                    selected_candidates = candidates_pool

                if not selected_candidates:
                    selected_candidates = [f for f in DEFAULT_FOODS if f[0] != "죽"]

                main_view.empty()
                rolling_spot = main_view.empty()

                shuffled = selected_candidates.copy()
                random.shuffle(shuffled)
                need_parking_flag = (st.session_state.selected_parking == "식당 주차장 혹은 인근 주차장 있음")

                # 롤링 애니메이션 전반부
                for i in range(5):
                    temp = random.choice(selected_candidates)
                    rolling_spot.markdown(
                        f"""
                        <div class="fade-in-content" style="text-align: center; margin: 14px 0 14px 0; padding: 22px 18px; 
                                    background: #FFFDF9; border-radius: 20px; border: 1.5px solid #F5D5B8; 
                                    box-shadow: 0 4px 16px rgba(245, 213, 184, 0.35);">
                            <div style="font-size: 58px; line-height: 1; margin-bottom: 6px;">{temp[1]}</div>
                            <div style="color: #2E1C10; font-size: 23px; font-weight: 800; margin: 4px 0;">{temp[0]}</div>
                            <p style="color: #8C827A; font-size: 13px; margin: 0;">{radius_display_text} 기준 맛집 추첨 중... 🎲</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    time.sleep(0.06)

                # 스마트 폴백 적용 하이브리드 탐색
                final_menu = None
                places = []
                for m_name, m_emoji, m_kw, _, _ in shuffled[:6]:
                    found = kakao_search_places(c_lat, c_lng, m_name, m_kw, radius_km=radius_km, need_parking=need_parking_flag)
                    if found:
                        final_menu = (m_name, m_emoji)
                        places = found
                        break

                if not places:
                    fallback_kw = "백반" if cu in ["한식", "상관없음"] else f"{cu} 전문점"
                    fallback_menu = "백반·가정식" if cu in ["한식", "상관없음"] else f"{cu} 밥집"
                    fallback_found = kakao_search_places(c_lat, c_lng, fallback_menu, fallback_kw, radius_km=radius_km, need_parking=need_parking_flag)
                    if fallback_found:
                        final_menu = (fallback_menu, "🍱")
                        places = fallback_found

                # 롤링 애니메이션 후반부
                for i in range(4):
                    temp = random.choice(selected_candidates)
                    rolling_spot.markdown(
                        f"""
                        <div style="text-align: center; margin: 14px 0 14px 0; padding: 22px 18px; 
                                    background: #FFFDF9; border-radius: 20px; border: 1.5px solid #F5D5B8; 
                                    box-shadow: 0 4px 16px rgba(245, 213, 184, 0.35);">
                            <div style="font-size: 58px; line-height: 1; margin-bottom: 6px;">{temp[1]}</div>
                            <div style="color: #2E1C10; font-size: 23px; font-weight: 800; margin: 4px 0;">{temp[0]}</div>
                            <p style="color: #8C827A; font-size: 13px; margin: 0;">{radius_display_text} 기준 맛집 추첨 중... 🎲</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    time.sleep(0.09 + (i * 0.05))

                if final_menu:
                    rolling_spot.markdown(
                        f"""
                        <div style="text-align: center; margin: 14px 0 14px 0; padding: 22px 18px; 
                                    background: #FFFDF9; border-radius: 20px; border: 2px solid #E86A3E; 
                                    box-shadow: 0 4px 20px rgba(232, 106, 62, 0.35);">
                            <div style="font-size: 62px; line-height: 1; margin-bottom: 6px;">{final_menu[1]}</div>
                            <div style="color: #2E1C10; font-size: 25px; font-weight: 900; margin: 4px 0;">{final_menu[0]}</div>
                            <p style="color: #E86A3E; font-size: 13px; font-weight: 700; margin: 0;">당첨! 식당 정보를 불러옵니다... ✨</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    time.sleep(0.25)

                rolling_spot.empty()

                if final_menu and places:
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
                    st.rerun()
                else:
                    st.warning("⚠️ 설정하신 조건 내에 만족하는 식당을 찾지 못했습니다. 반경을 넓히거나 가격/주차 옵션을 조정해 보세요!")
                    time.sleep(1.8)
                    st.rerun()
