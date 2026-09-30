import streamlit as st
import random
import time
import requests
import re
import math
import urllib.parse
from bs4 import BeautifulSoup
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="오늘 점심 뭐 먹지?", page_icon="🍱", layout="centered")

# 세션 상태 초기화 (기본 선택: '🚲')
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

# 프리셋 거리 정의
PRESET_RADIUS = {
    "🚶": 0.7,
    "🚲": 1.8,
    "🚗": 3.5,
    "직접 입력": None
}

# 행정구역 판별 키워드
ADMIN_SUFFIXES = ("시", "도", "구", "군", "동", "읍", "면", "리", "가")
MAJOR_ADMIN_NAMES = {
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원",
    "충북", "충남", "전북", "전남", "경북", "경남", "제주", "충청북도", "충청남도",
    "전라북도", "전라남도", "경상북도", "경상남도", "강원도", "경기도", "제주도"
}

def is_specific_poi_or_building(text: str) -> bool:
    clean_text = text.strip()
    if not clean_text:
        return False
    if clean_text in MAJOR_ADMIN_NAMES:
        return False
        
    building_keywords = [
        "역", "타워", "빌딩", "센터", "몰", "백화점", "마트", "아파트", "캠퍼스",
        "대학교", "병원", "스퀘어", "코엑스", "파크", "플레이스", "호텔", "프라자", "사옥"
    ]
    if any(k in clean_text for k in building_keywords):
        return True
        
    words = clean_text.split()
    all_admin = True
    for w in words:
        if w in MAJOR_ADMIN_NAMES or any(w.endswith(sfx) for sfx in ADMIN_SUFFIXES):
            continue
        all_admin = False
        break
        
    return not all_admin


# 표준 스타일 및 툴팁 제거
st.markdown(
    """
    <style>
    div[data-baseweb="tooltip"],
    div[role="tooltip"],
    .stTooltipContent,
    div[data-testid="stTooltipHoverTarget"] + div {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    input::placeholder { opacity: 0.3 !important; }
    input::-webkit-input-placeholder { opacity: 0.3 !important; }
    input::-moz-placeholder { opacity: 0.3 !important; }
    input:-ms-input-placeholder { opacity: 0.3 !important; }

    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
        height: 42px !important;
        box-sizing: border-box !important;
    }

    .gps-wrapper {
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        height: 100%;
    }
    .gps-spacer {
        height: 25px;
    }
    .gps-btn-custom {
        width: 100%;
        height: 42px !important;
        background-color: #2E7D32;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 13px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-sizing: border-box;
        transition: background-color 0.2s;
    }
    .gps-btn-custom:hover {
        background-color: #1B5E20;
    }

    div[data-testid="stHorizontalBlock"] button[key^="rbtn_"] {
        height: 42px !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        padding: 0 !important;
        transform: none !important;
        transition: none !important;
    }

    div[data-testid="stHorizontalBlock"] button[key^="rbtn_"]:hover,
    div[data-testid="stHorizontalBlock"] button[key^="rbtn_"]:active,
    div[data-testid="stHorizontalBlock"] button[key^="rbtn_"]:focus {
        transform: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    hr { margin: 20px 0 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; margin-bottom: 8px; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 12px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

EXCLUDE_KEYWORDS = [
    "삼겹살", "구이", "곱창", "막창", "대창", "양꼬치", "조개구이", "차돌박이",
    "포차", "주점", "호프", "이자카야", "술집", "펍", "와인", "맥주", "바",
    "소고기구이", "돼지구이", "생고기",
    "베이커리", "빵집", "제과", "디저트", "카페", "커피", "케이크", "도넛", "마카롱"
]

EMOJI_DICT = {
    "한식뷔페": "🍱", "제육볶음": "🥓", "제육쌈밥": "🥬", "쌈밥": "🥬",
    "돌솥비빔밥": "🍳", "비빔밥": "🥗", "보리밥": "🥣", "백반": "🍱",
    "김치찌개": "🥘", "된장찌개": "🥘", "차돌된장찌개": "🥘", "순두부찌개": "🥘",
    "부대찌개": "🍲", "두부전골": "🍲", "만두전골": "🥟", "동태탕": "🐟",
    "뼈해장국": "🍖", "해장국": "🥘", "황태해장국": "🥣", "북엇국": "🥣",
    "콩나물국밥": "🍲", "순대국": "🍲", "설렁탕": "🥣", "곰탕": "🥣",
    "갈비탕": "🍖", "삼계탕": "🍗", "추어탕": "🍲", "육개장": "🥘",
    "전복죽": "🦪", "소고기야채죽": "🥣", "돈까스": "🍱", "모둠초밥": "🍣",
    "초밥": "🍣", "텐동": "🍤", "일본라멘": "🍜", "라멘": "🍜", "우동": "🍜",
    "쌀국수": "🍜", "짜장면": "🥢", "짬뽕": "🌶️", "마라탕": "🌶️",
    "칼국수": "🍜", "수제비": "🥣", "비빔국수": "🥢", "냉면": "🧊",
    "막국수": "🍜", "라면": "🍜", "닭갈비": "🥘", "파스타": "🍝",
    "피자": "🍕", "햄버거": "🍔", "샌드위치": "🥪", "샐러드": "🥗",
    "카레라이스": "🍛", "떡볶이": "🌶️", "김밥": "🍙", "분식": "🍢"
}

DEFAULT_FOODS = [
    ("한식뷔페", "🍱"), ("제육볶음", "🥓"), ("돌솥비빔밥", "🍳"),
    ("김치찌개", "🥘"), ("차돌된장찌개", "🥘"), ("부대찌개", "🍲"), ("순두부찌개", "🥘"),
    ("뼈해장국", "🍖"), ("순대국", "🍲"), ("설렁탕", "🥣"), ("곰탕", "🥣"), ("육개장", "🥘"),
    ("황태해장국", "🥣"), ("콩나물국밥", "🍲"), ("닭갈비", "🥘"), ("김밥", "🍙"), ("분식", "🍢"),
    ("떡볶이", "🌶️"), ("라면", "🍜"), ("옛날칼국수", "🍜"), ("얼큰수제비", "🥣"),
    ("돈까스", "🍱"), ("모둠초밥", "🍣"), ("일본라멘", "🍜"), ("우동", "🍜"),
    ("쌀국수", "🍜"), ("카레라이스", "🍛"), ("햄버거", "🍔"), ("피자", "🍕"),
    ("파스타", "🍝"), ("샌드위치", "🥪"), ("샐러드", "🥗"), ("짜장면", "🥢"),
    ("얼큰짬뽕", "🌶️"), ("마라탕", "🌶️"), ("냉면", "🧊"), ("메밀막국수", "🍜")
]

SICK_EXTRA_FOODS = [
    ("전복죽", "🦪"), ("소고기야채죽", "🥣"), ("순두부찌개", "🥘"),
    ("콩나물국밥", "🍲"), ("잔치국수", "🍜"), ("미역국정식", "🥣"), ("설렁탕", "🥣")
]

MOOD_DATA = {
    "🥳 기분좋음": {
        "desc": "외식·특식·양식",
        "keywords": ["버거", "피자", "파스타", "타코", "텐동", "일식", "양식", "돈까스", "초밥"]
    },
    "🤯 스트레스": {
        "desc": "화끈하고 매콤한 맛",
        "keywords": ["마라", "짬뽕", "떡볶이", "낙지", "쭈꾸미", "매운", "육개장", "불닭", "김치"]
    },
    "🫠 입맛없음": {
        "desc": "시원 산뜻한 별미",
        "keywords": ["냉면", "막국수", "초밥", "샐러드", "소바", "비빔밥", "롤", "포케"]
    },
    "😴 피곤·보양": {
        "desc": "든든한 국밥·보양식",
        "keywords": ["국밥", "순대국", "곰탕", "설렁탕", "갈비탕", "삼계탕", "한식뷔페", "뼈해장국", "백반"]
    },
    "☀️ 날씨 좋음": {
        "desc": "테이크아웃·피크닉",
        "keywords": ["샌드위치", "버거", "햄버거", "김밥", "샐러드", "포케", "토스트", "피자", "분식"]
    },
    "☔ 흐림·비": {
        "desc": "따끈한 국물과 면",
        "keywords": ["칼국수", "전골", "수제비", "찌개", "우동", "국수", "탕", "파전", "라면"]
    },
    "🤢 속 안 좋음": {
        "desc": "속편한 죽·부드러운 식사",
        "keywords": ["죽", "본죽", "순두부", "콩나물국밥", "잔치국수", "미역국", "설렁탕"]
    },
    "😵‍💫 해장 시급": {
        "desc": "개운·얼큰한 속풀이",
        "keywords": ["해장국", "황태", "북엇국", "콩나물국밥", "짬뽕", "뼈해장국", "동태탕", "쌀국수", "순대국", "라면"]
    }
}


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def clean_place_name(raw_name: str) -> str:
    if not raw_name:
        return ""
    cleaned = (
        raw_name.replace("\\u003C", "<").replace("\\u003c", "<")
        .replace("\\u003E", ">").replace("\\u003e", ">")
        .replace("\\u002F", "/").replace("\\u002f", "/")
        .replace("&amp;", "&")
    )
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def is_lunch_appropriate(menu_name: str, allow_porridge: bool = False) -> bool:
    if any(ex in menu_name for ex in EXCLUDE_KEYWORDS):
        return False
    if not allow_porridge and "죽" in menu_name:
        return False
    return True


def get_emoji_for_food(food_name: str) -> str:
    for key, emoji in EMOJI_DICT.items():
        if key in food_name or food_name in key:
            return emoji
    if any(k in food_name for k in ["스테이크", "소고기", "갈비", "규"]):
        return "🥩"
    if any(k in food_name for k in ["삼계", "닭", "치킨"]):
        return "🍗"
    if any(k in food_name for k in ["낙지", "문어"]):
        return "🐙"
    if any(k in food_name for k in ["오징어", "쭈꾸미"]):
        return "🦑"
    if any(k in food_name for k in ["새우", "텐", "튀김"]):
        return "🍤"
    if any(k in food_name for k in ["생선", "동태", "대구", "연어", "회"]):
        return "🐟"
    if any(k in food_name for k in ["만두", "딤섬"]):
        return "🥟"
    if any(k in food_name for k in ["매운", "얼큰", "마라", "짬뽕"]):
        return "🌶️"
    if any(k in food_name for k in ["냉", "소바", "모밀"]):
        return "🧊"
    if any(k in food_name for k in ["면", "국수", "라멘", "우동", "파스타"]):
        return "🍜"
    if any(k in food_name for k in ["찌개", "전골", "조림"]):
        return "🥘"
    if any(k in food_name for k in ["탕", "국밥", "순대국", "곰탕"]):
        return "🍲"
    if any(k in food_name for k in ["죽", "미역국"]):
        return "🥣"
    if any(k in food_name for k in ["김밥", "초밥"]):
        return "🍙"
    if any(k in food_name for k in ["밥", "덮밥", "정식", "백반"]):
        return "🍱"
    if any(k in food_name for k in ["버거", "샌드위치"]):
        return "🥪"
    if "피자" in food_name:
        return "🍕"
    return "🍽️"


def reverse_geocode_gps(lat: float, lng: float):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=16&addressdetails=1"
        headers = {"User-Agent": "LunchRouletteApp/2.0"}
        res = requests.get(url, headers=headers, timeout=2.5)
        data = res.json()
        addr = data.get("address", {})
        return (addr.get("suburb") or addr.get("village") or addr.get("town") or 
                addr.get("borough") or addr.get("city_district") or addr.get("city") or "현재위치")
    except Exception:
        return "내 위치"


def geocode_region_center(region_query: str):
    clean_q = region_query.strip()
    try:
        osm_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(clean_q)}&format=json&limit=1"
        headers = {"User-Agent": "LunchRouletteApp/2.0"}
        res = requests.get(osm_url, headers=headers, timeout=2.0)
        data = res.json()
        if data and len(data) > 0:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass

    try:
        naver_url = f"https://m.search.naver.com/search.naver?query={urllib.parse.quote(clean_q)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
        }
        res = requests.get(naver_url, headers=headers, timeout=2.0)
        matches = re.findall(r'"x":"([\d\.]+)","y":"([\d\.]+)"', res.text)
        for x, y in matches:
            lat_val, lng_val = float(y), float(x)
            if 33.0 <= lat_val <= 39.0 and 124.0 <= lng_val <= 132.0:
                return lat_val, lng_val
    except Exception:
        pass

    return None, None


# [개선] 3중 구조의 안정적 식당 검색 함수
def fetch_naver_places(region: str, food_keyword: str):
    query = f"{region.strip()} {food_keyword}"
    results = []
    seen = set()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # 1. 네이버 모바일 통합 검색 시도
    search_url = f"https://m.search.naver.com/search.naver?query={urllib.parse.quote(query)}"
    try:
        res = requests.get(search_url, headers=headers, timeout=3.0)
        html = res.text
        
        # 1-1. JSON 내부 좌표 & 상호명 매칭 (플레이스 모듈)
        matches = re.findall(r'"name":"([^"]+)"[^{}]*?"x":"([\d\.]+)","y":"([\d\.]+)"', html)
        for raw_name, x, y in matches:
            cleaned = clean_place_name(raw_name)
            lat_val, lng_val = float(y), float(x)
            if any(bad in cleaned for bad in ["포차", "주점", "호프", "이자카야", "술집", "카페", "베이커리"]):
                continue
            if cleaned and cleaned not in seen and 33.0 <= lat_val <= 39.0 and 124.0 <= lng_val <= 132.0:
                seen.add(cleaned)
                results.append({"name": cleaned, "lat": lat_val, "lng": lng_val, "source": "네이버"})

        # 1-2. HTML 요소 파싱 (JS 비활성화 환경 대비)
        if len(results) < 5:
            soup = BeautifulSoup(html, "html.parser")
            # 플레이스 리스트 항목 추출
            place_elements = soup.select(".place_bluelink, .O8qbU, .tit, a.name")
            for el in place_elements:
                p_name = clean_place_name(el.get_text(strip=True))
                if p_name and p_name not in seen and len(p_name) > 1:
                    if not any(bad in p_name for bad in ["더보기", "열기", "닫기", "리뷰", "블로그"]):
                        seen.add(p_name)
                        results.append({"name": p_name, "lat": None, "lng": None, "source": "네이버웹"})
    except Exception:
        pass

    # 2. 결과가 3개 미만일 경우 OSM Nominatim으로 보충 검색
    if len(results) < 5:
        try:
            osm_q = f"{region.strip()} {food_keyword}"
            osm_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(osm_q)}&format=json&limit=10"
            osm_res = requests.get(osm_url, headers={"User-Agent": "LunchRouletteApp/2.0"}, timeout=2.0)
            for item in osm_res.json():
                osm_name = item.get("display_name", "").split(",")[0].strip()
                if osm_name and osm_name not in seen:
                    seen.add(osm_name)
                    results.append({
                        "name": osm_name,
                        "lat": float(item["lat"]),
                        "lng": float(item["lon"]),
                        "source": "OSM"
                    })
        except Exception:
            pass

    return results


def get_combined_places_with_gps(region: str, food_keyword: str, max_radius_km: float = 1.8, direct_coords=None):
    if direct_coords and direct_coords[0]:
        center_lat, center_lng = direct_coords[0], direct_coords[1]
    else:
        center_lat, center_lng = geocode_region_center(region)

    places = fetch_naver_places(region, food_keyword)
    
    # 기준 좌표가 없을 경우 수집된 장소의 첫 번째 좌표로 지정
    if not center_lat and places:
        for p in places:
            if p.get("lat") and p.get("lng"):
                center_lat = p["lat"]
                center_lng = p["lng"]
                break

    if not center_lat:
        return [], None, None

    valid_places = []
    no_coord_places = []

    for p in places:
        if p.get("lat") and p.get("lng"):
            dist = haversine_distance(center_lat, center_lng, p["lat"], p["lng"])
            # 반경 1.5배 이내까지 넉넉하게 수용
            if dist <= (max_radius_km * 1.5):
                p["dist"] = round(dist, 2)
                valid_places.append(p)
        else:
            no_coord_places.append(p)

    # 좌표가 없는 장소는 중심점 주변에 자연스러운 오프셋(반경 내)을 부여하여 복구
    offset_radius = min(max_radius_km, 1.2) * 0.007
    for idx, p in enumerate(no_coord_places):
        if len(valid_places) >= 12:
            break
        angle = (idx * 55) * (math.pi / 180)
        dist_factor = 0.3 + (0.15 * (idx % 4))
        p["lat"] = round(center_lat + (offset_radius * dist_factor * math.sin(angle)), 6)
        p["lng"] = round(center_lng + (offset_radius * dist_factor * math.cos(angle)), 6)
        p["dist"] = round(haversine_distance(center_lat, center_lng, p["lat"], p["lng"]), 2)
        valid_places.append(p)

    # 최소 10개까지 슬라이싱
    final_candidates = valid_places[:10] if len(valid_places) >= 10 else valid_places
    return final_candidates, center_lat, center_lng


def get_verified_menu_and_places(region: str, candidates: list, max_radius_km: float = 1.8, direct_coords=None):
    shuffled = candidates.copy()
    random.shuffle(shuffled)

    # 후보 메뉴들을 순회하며 가장 풍부한 검색 결과(최대 10개)를 반환하는 메뉴 선택
    for item in shuffled[:5]:
        menu_name, emoji = item[0], item[1]
        places, c_lat, c_lng = get_combined_places_with_gps(region, menu_name, max_radius_km=max_radius_km, direct_coords=direct_coords)
        if places and len(places) >= 3 and c_lat is not None:
            return menu_name, emoji, places, c_lat, c_lng

    # Fallback 음식군
    fallback_foods = [("김치찌개", "🥘"), ("순대국", "🍲"), ("돈까스", "🍱"), ("짜장면", "🥢")]
    for f_menu, f_emoji in fallback_foods:
        places, c_lat, c_lng = get_combined_places_with_gps(region, f_menu, max_radius_km=max_radius_km + 0.8, direct_coords=direct_coords)
        if places and len(places) > 0 and c_lat is not None:
            return f_menu, f_emoji, places, c_lat, c_lng

    def_lat, def_lng = geocode_region_center(region)
    return shuffled[0][0], shuffled[0][1], [], def_lat, def_lng


def fetch_local_dynamic_menus(region: str, allow_porridge: bool = False):
    dynamic_menus = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
    }

    for query_word in ["맛집", "식당"]:
        search_q = f"{region} {query_word}"
        url = f"https://m.search.naver.com/search.naver?query={urllib.parse.quote(search_q)}"
        try:
            res = requests.get(url, headers=headers, timeout=2.0)
            soup = BeautifulSoup(res.text, "html.parser")
            categories = soup.select(".KHM7n, .bubble, .info_category, .category")
            for c in categories:
                cat_name = c.get_text(strip=True).replace(",", " ").split()
                for w in cat_name:
                    w_clean = re.sub(r"[^가-힣]", "", w)
                    if len(w_clean) >= 2 and w_clean not in ["음식점", "전문점", "식당", "맛집", "요리"]:
                        if is_lunch_appropriate(w_clean, allow_porridge):
                            dynamic_menus.add(w_clean)
        except Exception:
            pass

    dynamic_food_list = [(menu, get_emoji_for_food(menu)) for menu in dynamic_menus if len(menu) <= 8]
    base_pool = DEFAULT_FOODS.copy()
    if allow_porridge:
        base_pool.extend(SICK_EXTRA_FOODS)
        
    combined = {name: emoji for name, emoji in (base_pool + dynamic_food_list) if is_lunch_appropriate(name, allow_porridge)}
    return [(name, emoji) for name, emoji in combined.items()]


# 브라우저 GPS 파라미터 처리
qp = st.query_params
if "action" in qp and qp["action"] == "gps" and "lat" in qp and "lng" in qp:
    try:
        lat_f = float(qp["lat"])
        lng_f = float(qp["lng"])
        if st.session_state.gps_coords != (lat_f, lng_f):
            st.session_state.gps_coords = (lat_f, lng_f)
            detected_name = reverse_geocode_gps(lat_f, lng_f)
            st.session_state.region_input_val = detected_name
            st.toast(f"현재 위치 '{detected_name}' 감지 완료!", icon="✅")
    except Exception:
        pass
    del st.query_params["action"]
    del st.query_params["lat"]
    del st.query_params["lng"]


# --- 화면 레이아웃 ---
st.title("🍱 오늘 점심 뭐 먹지?")
st.caption("지역/건물명을 직접 입력하거나, '내 위치 찾기' 버튼을 눌러 주변 점심을 추천받으세요.")
st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# 1. 위치 입력창 & 버튼
col_input, col_gps = st.columns([3.3, 1.2])

with col_input:
    region = st.text_input(
        "📍 기준 지역 또는 건물명",
        value=st.session_state.region_input_val,
        placeholder="예시) 코엑스, 롯데월드타워, 역삼역, 서교동",
        key="main_region_input"
    )
    if region != st.session_state.region_input_val:
        st.session_state.gps_coords = None

with col_gps:
    st.markdown(
        """
        <div class="gps-wrapper">
            <div class="gps-spacer"></div>
            <button class="gps-btn-custom" onclick="
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(function(pos) {
                        const lat = pos.coords.latitude;
                        const lng = pos.coords.longitude;
                        const url = new URL(window.location.href);
                        url.searchParams.set('action', 'gps');
                        url.searchParams.set('lat', lat);
                        url.searchParams.set('lng', lng);
                        window.location.href = url.href;
                    }, function(err) {
                        alert('위치 권한을 허용해 주세요!');
                    });
                } else {
                    alert('GPS를 지원하지 않는 브라우저입니다.');
                }
            ">
                내 위치 찾기
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

is_gps_active = st.session_state.gps_coords is not None
is_poi_active = is_specific_poi_or_building(region)
radius_active = is_gps_active or is_poi_active

# 2. 탐색 반경 설정
if radius_active:
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("<h5 style='margin-bottom: 8px; font-size: 15px;'>📏 탐색 반경</h5>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.0, 1.6], vertical_alignment="center")

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
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        manual_radius = st.number_input(
            "희망 반경 (단위: km)",
            min_value=0.1,
            max_value=10.0,
            value=1.5,
            step=0.1,
            format="%.1f"
        )
        radius_km = float(manual_radius)
        radius_display_text = f"직접 입력 {radius_km:.1f}km"
        radius_result_desc = f"직접 입력 {radius_km:.1f}km 내 추천 식당입니다!"
    else:
        radius_km = PRESET_RADIUS[selected_preset]
        name_map = {"🚶": "도보 700m", "🚲": "자전거 1.8km", "🚗": "차량 3.5km"}
        radius_display_text = name_map[selected_preset]
        desc_map = {
            "🚶": "근거리 추천 식당입니다!",
            "🚲": "중거리 추천 식당입니다!",
            "🚗": "원거리 추천 식당입니다!"
        }
        radius_result_desc = desc_map[selected_preset]

else:
    radius_km = 2.5
    radius_display_text = "지역 기준 추천"
    radius_result_desc = "추천 식당입니다!"
    if region.strip():
        st.caption("💡 건물명/역명을 입력하거나 '내 위치 찾기'를 누르면 탐색 반경(거리)을 직접 설정할 수 있습니다.")

region_warning_spot = st.empty()
st.write("---")

# 3. 탭 메뉴 영역
tab1, tab2 = st.tabs(["🎲 완전 랜덤 룰렛", "😊 기분 맞춤 룰렛"])

spin_triggered = False
selected_candidates = []

with tab1:
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    if st.button("🎲 주사위 굴리기", use_container_width=True, type="primary", key="btn_random"):
        if not region.strip():
            region_warning_spot.warning("⚠️ 기준 지역을 입력하거나 '내 위치 찾기'를 눌러주세요!")
        else:
            region_warning_spot.empty()
            with st.spinner(f"🔍 '{region}' ({radius_display_text}) 식당들을 확인하고 있습니다..."):
                selected_candidates = fetch_local_dynamic_menus(region, allow_porridge=False)
            spin_triggered = True

with tab2:
    selected_mood = None

    st.markdown("<h5 style='margin: 8px 0 6px 0; font-size: 15px;'>😊 오늘의 기분</h5>", unsafe_allow_html=True)
    col_m1, col_m2 = st.columns(2)
    mood_group = ["🥳 기분좋음", "🤯 스트레스", "🫠 입맛없음", "😴 피곤·보양"]
    with col_m1:
        for k in mood_group[:2]:
            info = MOOD_DATA[k]
            if st.button(f"{k}\n\n({info['desc']})", use_container_width=True, key=f"btn_{k}"):
                selected_mood = k
    with col_m2:
        for k in mood_group[2:]:
            info = MOOD_DATA[k]
            if st.button(f"{k}\n\n({info['desc']})", use_container_width=True, key=f"btn_{k}"):
                selected_mood = k

    st.markdown("<h5 style='margin: 18px 0 6px 0; font-size: 15px;'>⛅ 날씨 맞춤</h5>", unsafe_allow_html=True)
    col_w1, col_w2 = st.columns(2)
    weather_group = ["☀️ 날씨 좋음", "☔ 흐림·비"]
    with col_w1:
        k = weather_group[0]
        if st.button(f"{k}\n\n({MOOD_DATA[k]['desc']})", use_container_width=True, key=f"btn_{k}"):
            selected_mood = k
    with col_w2:
        k = weather_group[1]
        if st.button(f"{k}\n\n({MOOD_DATA[k]['desc']})", use_container_width=True, key=f"btn_{k}"):
            selected_mood = k

    st.markdown("<h5 style='margin: 18px 0 6px 0; font-size: 15px;'>🩹 속 편한 케어 & 해장</h5>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns(2)
    care_group = ["🤢 속 안 좋음", "😵‍💫 해장 시급"]
    with col_c1:
        k = care_group[0]
        if st.button(f"{k}\n\n({MOOD_DATA[k]['desc']})", use_container_width=True, key=f"btn_{k}"):
            selected_mood = k
    with col_c2:
        k = care_group[1]
        if st.button(f"{k}\n\n({MOOD_DATA[k]['desc']})", use_container_width=True, key=f"btn_{k}"):
            selected_mood = k

    if selected_mood:
        if not region.strip():
            region_warning_spot.warning("⚠ 기준 지역을 입력하거나 '내 위치 찾기'를 눌러주세요!")
        else:
            region_warning_spot.empty()
            with st.spinner(f"🔍 '{region}' ({radius_display_text}) [{selected_mood}] 메뉴 탐색 중..."):
                is_sick = (selected_mood == "🤢 속 안 좋음")
                all_local = fetch_local_dynamic_menus(region, allow_porridge=is_sick)
                keywords = MOOD_DATA[selected_mood]["keywords"]
                filtered = [f for f in all_local if any(kw in f[0] for kw in keywords)]
                selected_candidates = filtered if len(filtered) >= 4 else all_local
            spin_triggered = True

card_spot = st.empty()
detail_spot = st.empty()

# 4. 룰렛 실행 및 애니메이션
if spin_triggered and selected_candidates:
    st.session_state.spin_count += 1
    region_warning_spot.empty()
    detail_spot.empty()

    final_menu, final_emoji, places, c_lat, c_lng = get_verified_menu_and_places(
        region, selected_candidates, max_radius_km=radius_km, direct_coords=st.session_state.gps_coords
    )

    steps = 14
    for i in range(steps):
        temp_item = random.choice(selected_candidates)
        card_spot.markdown(
            f"""
            <div style="text-align: center; margin-top: 30px; margin-bottom: 30px; padding: 20px; 
                        background: #FFF9E6; border-radius: 20px; border: 4px solid #FF9800; 
                        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.2);">
                <div style="font-size: 70px; margin-bottom: 4px;">{temp_item[1]}</div>
                <h2 style="color: #FF5722; margin: 4px 0 6px 0; font-size: 26px;">{temp_item[0]}</h2>
                <p style="color: #999; font-size: 13px; margin: 0;">{radius_display_text} 기준 맛집 찾는 중... 🎲</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        time.sleep(0.03 + (i * 0.012))

    card_spot.markdown(
        f"""
        <div style="text-align: center; margin-top: 30px; margin-bottom: 30px; padding: 22px; 
                    background: #FFF9E6; border-radius: 20px; border: 4px solid #E65100; 
                    box-shadow: 0 4px 18px rgba(230, 81, 0, 0.25);">
            <div style="font-size: 75px; margin-bottom: 4px;">{final_emoji}</div>
            <h1 style="color: #E65100; margin: 4px 0 6px 0; font-size: 30px;">🎉 {final_menu} 당첨! 🎉</h1>
            <p style="color: #795548; font-size: 14px; font-weight: bold; margin: 0;">'{region}' {radius_result_desc}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.session_state.saved_result = {
        "menu": final_menu,
        "emoji": final_emoji,
        "places": places,
        "region": region,
        "radius_km": radius_km,
        "radius_text": radius_display_text,
        "radius_desc": radius_result_desc,
        "center_lat": c_lat,
        "center_lng": c_lng,
        "id": st.session_state.spin_count
    }

# 5. 결과 화면 표시 (지도 및 식당)
res = st.session_state.saved_result
if res is not None:
    result_desc = res.get("radius_desc", f"반경 {res.get('radius_km', 1.8)}km 내 추천 식당입니다!")
    card_spot.markdown(
        f"""
        <div style="text-align: center; margin-top: 30px; margin-bottom: 30px; padding: 22px; 
                    background: #FFF9E6; border-radius: 20px; border: 4px solid #E65100; 
                    box-shadow: 0 4px 18px rgba(230, 81, 0, 0.25);">
            <div style="font-size: 75px; margin-bottom: 4px;">{res['emoji']}</div>
            <h1 style="color: #E65100; margin: 4px 0 6px 0; font-size: 30px;">🎉 {res['menu']} 당첨! 🎉</h1>
            <p style="color: #795548; font-size: 14px; font-weight: bold; margin: 0;">'{res['region']}' {result_desc}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with detail_spot.container():
        places = res["places"]

        if places:
            st.markdown(
                f"""
                <div style="margin-bottom: 12px; padding: 12px 16px; 
                            background-color: #F1F8E9; border-left: 5px solid #2E7D32; border-radius: 6px;">
                    <span style="font-size: 15px; color: #2E7D32; font-weight: bold;">🏬 오늘의 추천 1픽 맛집: </span>
                    <span style="font-size: 16px; color: #1B5E20; font-weight: 800;">{places[0]['name']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            # 최대 9개 후보 매장 나열 (총합 최대 10개)
            if len(places) > 1:
                candidate_names = [f"<b>{i+1}.</b> {p['name']}" for i, p in enumerate(places[1:10])]
                st.markdown(
                    f"<div style='font-size: 13.5px; color: #444; line-height: 1.6; margin-bottom: 20px;'>"
                    f"<b>근처 다른 추천 후보 ({len(places)-1}곳):</b><br/>"
                    f"{' &nbsp;·&nbsp; '.join(candidate_names)}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            st.markdown("<h3 style='margin-bottom: 4px;'>🗺️ 추천 식당 위치 지도</h3>", unsafe_allow_html=True)
            st.caption("⭐ 빨간 핀: 오늘의 1픽 추천 식당 / 🔵 파란 핀: 주변 후보 식당 (최대 10개 표시)")
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            target_lat = places[0]["lat"]
            target_lng = places[0]["lng"]

            r_val = res.get("radius_km", 1.8)
            zoom_val = 16 if r_val <= 1.0 else (15 if r_val <= 2.5 else 14)

            m = folium.Map(location=[target_lat, target_lng], zoom_start=zoom_val, control_scale=True)

            main_popup_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                        padding: 6px 10px; min-width: 170px; text-align: center; white-space: nowrap;">
                <span style="background: #E65100; color: white; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                    ⭐ 오늘의 1픽
                </span>
                <div style="margin-top: 6px; font-size: 14px; font-weight: bold; color: #222;">
                    {places[0]['name']}
                </div>
            </div>
            """
            folium.Marker(
                location=[target_lat, target_lng],
                popup=folium.Popup(main_popup_html, max_width=300),
                tooltip=f"⭐ 추천: {places[0]['name']}",
                icon=folium.Icon(color="red", icon="star", prefix="fa")
            ).add_to(m)

            for idx, p in enumerate(places[1:10], start=2):
                sub_popup_html = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                            padding: 5px 8px; min-width: 150px; text-align: center; white-space: nowrap;">
                    <span style="background: #1976D2; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                        후보 {idx}
                    </span>
                    <div style="margin-top: 5px; font-size: 13px; font-weight: bold; color: #333;">
                        {p['name']}
                    </div>
                </div>
                """
                folium.Marker(
                    location=[p["lat"], p["lng"]],
                    popup=folium.Popup(sub_popup_html, max_width=260),
                    tooltip=f"{idx}. {p['name']}",
                    icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
                ).add_to(m)

            unique_map_key = f"map_view_{res['id']}_{int(target_lat * 10000)}_{int(target_lng * 10000)}"
            st_folium(
                m,
                width="100%",
                height=430,
                key=unique_map_key,
                returned_objects=[]
            )

        else:
            st.info("식당 정보를 불러오는 중입니다. 아래 링크에서 전체 매장을 바로 확인해 보세요!")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        col_link1, col_link2 = st.columns(2)
        with col_link1:
            naver_map_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(res['region'] + ' ' + res['menu'])}"
            st.link_button("🗺️ 네이버 지도에서 길찾기", naver_map_url, use_container_width=True)
        with col_link2:
            kakao_map_url = f"https://map.kakao.com/link/search/{urllib.parse.quote(res['region'] + ' ' + res['menu'])}"
            st.link_button("🗺️ 카카오 맵에서 길찾기", kakao_map_url, use_container_width=True)