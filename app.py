import streamlit as st
import random
import time
import requests
import urllib.parse
import re
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="점메추", page_icon="🍱", layout="centered")

# --- UI/UX 전체 톤앤매너 및 네이티브 앱 전용 스타일 CSS ---
st.markdown(
    """
    <style>
    :root, .stApp, [data-testid="stAppViewContainer"] {
        --primary-color: #E86A3E !important;
        --primary: #E86A3E !important;
    }

    /* --- 네이티브 앱처럼 보이도록 Streamlit 웹 UI 요소 숨김 처리 --- */
    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    #MainMenu,
    footer,
    .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_ {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    .stApp {
        background-color: #FAF8F5;
        font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Apple SD Gothic Neo", sans-serif;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3.6rem !important;
        max-width: 620px !important;
    }

    /* 터치 시 글자나 버튼이 파랗게 드래그되는 현상 방지 */
    * {
        -webkit-tap-highlight-color: transparent !important;
        -webkit-touch-callout: none !important;
        -webkit-user-select: none !important;
        user-select: none !important;
    }
    input, textarea {
        -webkit-user-select: text !important;
        user-select: text !important;
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

# ==============================================================================
# 필터링 키워드 (주점, 술집, 야식, 던킨·디저트 원천 차단)
# ==============================================================================
EXCLUDED_CATEGORIES = [
    "술집", "주점", "호프", "포차", "이자카야", "바(BAR)", "요리주점", "와인바",
    "칵테일바", "민속주점", "맥주", "룸살롱", "단란주점", "유흥주점", "라이브카페", 
    "나이트클럽", "오뎅바", "꼬치구이전문점", "선술집", "해물주점", "실내포차",
    "포장마차", "와인", "위스키", "선술", "감성주점", "카페", "디저트", "제과,베이커리",
    "도넛", "실비집", "대포집", "맥줏집"
]

EXCLUDED_NAME_KEYWORDS = [
    "포차", "주점", "호프", "이자카야", "술집", "맥주", "와인", "비어",
    "BEER", "노래방", "포장마차", "야시장", "소주", "오뎅바", "소주방",
    "막걸리", "동동주", "생맥주", "달빛", "심야", "야식", "올나잇", "주막", "동동",
    "탁주", "양조장", "브루어리", "BREW", "탭룸", "살롱", "가라오케", "선술집",
    "대포", "대포집", "통닭발", "껍데기", "연탄구이", "원조골뱅이", "실비집", "실비",
    "던킨", "DUNKIN", "크리스피크림", "랜디스", "노티드", "배스킨라빈스", "베스킨"
]

JEON_KEYWORDS = [
    "파전", "빈대떡", "부침개", "지짐이", "전이야기", "전나라", "전마을", 
    "전선생", "종로전", "원조전", "전골목", "주막", "전사랑", "전세상"
]

NON_LUNCH_CATEGORIES = [
    "육류,고기구이", "삼겹살", "곱창,막창", "양꼬치", "조개구이",
    "치킨", "닭요리 > 치킨", "닭꼬치", "꼬치구이", "전,빈대떡", "닭발"
]

MEAT_SHOP_KEYWORDS = [
    "축산", "정육", "식육", "마장", "화로", "연탄", "솥뚜껑",
    "뒷고기", "주먹고기", "생고기", "생삼겹", "대패", "삼겹", "오겹",
    "곱창", "막창", "대창", "특양", "양꼬치", "양갈비", "갈매기", "뽈살",
    "야키니쿠", "우삼겹", "냉삼", "생갈비", "통닭발", "불닭발", "조개구이",
    "장어구이", "야키토리", "쿠시카츠", "닭강정"
]

EVENING_RAW_FISH_KEYWORDS = [
    "횟집", "회센타", "회센터", "수산", "회타운", "활어", "선어", "막회", "숙성회",
    "물회마차", "포차회", "바다마차", "해물포차", "해산물포차", "참치정육점"
]

STEAK_EXCLUDED_KEYWORDS = [
    "한솥", "도시락", "김밥", "천국", "돈까스", "돈가스", "카츠", "가츠", "카쯔",
    "함박", "함바그", "버거", "맥도날드", "롯데리아", "맘스터치", "버거킹", "토마토김밥",
    "얌샘", "고봉민", "싸다김밥", "분식", "포장마차", "국수나무", "역전우동"
]

STRICT_SPECIALTY_KEYWORDS = {
    "막국수": {
        "required": ["막국수"],
        "forbidden": ["돼지국밥", "순대", "순댓국", "감자탕", "뼈해장국", "보쌈", "족발"]
    },
    "돈까스": {
        "required": ["돈까스", "돈가스", "카츠", "가츠", "카쯔", "돈카츠", "포크커틀릿"],
        "forbidden": ["김밥", "천국", "한솥", "도시락", "떡볶이", "순대"]
    },
    "국밥": {
        "required": ["국밥", "순대", "순댓국", "돼지국밥", "따로국밥", "소머리국밥", "해장국"],
        "forbidden": ["막국수", "돈까스", "피자", "파스타"]
    },
    "닭갈비": {
        "required": ["닭갈비"],
        "forbidden": ["치킨", "통닭", "삼계탕", "백숙", "닭발"]
    },
    "수제비": {
        "required": ["수제비"],
        "forbidden": ["매운탕", "감자탕", "부대찌개", "동태탕", "포차"]
    },
    "칼국수": {
        "required": ["칼국수"],
        "forbidden": ["중국집", "짜장", "짬뽕"]
    },
    "초밥": {
        "required": ["스시", "초밥"],
        "forbidden": ["횟집", "회센터", "수산", "활어", "물회마차", "포차"]
    },
    "스테이크": {
        "required": ["스테이크", "STEAK", "립하우스", "그릴", "아웃백", "빕ส"],
        "forbidden": ["한솥", "도시락", "김밥", "돈까스", "돈가스", "함박", "분식", "햄버거"]
    },
    "짜장면": {
        "required": ["중화", "중국", "반점", "루", "원", "각", "짜장", "짬뽕", "차이"],
        "forbidden": ["분식", "김밥"]
    },
    "짬뽕": {
        "required": ["짬뽕", "중화", "중국", "반점", "교동"],
        "forbidden": ["분식", "김밥"]
    },
    "타코": {
        "required": ["타코", "TACO", "멕시칸", "멕시코"],
        "forbidden": ["치킨"]
    },
    "인도커리": {
        "required": ["인도", "커리", "인디아", "난", "CURRY"],
        "forbidden": ["분식"]
    }
}

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

    # 양식
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

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_google_place_details(place_name: str, lat: float, lng: float) -> dict:
    default_res = {
        "found": False,
        "is_lunch_open": None,
        "open_now": None,
        "today_hours_text": "",
        "price_level": None,
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

            raw_price = p.get("priceLevel", "")
            default_res["price_level"] = raw_price
            price_map = {
                "PRICE_LEVEL_INEXPENSIVE": "1만원 이하",
                "PRICE_LEVEL_MODERATE": "1~2만원대",
                "PRICE_LEVEL_EXPENSIVE": "2~3만원대",
                "PRICE_LEVEL_VERY_EXPENSIVE": "3만원 이상"
            }
            default_res["price_level_text"] = price_map.get(raw_price, "")

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

                        if earliest_open_hour <= 13 and latest_close_hour >= 12:
                            default_res["is_lunch_open"] = True
                        else:
                            default_res["is_lunch_open"] = False
                else:
                    default_res["is_lunch_open"] = False

    except Exception:
        pass

    return default_res

def is_valid_specialized_restaurant(menu_name: str, place_name: str, category_name: str, g_details: dict, selected_price_code: str) -> bool:
    clean_name = place_name.replace(" ", "").upper()
    cat_full = category_name.replace(" ", "")

    if any(ex in cat_full for ex in EXCLUDED_CATEGORIES):
        return False

    if menu_name == "타코" and any(k in clean_name for k in ["타코", "TACO", "멕시칸"]):
        if any(bad in clean_name for bad in ["노래방", "나이트클럽", "룸살롱", "단란주점", "유흥주점", "소주방", "호프"]):
            return False
    else:
        if any(bad in clean_name for bad in [k.upper() for k in EXCLUDED_NAME_KEYWORDS]):
            return False

    if any(jeon in clean_name for jeon in JEON_KEYWORDS):
        return False
    if any(c in cat_full for c in ["전,빈대떡", "빈대떡"]):
        return False

    if any(non in cat_full for non in NON_LUNCH_CATEGORIES):
        if not (menu_name == "닭갈비" and "닭요리" in cat_full):
            return False

    if "굽자" not in place_name:
        if "구이" in clean_name and menu_name != "생선구이":
            return False
        if any(bad in clean_name for bad in [k.upper() for k in MEAT_SHOP_KEYWORDS]):
            return False

    if menu_name not in ["초밥", "회덮밥", "생선구이"]:
        if any(fish in clean_name for fish in EVENING_RAW_FISH_KEYWORDS):
            return False

    if menu_name in STRICT_SPECIALTY_KEYWORDS:
        rule = STRICT_SPECIALTY_KEYWORDS[menu_name]
        has_required = any(req.upper() in clean_name or req.upper() in cat_full for req in rule["required"])
        if not has_required:
            return False
        
        has_forbidden = any(forbid.upper() in clean_name for forbid in rule["forbidden"])
        if has_forbidden:
            return False

    if menu_name == "스테이크":
        if any(bad in clean_name for bad in STEAK_EXCLUDED_KEYWORDS):
            return False
        if any(bad_cat in cat_full for bad_cat in ["도시락", "분식", "돈가스", "돈까스", "패스트푸드"]):
            return False

    if g_details.get("found") and g_details.get("is_lunch_open") is not None:
        if not g_details["is_lunch_open"]:
            return False

    if selected_price_code and g_details.get("price_level"):
        pl = g_details["price_level"]
        if selected_price_code == "low":
            if pl in ["PRICE_LEVEL_MODERATE", "PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE"]:
                return False
        elif selected_price_code == "high":
            if pl == "PRICE_LEVEL_INEXPENSIVE":
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

def kakao_search_places(lat: float, lng: float, menu_name: str, search_query: str, radius_km: float = 1.8, need_parking: bool = False, selected_price_code: str = None):
    if not KAKAO_REST_KEY:
        return []
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    radius_meters = int(radius_km * 1000)

    CUISINE_FALLBACK_MAP = {
        "스테이크": ["스테이크하우스", "스테이크 레스토랑", "패밀리레스토랑"],
        "리조또": ["이탈리안", "파스타", "양식당"],
        "브런치": ["브런치", "양식"],
        "타코": ["타코", "멕시칸", "멕시코요리"],
        "부리또": ["부리또", "브리또", "멕시칸"],
        "퀘사디아": ["멕시칸", "멕시코", "타코"],
        "파히타": ["멕시코", "남미음식", "멕시칸"],
        "인도커리": ["인도커리", "인도음식", "인도요리"],
        "인도난커리": ["인도요리", "인도음식", "커리"],
        "탄두리치킨": ["인도음식", "인도요리", "커리"],
        "카레라이스": ["커리", "카레", "인도음식"],
