import streamlit as st
import random
import time
import requests
import urllib.parse
import re
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="오늘 점심 뭐 먹지?", page_icon="🍱", layout="centered")

# --- UI/UX 전체 톤앤매너 및 간격 정돈 커스텀 CSS ---
st.markdown(
    """
    <style>
    /* 전체 배경 및 폰트 렌더링 */
    .stApp {
        background-color: #FAF8F5;
        font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Apple SD Gothic Neo", sans-serif;
    }
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 3.0rem !important;
        max-width: 640px !important;
    }

    /* 통일된 섹션 헤더 스타일 */
    .section-title {
        font-size: 14px;
        font-weight: 700;
        color: #3E3228;
        margin-top: 22px;
        margin-bottom: 6px;
        letter-spacing: -0.3px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .section-title:first-of-type {
        margin-top: 0px;
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

    /* 슬라이드 모션 */
    @keyframes smoothSlideDown {
        0% { opacity: 0; transform: translateY(-6px) scale(0.99); }
        100% { opacity: 1; transform: translateY(0) scale(1); }
    }
    .radius-wrapper, .cuisine-wrapper, .filter-wrapper {
        animation: smoothSlideDown 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        transform-origin: top center;
    }

    /* 룰렛 묶음 박스 간격 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px !important;
        border: 1.8px solid #EAE3DB !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02) !important;
        margin-bottom: 10px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #F0A284 !important;
    }

    /* 버튼 높이 및 폰트 통일 */
    div.stButton > button {
        height: 42px !important;
        border-radius: 12px !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #E86A3E !important;
        color: white !important;
        border: none !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        box-shadow: 0 3px 10px rgba(232, 106, 62, 0.22) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #D65A2F !important;
        transform: translateY(-1px);
    }
    div.stButton > button[kind="secondary"] {
        border: 1.2px solid #EDE4DC !important;
        background-color: #FFFFFF !important;
        color: #3E3228 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        padding: 8px 10px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #E86A3E !important;
        color: #E86A3E !important;
        background-color: #FFFDF9 !important;
        transform: translateY(-1px);
    }

    /* 컬럼 패딩을 좁혀 버튼 간격 통일 */
    div[data-testid="stColumn"] {
        padding: 0 2.5px !important;
    }

    /* 경고창 여백 정돈 */
    .warning-box {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        width: 100%;
        height: 42px;
        margin: 14px 0 6px 0;
        background-color: #FFFDF7;
        border: 1.5px solid #F7D488;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 1. API Key 보안 처리
has_key = "KAKAO_REST_KEY" in st.secrets and bool(st.secrets["KAKAO_REST_KEY"].strip())
KAKAO_REST_KEY = st.secrets["KAKAO_REST_KEY"].strip() if has_key else ""

PRESET_RADIUS = {
    "인근": 0.7,
    "근거리": 1.8,
    "원거리": 3.5,
    "직접 입력": None
}

# 세션 상태 초기화 및 보정
if "selected_radius_preset" not in st.session_state or st.session_state.selected_radius_preset not in PRESET_RADIUS:
    st.session_state.selected_radius_preset = "근거리"
if "custom_radius_val" not in st.session_state:
    st.session_state.custom_radius_val = 2.0
if "selected_cuisine" not in st.session_state:
    st.session_state.selected_cuisine = None
if "selected_price" not in st.session_state:
    st.session_state.selected_price = "금액 상관 없음"
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

# --- 정밀 필터링 키워드 정의 ---
EXCLUDED_CATEGORIES = [
    "술집", "주점", "호프", "포차", "이자카야", "바(BAR)", "요리주점", "와인바",
    "칵테일바", "민속주점", "맥주", "룸살롱", "단란주점", "유흥주점", "라이브카페", 
    "나이트클럽", "오뎅바", "꼬치구이전문점", "선술집", "해물주점", "실내포차",
    "포장마차", "와인", "위스키", "펍", "선술", "선술집", "감성주점", "카페", "디저트", "제과,베이커리"
]

EXCLUDED_NAME_KEYWORDS = [
    "포차", "주점", "호프", "이자카야", "술집", "맥주", "와인", "펍", "PUB", "비어",
    "BEER", "라운지", "BAR", "노래방", "포장마차", "야시장", "소주", "오뎅바",
    "막걸리", "동동주", "생맥주", "달빛", "심야", "야식", "올나잇", "주막", "동동",
    "탁주", "양조장", "브루어리", "BREW", "탭룸", "살롱", "가라오케", "선술집",
    "대포", "대포집", "통닭발", "껍데기", "연탄구이", "원조골뱅이"
]

JEON_KEYWORDS = [
    "파전", "빈대떡", "부침개", "지짐이", "전이야기", "전나라", "전마을", 
    "전선생", "종로전", "원조전", "전골목", "주막", "전사랑", "전세상"
]

NON_LUNCH_CATEGORIES = [
    "육류,고기", "육류,고기구이", "삼겹살", "곱창,막창", "양꼬치", "조개구이",
    "치킨", "닭요리 > 치킨", "닭꼬치", "꼬치구이", "전,빈대떡", "닭발"
]

MEAT_SHOP_KEYWORDS = [
    "축산", "정육", "식육", "마장", "가든", "화로", "연탄", "숯불", "솥뚜껑",
    "뒷고기", "주먹고기", "생고기", "생삼겹", "대패", "삼겹", "오겹",
    "곱창", "막창", "대창", "특양", "양꼬치", "양갈비", "갈매기", "뽈살",
    "야키니쿠", "우삼겹", "냉삼", "생갈비", "소갈비", "돼지갈비", "통닭발",
    "불닭발", "조개구이", "장어구이", "야키토리", "쿠시카츠", "닭강정"
]

EVENING_RAW_FISH_KEYWORDS = [
    "횟집", "회센타", "회센터", "수산", "회타운", "활어", "선어", "막회", "숙성회",
    "물회마차", "포차회", "바다마차", "해물포차", "해산물포차", "참치정육점"
]

VIETNAMESE_NOODLE_KEYWORDS = [
    "쌀국수", "포(PHO)", "PHO", "분짜", "반미", "포보", "미분당", "에머이",
    "사이공", "반포식스", "포메인", "포베이", "까몬", "더포", "낭만쌀국수",
    "아시아문", "팟타이", "포앤", "반쎄오", "월남쌈"
]

MULTI_MENU_FRANCHISES = [
    "국수나무", "미소야", "역전우동", "한솥", "도시락",
    "김밥천국", "고봉민", "김가네", "얌샘", "싸다김밥", "종로김밥", 
    "선비꼬마김밥", "마녀김밥", "바르다김선생", "밥버거", "토마토김밥",
    "분식천국", "나드리김밥", "소풍김밥"
]

KNOWN_FRANCHISE_BRANDS = [
    "김밥천국", "고봉민", "김가네", "얌샘", "싸다김밥", "종로김밥", "선비꼬마김밥",
    "마녀김밥", "바르다김선생", "밥버거", "토마토김밥", "국수나무", "미소야", "역전우동",
    "한솥", "본죽", "신전떡볶이", "동대문엽기", "죠스떡볶이", "청년다방", "두끼",
    "홍콩반점", "교동짬뽕", "백소정", "카츠젠", "롤링파스타", "서브웨이",
    "맥도날드", "롯데리아", "버거킹", "노브랜드버거", "맘스터치", "KFC",
    "상무초밥", "쿠우쿠우", "스시로", "갓덴스시", "미카도스시"
]

TONKATSU_NAME_INDICATORS = ["돈까스", "돈가스", "카츠", "카쯔", "가츠", "돈카츠", "포크커틀릿"]

STRICT_SPECIALTY_NAME_RULES = {
    "칼국수": ["칼국수"],
    "막국수": ["막국수"],
    "국밥": ["국밥", "순대", "순댓국", "돼지국밥", "따로국밥", "소머리국밥"],
    "뼈해장국": ["해장국", "감자탕", "뼈"],
    "초밥": ["스시", "초밥"],
    "김밥": ["김밥"],
    "죽": ["죽"],
    "잔치국수": ["잔치국수", "국수집", "할매국수", "멸치국수", "국수마을", "국수나라", "국수전문", "국수"],
    "육개장": ["육개장", "육대장", "혜장국"]
}

DEFAULT_FOODS = [
    ("김치찌개", "🥘", "김치찌개 전문점", "한식", "low"),
    ("된장찌개", "🍲", "된장찌개 백반", "한식", "low"),
    ("순두부찌개", "🥚", "순두부찌개 전문점", "한식", "low"),
    ("부대찌개", "🥓", "부대찌개 전문점", "한식", "mid"),
    ("청국장", "🍲", "청국장 전문점", "한식", "low"),
    ("동태탕", "🐟", "동태탕 전문점", "한식", "mid"),
    ("국밥", "🥣", "국밥 전문점", "한식", "low"),
    ("뼈해장국", "🍖", "뼈해장국", "한식", "low"),
    ("설렁탕", "🥣", "설렁탕 전문점", "한식", "mid"),
    ("곰탕", "🥩", "곰탕 전문점", "한식", "mid"),
    ("갈비탕", "🍖", "갈비탕 전문점", "한식", "mid"),
    ("삼계탕", "🍗", "삼계탕 전문점", "한식", "mid"),
    ("추어탕", "🍲", "추어탕 전문점", "한식", "mid"),
    ("육개장", "🌶️", "전통 육개장 전문점", "한식", "low"),
    ("콩나물국밥", "🌱", "콩나물국밥 전문점", "한식", "low"),
    ("황태해장국", "🐟", "황태해장국 전문점", "한식", "low"),
    ("선지해장국", "🥘", "선지해장국 전문점", "한식", "low"),
    ("도가니탕", "🥣", "도가니탕 전문점", "한식", "high"),
    ("백반", "🍱", "백반 가정식", "한식", "low"),
    ("제육볶음", "🔥", "제육볶음 정식", "한식", "low"),
    ("오징어볶음", "🦑", "오징어볶음 백반", "한식", "mid"),
    ("낙지볶음", "🐙", "낙지볶음 전문점", "한식", "mid"),
    ("쭈꾸미볶음", "🐙", "쭈꾸미 전문점", "한식", "mid"),
    ("돌솥비빔밥", "🍳", "비빔밥 전문점", "한식", "low"),
    ("보리밥정식", "🌾", "보리밥 정식", "한식", "low"),
    ("쌈밥정식", "🥬", "쌈밥 정식", "한식", "mid"),
    ("생선구이백반", "🐟", "생선구이 백반", "한식", "mid"),
    ("닭갈비", "🍗", "닭갈비 전문점", "한식", "mid"),
    ("찜닭", "🥔", "찜닭 전문점", "한식", "mid"),
    ("코다리조림", "🐟", "코다리조림 전문점", "한식", "mid"),
    ("간장게장백반", "🦀", "게장 정식", "한식", "high"),
    ("칼국수", "🍜", "칼국수 전문점", "한식", "low"),
    ("수제비", "🥣", "수제비 전문점", "한식", "low"),
    ("막국수", "🥢", "막국수 전문점", "한식", "low"),
    ("냉면", "🧊", "함흥 평양 냉면 전문점", "한식", "mid"),
    ("잔치국수", "🍜", "잔치국수 멸치국수 전문점", "한식", "low"),
    ("비빔국수", "🌶️", "비빔국수 전문점", "한식", "low"),
    ("죽", "🥣", "죽 전문점", "한식", "low"),
    ("떡볶이", "🍢", "떡볶이 전문점", "한식", "low"),
    ("김밥", "🍙", "김밥 전문점", "한식", "low"),
    ("짜장면", "🥢", "짜장면", "중식", "low"),
    ("짬뽕", "🔥", "짬뽕", "중식", "low"),
    ("볶음밥", "🍚", "중화 볶음밥", "중식", "low"),
    ("마파두부밥", "🍛", "마파두부", "중식", "low"),
    ("마라탕", "🌶️", "마라탕 전문점", "중식", "mid"),
    ("소바", "🥢", "메밀소바 모밀 전문점", "일식", "low"),
    ("돈까스", "🍱", "돈까스 카츠 전문점", "일식", "mid"),
    ("초밥", "🍣", "스시 초밥 전문점", "일식", "mid"),
    ("일본라멘", "🍜", "일본라멘 전문점", "일식", "mid"),
    ("우동", "🍢", "사누키 우동 전문점", "일식", "low"),
    ("사케동", "🍣", "연어덮밥 사케동", "일식", "mid"),
    ("가츠동", "🍛", "돈부리 덮밥 전문점", "일식", "low"),
    ("텐동", "🍤", "텐동 전문점", "일식", "mid"),
    ("회덮밥", "🥗", "활어 회덮밥", "일식", "mid"),
    ("카레라이스", "🍛", "일본카레 전문점", "일식", "low"),
    ("파스타", "🍝", "파스타 레스토랑", "양식", "mid"),
    ("피자", "🍕", "화덕피자", "양식", "mid"),
    ("수제버거", "🍔", "수제버거 전문점", "양식", "mid"),
    ("스테이크덮밥", "🥩", "스테이크 덮밥", "양식", "mid"),
    ("리조또", "🧀", "이탈리안 리조또", "양식", "mid"),
    ("샌드위치", "🥪", "수제 샌드위치", "양식", "low"),
    ("쌀국수", "🍜", "베트남 쌀국수", "동남아식", "mid"),
    ("팟타이", "🥢", "태국음식 팟타이", "동남아식", "mid"),
    ("나시고랭", "🍳", "인도네시아 나시고랭", "동남아식", "mid"),
    ("인도커리", "🍛", "인도커리 난 전문점", "인도식", "mid"),
    ("타코", "🌮", "멕시칸 타코", "멕시코식", "mid"),
    ("브리또", "🌯", "멕시칸 브리또", "멕시코식", "low"),
    ("포케", "🥗", "하와이안 포케", "퓨전식", "mid"),
    ("퓨전파스타", "🍝", "퓨전 양식당", "퓨전식", "mid")
]

# --- 식당 텍스트 및 카테고리 정밀 검증 엔진 ---
def is_valid_specialized_restaurant(menu_name: str, place_name: str, category_name: str) -> bool:
    clean_name = place_name.replace(" ", "").upper()
    cat_full = category_name.replace(" ", "")

    if any(ex in cat_full for ex in EXCLUDED_CATEGORIES):
        return False
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
        if "구이" in clean_name and menu_name != "생선구이백반":
            return False
        if any(bad in clean_name for bad in [k.upper() for k in MEAT_SHOP_KEYWORDS]):
            return False

    if menu_name not in ["김밥", "떡볶이"]:
        if any(brand in clean_name for brand in MULTI_MENU_FRANCHISES):
            return False
        if "분식" in cat_full and not any(k in cat_full for k in ["일식", "양식", "한식", "중식", "아시아음식"]):
            return False

    if menu_name == "초밥":
        if any(fish in clean_name for fish in EVENING_RAW_FISH_KEYWORDS):
            return False
        if "회" in cat_full and not any(k in clean_name for k in ["스시", "초밥"]):
            return False

    if menu_name == "돈까스":
        is_tonkatsu = any(k in clean_name for k in TONKATSU_NAME_INDICATORS) or any(c in cat_full for c in ["돈가스", "돈까스"])
        if not is_tonkatsu:
            return False

    if menu_name == "잔치국수":
        if any(asian in cat_full for asian in ["아시아음식", "베트남", "태국", "동남아"]):
            return False
        if any(pho in clean_name for pho in VIETNAMESE_NOODLE_KEYWORDS):
            return False

    if menu_name in STRICT_SPECIALTY_NAME_RULES:
        required_words = STRICT_SPECIALTY_NAME_RULES[menu_name]
        if not any(req in clean_name for req in required_words):
            return False

    return True

# --- 실시간 웹 검색 스크래핑 기반 14:00 이후 오픈 식당 필터링 ---
def is_dinner_only_restaurant(place_name: str, address: str) -> bool:
    clean_pname = place_name.split()[0]
    region_chunk = " ".join(address.split()[:2]) if address else ""
    query = f"{region_chunk} {clean_pname} 영업시간".strip()

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    url = f"https://m.search.daum.net/search?w=tot&q={urllib.parse.quote(query)}"

    try:
        res = requests.get(url, headers=headers, timeout=0.8)
        if res.status_code == 200:
            text = res.text
            time_matches = re.findall(r"(\d{1,2}):(\d{2})\s*(?:~|-|에|오픈|영업)", text)
            for h_str, _ in time_matches:
                h = int(h_str)
                if 14 <= h <= 23:
                    return True
                if 9 <= h <= 13:
                    return False

            pm_matches = re.findall(r"오후\s*(\d{1,2})(?::(\d{2})|시)", text)
            for match in pm_matches:
                h = int(match[0])
                if h < 12:
                    h += 12
                if h >= 14:
                    return True
                if h <= 13:
                    return False
    except Exception:
        pass

    return False

# --- 인근 주차장(300m 이내) 보유 여부 검증 함수 ---
def has_nearby_parking(lat: float, lng: float, place_name: str) -> bool:
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
    is_franchise = any(f_name in p_name for f_name in KNOWN_FRANCHISE_BRANDS) or any(p_name.strip().endswith(sfx) for sfx in ["점", "호점", "직영점"])
    
    place["is_personal"] = not is_franchise
    score += (2.5 if is_franchise else -0.5)

    if menu_name == "돈까스" and any(k in p_name for k in TONKATSU_NAME_INDICATORS):
        score -= 2.0
    if menu_name == "초밥" and any(k in p_name for k in ["스시", "초밥"]):
        score -= 2.5
    if menu_name == "죽" and "죽" in p_name:
        score -= 2.0
    if menu_name == "국밥" and any(k in p_name for k in ["국밥", "순대", "순댓국", "돼지국밥"]):
        score -= 2.5
    if menu_name == "잔치국수":
        if any(k in p_name for k in ["잔치국수", "멸치국수", "할매국수"]):
            score -= 3.0
        elif "국수" in p_name:
            score -= 1.5
    if menu_name == "육개장":
        if any(k in p_name for k in ["육개장", "육대장"]):
            score -= 3.0

    if need_parking:
        score -= (3.5 if has_parking else 0.0)

    return score

# --- 카카오 공식 API 통신 함수 ---
def kakao_get_coordinates(query: str):
    if not KAKAO_REST_KEY:
        return None, None
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {"query": query.strip(), "size": 1}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=3.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                return float(docs[0]["y"]), float(docs[0]["x"])
    except Exception:
        pass
    return None, None

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

def kakao_search_places(lat: float, lng: float, menu_name: str, search_query: str, radius_km: float = 1.8, need_parking: bool = False):
    if not KAKAO_REST_KEY:
        return []
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    radius_meters = int(radius_km * 1000)

    query_text = f"{search_query} 주차" if need_parking else search_query

    params = {
        "query": query_text,
        "category_group_code": "FD6",
        "x": str(lng),
        "y": str(lat),
        "radius": min(radius_meters, 20000),
        "sort": "distance",
        "size": 15
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=3.0)
        docs = res.json().get("documents", []) if res.status_code == 200 else []
        if not docs and need_parking:
            params["query"] = search_query
            res = requests.get(url, headers=headers, params=params, timeout=3.0)
            docs = res.json().get("documents", []) if res.status_code == 200 else []

        if docs:
            candidates = []
            for d in docs:
                p_name = d.get("place_name", "")
                cat_name = d.get("category_name", "")
                if not is_valid_specialized_restaurant(menu_name, p_name, cat_name):
                    continue
                
                dist_m = float(d.get("distance", 0))
                p_lat = float(d.get("y"))
                p_lng = float(d.get("x"))
                
                parking_available = False
                if need_parking:
                    parking_available = has_nearby_parking(p_lat, p_lng, p_name)

                p_dict = {
                    "id": d.get("id", ""),
                    "name": p_name,
                    "category": cat_name.split(">")[-1].strip() if ">" in cat_name else cat_name,
                    "lat": p_lat,
                    "lng": p_lng,
                    "dist": round(dist_m / 1000, 2) if dist_m > 0 else 0.1,
                    "address": d.get("road_address_name") or d.get("address_name", ""),
                    "place_url": d.get("place_url", ""),
                    "has_parking": parking_available
                }
                p_dict["priority_score"] = calculate_priority(p_dict, menu_name, has_parking=parking_available, need_parking=need_parking)
                candidates.append(p_dict)
            
            if need_parking:
                candidates.sort(key=lambda x: (not x["has_parking"], x["priority_score"]))
            else:
                candidates.sort(key=lambda x: x["priority_score"])

            if candidates:
                valid_top = None
                for i in range(min(4, len(candidates))):
                    cand = candidates[i]
                    if is_dinner_only_restaurant(cand["name"], cand["address"]):
                        continue
                    valid_top = candidates.pop(i)
                    break
                if valid_top:
                    candidates.insert(0, valid_top)

            return candidates
    except Exception:
        pass
    return []

# --- 브라우저 GPS 수신 처리 ---
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

# --- 화면 레이아웃 상단부 ---
st.markdown("<h1 style='color: #2E1C10; font-size: 26px; font-weight: 800; margin: 0 0 4px 0;'>🍱 오늘 점심 뭐 먹지?</h1>", unsafe_allow_html=True)
st.markdown("<div style='color: #8C827A; font-size: 13px; margin-bottom: 12px;'>고민되는 점심 메뉴와 검증된 주변 밥집을 랜덤으로 골라드립니다.</div>", unsafe_allow_html=True)

if not has_key:
    st.warning("⚠️ **API 키 설정 필요**: `.streamlit/secrets.toml` 또는 Cloud Secrets에 `KAKAO_REST_KEY`를 설정해주세요.")

# 1. 위치 입력 섹션
st.markdown("<div class='section-title'>📍 위치</div>", unsafe_allow_html=True)
col_input, col_gps = st.columns([3.5, 1.2], vertical_alignment="center")

with col_input:
    region = st.text_input(
        "위치입력",
        value=st.session_state.region_input_val,
        placeholder="예시) 역삼역, 판교 테크노밸리, 홍대입구",
        key="main_region_input",
        label_visibility="collapsed"
    )
    if region != st.session_state.region_input_val:
        st.session_state.region_input_val = region
        st.session_state.gps_coords = None
        st.session_state.saved_result = None

    if not region.strip() and not st.session_state.gps_coords:
        st.session_state.saved_result = None

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

# 2. 반경 노출 섹션
clean_region = region.strip()
is_admin_region = False

if clean_region:
    is_spot = bool(re.search(r"(역|출구|거리|센터|스퀘어|타워|빌딩|공원|마트|백화점)$", clean_region))
    is_pure_admin = bool(re.search(r"([시군구읍면동]|\b\w+[0-9]*가)$", clean_region))
    if is_pure_admin and not is_spot:
        is_admin_region = True

should_show_radius = bool(clean_region and not is_admin_region)

if should_show_radius:
    st.markdown("<div class='radius-wrapper'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📏 탐색 반경</div>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.0, 1.2], vertical_alignment="center")
    current_preset = st.session_state.selected_radius_preset

    with c1:
        if st.button("🚶 인근", key="rbtn_walk", type="primary" if current_preset == "인근" else "secondary", use_container_width=True):
            if st.session_state.selected_radius_preset != "인근":
                st.session_state.selected_radius_preset = "인근"
                st.session_state.saved_result = None
                st.rerun()

    with c2:
        if st.button("🚲 근거리", key="rbtn_bike", type="primary" if current_preset == "근거리" else "secondary", use_container_width=True):
            if st.session_state.selected_radius_preset != "근거리":
                st.session_state.selected_radius_preset = "근거리"
                st.session_state.saved_result = None
                st.rerun()

    with c3:
        if st.button("🚗 원거리", key="rbtn_car", type="primary" if current_preset == "원거리" else "secondary", use_container_width=True):
            if st.session_state.selected_radius_preset != "원거리":
                st.session_state.selected_radius_preset = "원거리"
                st.session_state.saved_result = None
                st.rerun()

    with c4:
        if st.button("직접 입력", key="rbtn_custom", type="primary" if current_preset == "직접 입력" else "secondary", use_container_width=True):
            if st.session_state.selected_radius_preset != "직접 입력":
                st.session_state.selected_radius_preset = "직접 입력"
                st.session_state.saved_result = None
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
            st.session_state.saved_result = None
        radius_km = float(manual_radius)
        radius_display_text = f"직접 입력 {radius_km:.1f}km"
    else:
        radius_km = PRESET_RADIUS.get(st.session_state.selected_radius_preset, 1.8)
        radius_display_text = f"{st.session_state.selected_radius_preset} ({radius_km}km)"

    st.markdown("</div>", unsafe_allow_html=True)
else:
    radius_km = 1.8
    radius_display_text = "지역 인근"

# --- 3. 음식 종류 선택 섹션 ---
st.markdown("<div class='cuisine-wrapper'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>🍽️ 음식 종류</div>", unsafe_allow_html=True)

cu1, cu2, cu3, cu4 = st.columns(4)
current_cuisine = st.session_state.selected_cuisine

with cu1:
    if st.button("한식", key="cbtn_korean", type="primary" if current_cuisine == "한식" else "secondary", use_container_width=True):
        if st.session_state.selected_cuisine != "한식":
            st.session_state.selected_cuisine = "한식"
            st.session_state.saved_result = None
            st.rerun()
with cu2:
    if st.button("중식", key="cbtn_chinese", type="primary" if current_cuisine == "중식" else "secondary", use_container_width=True):
        if st.session_state.selected_cuisine != "중식":
            st.session_state.selected_cuisine = "중식"
            st.session_state.saved_result = None
            st.rerun()
with cu3:
    if st.button("일식", key="cbtn_japanese", type="primary" if current_cuisine == "일식" else "secondary", use_container_width=True):
        if st.session_state.selected_cuisine != "일식":
            st.session_state.selected_cuisine = "일식"
            st.session_state.saved_result = None
            st.rerun()
with cu4:
    if st.button("양식", key="cbtn_western", type="primary" if current_cuisine == "양식" else "secondary", use_container_width=True):
        if st.session_state.selected_cuisine != "양식":
            st.session_state.selected_cuisine = "양식"
            st.session_state.saved_result = None
            st.rerun()

st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

cu5, cu6, cu7, cu8 = st.columns(4)
with cu5:
    if st.button("동남아식", key="cbtn_asian", type="primary" if current_cuisine == "동남아식" else "secondary", use_container_width=True):
        if st.session_state.selected_cuisine != "동남아식":
            st.session_state.selected_cuisine = "동남아식"
            st.session_state.saved_result = None
            st.rerun()
with cu6:
    if st.button("인도식", key="cbtn_indian", type="primary" if current_cuisine == "인도식" else "secondary", use_container_width=True):
        if st.session_state.selected_cuisine != "인도식":
            st.session_state.selected_cuisine = "인도식"
            st.session_state.saved_result = None
            st.rerun()
with cu7:
    if st.button("멕시코식", key="cbtn_mexican", type="primary" if current_cuisine == "멕시코식" else "secondary", use_container_width=True):
        if st.session_state.selected_cuisine != "멕시코식":
            st.session_state.selected_cuisine = "멕시코식"
            st.session_state.saved_result = None
            st.rerun()
with cu8:
    if st.button("퓨전식", key="cbtn_fusion", type="primary" if current_cuisine == "퓨전식" else "secondary", use_container_width=True):
        if st.session_state.selected_cuisine != "퓨전식":
            st.session_state.selected_cuisine = "퓨전식"
            st.session_state.saved_result = None
            st.rerun()

st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

if st.button("모두 (종류 구분 없음)", key="cbtn_all", type="primary" if current_cuisine == "모두" else "secondary", use_container_width=True):
    if st.session_state.selected_cuisine != "모두":
        st.session_state.selected_cuisine = "모두"
        st.session_state.saved_result = None
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# --- 4. 음식(식사 기준) 가격 & 주차 가능 여부 선택 섹션 ---
st.markdown("<div class='filter-wrapper'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>💵 음식(식사 기준) 가격</div>", unsafe_allow_html=True)

p1, p2, p3, p4 = st.columns(4)
current_price = st.session_state.selected_price

with p1:
    if st.button("1만원 이하", key="pbtn_low", type="primary" if current_price == "1만원 이하" else "secondary", use_container_width=True):
        if st.session_state.selected_price != "1만원 이하":
            st.session_state.selected_price = "1만원 이하"
            st.session_state.saved_result = None
            st.rerun()
with p2:
    if st.button("1~2만원", key="pbtn_mid", type="primary" if current_price == "1~2만원" else "secondary", use_container_width=True):
        if st.session_state.selected_price != "1~2만원":
            st.session_state.selected_price = "1~2만원"
            st.session_state.saved_result = None
            st.rerun()
with p3:
    if st.button("2만원 이상", key="pbtn_high", type="primary" if current_price == "2만원 이상" else "secondary", use_container_width=True):
        if st.session_state.selected_price != "2만원 이상":
            st.session_state.selected_price = "2만원 이상"
            st.session_state.saved_result = None
            st.rerun()
with p4:
    if st.button("금액 상관 없음", key="pbtn_any", type="primary" if current_price == "금액 상관 없음" else "secondary", use_container_width=True):
        if st.session_state.selected_price != "금액 상관 없음":
            st.session_state.selected_price = "금액 상관 없음"
            st.session_state.saved_result = None
            st.rerun()

st.markdown("<div class='section-title'>🅿️ 주차 가능 여부</div>", unsafe_allow_html=True)
pk1, pk2 = st.columns(2)
current_parking = st.session_state.selected_parking

with pk1:
    if st.button("식당 주차장 혹은 인근 주차장 있음", key="pkbtn_yes", type="primary" if current_parking == "식당 주차장 혹은 인근 주차장 있음" else "secondary", use_container_width=True):
        if st.session_state.selected_parking != "식당 주차장 혹은 인근 주차장 있음":
            st.session_state.selected_parking = "식당 주차장 혹은 인근 주차장 있음"
            st.session_state.saved_result = None
            st.rerun()
with pk2:
    if st.button("주차 불필요", key="pkbtn_any", type="primary" if current_parking == "주차 불필요" else "secondary", use_container_width=True):
        if st.session_state.selected_parking != "주차 불필요":
            st.session_state.selected_parking = "주차 불필요"
            st.session_state.saved_result = None
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# 경고 안내문 표시 영역
region_warning_spot = st.empty()
spin_triggered = False
selected_candidates = []

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

# --- 5. 룰렛 돌리기 섹션 ---
st.markdown("<div class='section-title'>🎯 룰렛 돌리기</div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div>
                <div style="font-size: 15.5px; font-weight: 800; color: #2E1C10;">🎲 점심 메뉴 룰렛</div>
                <div style="font-size: 12.5px; color: #8C827A; margin-top: 1px;">선택하신 조건에 맞춰 무작위로 점심 메뉴와 밥집을 추천합니다!</div>
            </div>
            <span style="font-size: 22px;">🎰</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("🎲 랜덤 룰렛 돌리기", use_container_width=True, type="primary", key="btn_trigger_random"):
        if not region.strip() and not st.session_state.gps_coords:
            show_location_warning()
        elif not st.session_state.selected_cuisine:
            show_cuisine_warning()
        else:
            region_warning_spot.empty()
            cu = st.session_state.selected_cuisine
            pr = st.session_state.selected_price

            price_map = {"1만원 이하": "low", "1~2만원": "mid", "2만원 이상": "high"}
            target_pr = price_map.get(pr, None)

            if cu == "모두":
                candidates_pool = [f for f in DEFAULT_FOODS if f[0] != "죽"]
            else:
                candidates_pool = [f for f in DEFAULT_FOODS if f[3] == cu and f[0] != "죽"]

            if target_pr:
                price_filtered = [f for f in candidates_pool if f[4] == target_pr]
                selected_candidates = price_filtered if price_filtered else candidates_pool
            else:
                selected_candidates = candidates_pool

            spin_triggered = True

card_spot = st.empty()
detail_spot = st.empty()

# --- 6. 룰렛 실행 및 고속 탐색 로직 ---
if spin_triggered and selected_candidates:
    detail_spot.empty()

    if st.session_state.gps_coords:
        c_lat, c_lng = st.session_state.gps_coords
    else:
        with st.spinner(f"'{region}' 위치 확인 중..."):
            c_lat, c_lng = kakao_get_coordinates(region)

    if not c_lat:
        region_warning_spot.error(f"⚠️ '{region}' 위치를 찾지 못했습니다. 주요 건물이나 역 이름을 입력해 보세요.")
    else:
        final_menu = None
        places = []
        shuffled = selected_candidates.copy()
        random.shuffle(shuffled)

        need_parking_flag = (st.session_state.selected_parking == "식당 주차장 혹은 인근 주차장 있음")

        with st.spinner("조건에 맞는 점심 식당을 필터링하는 중..."):
            for m_name, m_emoji, m_kw, _, _ in shuffled[:6]:
                found = kakao_search_places(c_lat, c_lng, m_name, m_kw, radius_km=radius_km, need_parking=need_parking_flag)
                if found:
                    final_menu = (m_name, m_emoji)
                    places = found
                    break

            if not places:
                cu = st.session_state.selected_cuisine
                fallback_kw = "백반 가정식" if cu in ["한식", "모두"] else f"{cu} 전문점"
                fallback_menu = "백반·가정식" if cu in ["한식", "모두"] else f"{cu} 밥집"
                fallback_found = kakao_search_places(c_lat, c_lng, fallback_menu, fallback_kw, radius_km=radius_km, need_parking=need_parking_flag)
                if fallback_found:
                    final_menu = (fallback_menu, "🍱")
                    places = fallback_found

        if final_menu and places:
            for i in range(5):
                temp = random.choice(selected_candidates)
                card_spot.markdown(
                    f"""
                    <div style="text-align: center; margin: 16px 0 14px 0; padding: 20px 18px; 
                                background: #FFFDF9; border-radius: 20px; border: 1.5px solid #F5D5B8;
                                box-shadow: 0 4px 16px rgba(245, 213, 184, 0.35);">
                        <div style="font-size: 54px; line-height: 1; margin-bottom: 6px;">{temp[1]}</div>
                        <div style="color: #2E1C10; font-size: 22px; font-weight: 800; margin: 4px 0;">{temp[0]}</div>
                        <p style="color: #8C827A; font-size: 13px; margin: 0;">{radius_display_text} 기준 맛집 추첨 중... 🎲</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                time.sleep(0.04 + (i * 0.02))

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
            region_warning_spot.warning(f"⚠️ 설정하신 조건 내에 만족하는 식당을 찾지 못했습니다. 반경을 넓히거나 가격/주차 옵션을 조정해 보세요!")

# --- 7. 결과 화면 출력 (HTML 마크다운 파싱 오류 완벽 해결) ---
has_valid_location = bool(region.strip() or st.session_state.gps_coords)
res = st.session_state.saved_result

if has_valid_location and res is not None and res.get("places"):
    card_html = (
        f'<div style="text-align: center; margin: 18px 0 16px 0; padding: 24px 20px; '
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
    card_spot.markdown(card_html, unsafe_allow_html=True)

    with detail_spot.container():
        places = res["places"]
        top_pick = places[0]

        tag_text = "개인 전문점" if top_pick.get("is_personal", True) else "프랜차이즈"
        tag_bg = "#FCEFE6" if top_pick.get("is_personal", True) else "#F7E6D2"
        tag_color = "#C85A32" if top_pick.get("is_personal", True) else "#8A532B"

        parking_badge = ""
        if top_pick.get("has_parking", False):
            parking_badge = '<span style="font-size: 11px; background: #E8F4EA; color: #2E7D32; padding: 2px 7px; border-radius: 6px; font-weight: 700;">🅿 주차 편리</span>'

        # 들여쓰기로 인한 코드블록 변환 방지를 위해 좌측 공백 제거(한 줄 구성)
        top_pick_html = (
            f'<div style="margin-bottom: 20px; padding: 22px 18px; '
            f'background: #FFFDF9; border-radius: 22px; border: 1.5px solid #F5D5B8; '
            f'box-shadow: 0 4px 18px rgba(245, 213, 184, 0.35); text-align: center;">'
            f'<div style="display: flex; justify-content: center; align-items: center; gap: 6px; margin-bottom: 8px; flex-wrap: wrap;">'
            f'<span style="font-size: 12.5px; color: #E86A3E; font-weight: 700;">⭐ 오늘의 1픽 추천 밥집</span>'
            f'<span style="font-size: 11px; background: {tag_bg}; color: {tag_color}; padding: 2px 7px; border-radius: 6px; font-weight: 700;">{tag_text}</span>'
            f'<span style="font-size: 11px; background: #F3ECE4; color: #6E5F55; padding: 2px 7px; border-radius: 6px; font-weight: 600;">{top_pick.get("category", "식당")}</span>'
            f'{parking_badge}'
            f'</div>'
            f'<div style="margin: 4px 0;">'
            f'<a href="{top_pick.get("place_url", "#")}" target="_blank" style="text-decoration: none; color: #2E1C10; font-size: 23px; font-weight: 900; display: inline-block;">'
            f'{top_pick["name"]}'
            f'</a>'
            f'</div>'
            f'<div style="font-size: 13px; color: #7A6F66; margin-top: 4px;">'
            f'📍 {top_pick["address"]} (약 {top_pick["dist"]}km)'
            f'</div>'
            f'</div>'
        )
        st.markdown(top_pick_html, unsafe_allow_html=True)

        if len(places) > 1:
            st.markdown(f"<div style='font-size: 14px; font-weight: 700; color: #2E1C10; margin-bottom: 8px;'>근처 다른 후보 ({len(places)-1}곳)</div>", unsafe_allow_html=True)
            other_candidates = places[1:11]
            col_left, col_right = st.columns(2)

            for idx, p in enumerate(other_candidates, start=1):
                p_tag = "개인" if p.get("is_personal", True) else "체인"
                short_cat = p.get('category', '식당').split('/')[-1].strip()
                target_col = col_left if idx % 2 != 0 else col_right

                with target_col:
                    cand_html = (
                        f'<div style="display: flex; justify-content: space-between; align-items: center; '
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
        st.markdown("<h3 style='margin-bottom: 2px; font-size: 16px; font-weight: 800; color: #2E1C10;'>🗺️ 식당 위치 지도</h3>", unsafe_allow_html=True)
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
                icon=folium.Icon(color="blue", icon="utensils", prefix="fa")
            ).add_to(m)

        unique_map_key = f"map_{res['id']}_{int(top_pick['lat'] * 10000)}"
        st_folium(m, width="100%", height=380, key=unique_map_key, returned_objects=[])

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        kakao_directions_url = f"https://map.kakao.com/link/to/{urllib.parse.quote(top_pick['name'])},{top_pick['lat']},{top_pick['lng']}"
        st.link_button(f"🧭 '{top_pick['name']}' 길찾기 바로가기", kakao_directions_url, use_container_width=True)
