import streamlit as st
import random
import time
import requests
import re
import math
import urllib.parse
import folium
from streamlit_folium import st_folium

# 카카오 REST API 키 설정
KAKAO_REST_KEY = "bb9c8bfabfc3d5a4c0dbdb3312d8ca30"

st.set_page_config(page_title="오늘 점심 뭐 먹지?", page_icon="🍱", layout="centered")

# 세션 상태 초기화
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

# 거리 정의
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
    if not clean_text or clean_text in MAJOR_ADMIN_NAMES:
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


# UI 커스텀 스타일
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
    ("떡볶이", "🌶️"), ("라면", "🍜"), ("칼국수", "🍜"), ("수제비", "🥣"),
    ("돈까스", "🍱"), ("초밥", "🍣"), ("일본라멘", "🍜"), ("우동", "🍜"),
    ("쌀국수", "🍜"), ("카레라이스", "🍛"), ("햄버거", "🍔"), ("피자", "🍕"),
    ("파스타", "🍝"), ("샌드위치", "🥪"), ("샐러드", "🥗"), ("짜장면", "🥢"),
    ("짬뽕", "🌶️"), ("마라탕", "🌶️"), ("냉면", "🧊"), ("막국수", "🍜")
]

SICK_EXTRA_FOODS = [
    ("전복죽", "🦪"), ("소고기야채죽", "🥣"), ("순두부찌개", "🥘"),
    ("콩나물국밥", "🍲"), ("잔치국수", "🍜"), ("미역국", "🥣"), ("설렁탕", "🥣")
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
        "keywords": ["냉면", "막국수", "초밥", "샐러드", "소바", "비빔밥", "포케"]
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

# --- 카카오 공식 API 연동 함수군 ---

def reverse_geocode_gps(lat: float, lng: float) -> str:
    """좌표(WGS84)를 법정동/행정동 이름으로 변환"""
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {"x": str(lng), "y": str(lat)}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=3.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            for doc in docs:
                if doc.get("region_type") == "H":  # 행정동 우선
                    return f"{doc.get('region_2depth_name', '')} {doc.get('region_3depth_name', '')}".strip()
            if docs:
                return docs[0].get("address_name", "내 위치")
    except Exception:
        pass
    return "내 위치"


def geocode_region_center(region_query: str):
    """입력받은 키워드/지역명의 중심 좌표(위도, 경도)를 반환"""
    clean_q = region_query.strip()
    if not clean_q:
        return None, None
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {"query": clean_q, "size": 1}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=3.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                return float(docs[0]["y"]), float(docs[0]["x"])
    except Exception:
        pass
    return None, None


def fetch_kakao_places(keyword: str, center_lat: float, center_lng: float, radius_km: float = 1.8):
    """반경 내 음식점(카테고리: FD6)을 카카오 API로 검색"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {
        "query": keyword,
        "category_group_code": "FD6",  # 음식점만 필터링
        "x": str(center_lng),
        "y": str(center_lat),
        "radius": min(int(radius_km * 1000), 20000),
        "sort": "accuracy",
        "size": 15
    }
    results = []
    try:
        res = requests.get(url, headers=headers, params=params, timeout=3.0)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            for doc in docs:
                raw_name = doc.get("place_name", "")
                if any(bad in raw_name for bad in ["주점", "호프", "포차", "이자카야", "술집"]):
                    continue
                dist_m = float(doc.get("distance", 0))
                results.append({
                    "name": raw_name,
                    "lat": float(doc["y"]),
                    "lng": float(doc["x"]),
                    "dist": round(dist_m / 1000, 2) if dist_m > 0 else 0.0,
                    "address": doc.get("road_address_name") or doc.get("address_name", ""),
                    "place_url": doc.get("place_url", "")
                })
    except Exception:
        pass
    return results


def get_verified_menu_and_places(region: str, candidates: list, max_radius_km: float = 1.8, direct_coords=None):
    """후보 메뉴 중 실제 반경 내에 존재하는 식당 목록과 함께 매칭"""
    if direct_coords and direct_coords[0]:
        c_lat, c_lng = direct_coords[0], direct_coords[1]
    else:
        c_lat, c_lng = geocode_region_center(region)

    if not c_lat:
        return candidates[0][0], candidates[0][1], [], None, None

    shuffled = candidates.copy()
    random.shuffle(shuffled)

    # 후보군 탐색
    for menu_name, emoji in shuffled[:6]:
        places = fetch_kakao_places(menu_name, c_lat, c_lng, radius_km=max_radius_km)
        if places and len(places) >= 2:
            return menu_name, emoji, places[:10], c_lat, c_lng

    # 보증된 대중 메뉴 폴백
    fallback_foods = [("김치찌개", "🥘"), ("순대국", "🍲"), ("돈까스", "🍱"), ("짜장면", "🥢"), ("백반", "🍱")]
    for f_menu, f_emoji in fallback_foods:
        places = fetch_kakao_places(f_menu, c_lat, c_lng, radius_km=max_radius_km + 0.5)
        if places:
            return f_menu, f_emoji, places[:10], c_lat, c_lng

    return shuffled[0][0], shuffled[0][1], [], c_lat, c_lng


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
st.caption("카카오맵 공식 API를 통해 실시간 근처 맛집을 추천합니다.")
st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# 1. 위치 입력창 & GPS 버튼
col_input, col_gps = st.columns([3.3, 1.2])

with col_input:
    region = st.text_input(
        "📍 기준 지역 또는 건물명",
        value=st.session_state.region_input_val,
        placeholder="예시) 코엑스, 롯데월드타워, 역삼역, 판교역",
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

# 2. 반경 설정
if radius_active:
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("<h5 style='margin-bottom: 8px; font-size: 15px;'>📏 탐색 반경</h5>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.0, 1.6], vertical_alignment="center")

    with c1:
        btn_type = "primary" if st.session_state.selected_radius_preset == "🚶" else "secondary"
        if st.button("🚶 700m", key="rbtn_walk", type=btn_type, use_container_width=True):
            st.session_state.selected_radius_preset = "🚶"
            st.rerun()

    with c2:
        btn_type = "primary" if st.session_state.selected_radius_preset == "🚲" else "secondary"
        if st.button("🚲 1.8km", key="rbtn_bike", type=btn_type, use_container_width=True):
            st.session_state.selected_radius_preset = "🚲"
            st.rerun()

    with c3:
        btn_type = "primary" if st.session_state.selected_radius_preset == "🚗" else "secondary"
        if st.button("🚗 3.5km", key="rbtn_car", type=btn_type, use_container_width=True):
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
    else:
        radius_km = PRESET_RADIUS[selected_preset]
        name_map = {"🚶": "도보 700m", "🚲": "자전거 1.8km", "🚗": "차량 3.5km"}
        radius_display_text = name_map[selected_preset]

else:
    radius_km = 2.0
    radius_display_text = "기본 반경 2.0km"
    if region.strip():
        st.caption("💡 특정 건물/역명을 입력하거나 '내 위치 찾기'를 사용하시면 탐색 반경(거리)을 직접 설정할 수 있습니다.")

region_warning_spot = st.empty()
st.write("---")

# 3. 메뉴 추첨 탭
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
            selected_candidates = DEFAULT_FOODS.copy()
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

    st.markdown("<h5 style='margin: 18px 0 6px 0; font-size: 15px;'>⛅ 날씨 & 속편한 케어</h5>", unsafe_allow_html=True)
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        for k in ["☀️ 날씨 좋음", "🤢 속 안 좋음"]:
            if st.button(f"{k}\n\n({MOOD_DATA[k]['desc']})", use_container_width=True, key=f"btn_{k}"):
                selected_mood = k
    with col_w2:
        for k in ["☔ 흐림·비", "😵‍💫 해장 시급"]:
            if st.button(f"{k}\n\n({MOOD_DATA[k]['desc']})", use_container_width=True, key=f"btn_{k}"):
                selected_mood = k

    if selected_mood:
        if not region.strip():
            region_warning_spot.warning("⚠️ 기준 지역을 입력하거나 '내 위치 찾기'를 눌러주세요!")
        else:
            region_warning_spot.empty()
            is_sick = (selected_mood == "🤢 속 안 좋음")
            pool = DEFAULT_FOODS.copy() + (SICK_EXTRA_FOODS if is_sick else [])
            keywords = MOOD_DATA[selected_mood]["keywords"]
            filtered = [f for f in pool if any(kw in f[0] for kw in keywords)]
            selected_candidates = filtered if filtered else pool
            spin_triggered = True

card_spot = st.empty()
detail_spot = st.empty()

# 4. 애니메이션 및 실행
if spin_triggered and selected_candidates:
    st.session_state.spin_count += 1
    region_warning_spot.empty()
    detail_spot.empty()

    with st.spinner("카카오맵에서 최적의 매장을 찾는 중..."):
        final_menu, final_emoji, places, c_lat, c_lng = get_verified_menu_and_places(
            region, selected_candidates, max_radius_km=radius_km, direct_coords=st.session_state.gps_coords
        )

    # 룰렛 애니메이션
    for i in range(10):
        temp_item = random.choice(selected_candidates)
        card_spot.markdown(
            f"""
            <div style="text-align: center; margin: 25px 0; padding: 20px; 
                        background: #FFF9E6; border-radius: 20px; border: 4px solid #FF9800; 
                        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.2);">
                <div style="font-size: 65px; margin-bottom: 4px;">{temp_item[1]}</div>
                <h2 style="color: #FF5722; margin: 4px 0 6px 0; font-size: 24px;">{temp_item[0]}</h2>
                <p style="color: #888; font-size: 13px; margin: 0;">{radius_display_text} 기준 맛집 스캔 중... 🎲</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        time.sleep(0.04 + (i * 0.015))

    st.session_state.saved_result = {
        "menu": final_menu,
        "emoji": final_emoji,
        "places": places,
        "region": region,
        "radius_km": radius_km,
        "radius_text": radius_display_text,
        "center_lat": c_lat,
        "center_lng": c_lng,
        "id": st.session_state.spin_count
    }

# 5. 결과 및 지도 표시
res = st.session_state.saved_result
if res is not None:
    card_spot.markdown(
        f"""
        <div style="text-align: center; margin: 25px 0; padding: 22px; 
                    background: #FFF9E6; border-radius: 20px; border: 4px solid #E65100; 
                    box-shadow: 0 4px 18px rgba(230, 81, 0, 0.25);">
            <div style="font-size: 75px; margin-bottom: 4px;">{res['emoji']}</div>
            <h1 style="color: #E65100; margin: 4px 0 6px 0; font-size: 30px;">🎉 {res['menu']} 당첨! 🎉</h1>
            <p style="color: #795548; font-size: 14px; font-weight: bold; margin: 0;">
                '{res['region']}' ({res['radius_text']}) 반경 내 추천 식당입니다!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with detail_spot.container():
        places = res["places"]

        if places:
            top_pick = places[0]
            st.markdown(
                f"""
                <div style="margin-bottom: 15px; padding: 14px 18px; 
                            background-color: #F1F8E9; border-left: 5px solid #2E7D32; border-radius: 6px;">
                    <div style="font-size: 14px; color: #2E7D32; font-weight: bold;">⭐ 오늘의 1픽 추천 맛집</div>
                    <div style="font-size: 18px; color: #1B5E20; font-weight: 800; margin-top: 4px;">
                        <a href="{top_pick.get('place_url', '#')}" target="_blank" style="text-decoration: none; color: #1B5E20;">
                            {top_pick['name']} 🔗
                        </a>
                    </div>
                    <div style="font-size: 13px; color: #555; margin-top: 4px;">
                        📍 {top_pick['address']} (약 {top_pick['dist']}km)
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if len(places) > 1:
                candidate_names = [
                    f"<b>{i+1}.</b> <a href='{p.get('place_url', '#')}' target='_blank' style='color:#333;text-decoration:none;'>{p['name']}</a> ({p['dist']}km)"
                    for i, p in enumerate(places[1:10])
                ]
                st.markdown(
                    f"<div style='font-size: 13.5px; color: #444; line-height: 1.8; margin-bottom: 20px;'>"
                    f"<b>근처 다른 추천 후보 ({len(places)-1}곳):</b><br/>"
                    f"{' &nbsp;·&nbsp; '.join(candidate_names)}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            st.markdown("<h3 style='margin-bottom: 4px;'>🗺️ 추천 식당 카카오 위치 지도</h3>", unsafe_allow_html=True)
            st.caption("🔴 빨간 핀: 1픽 맛집 / 🔵 파란 핀: 주변 후보 맛집 (클릭 시 상세 팝업)")

            m = folium.Map(location=[top_pick["lat"], top_pick["lng"]], zoom_start=15, control_scale=True)

            # 1픽 마커
            folium.Marker(
                location=[top_pick["lat"], top_pick["lng"]],
                popup=folium.Popup(
                    f"<b>⭐ {top_pick['name']}</b><br>{top_pick['address']}<br>"
                    f"<a href='{top_pick.get('place_url', '#')}' target='_blank'>카카오맵 정보 보기</a>",
                    max_width=250
                ),
                tooltip=f"⭐ 1픽: {top_pick['name']}",
                icon=folium.Icon(color="red", icon="star", prefix="fa")
            ).add_to(m)

            # 나머지 후보 마커
            for idx, p in enumerate(places[1:10], start=2):
                folium.Marker(
                    location=[p["lat"], p["lng"]],
                    popup=folium.Popup(
                        f"<b>{idx}. {p['name']}</b><br>{p['address']}<br>"
                        f"<a href='{p.get('place_url', '#')}' target='_blank'>카카오맵 정보 보기</a>",
                        max_width=250
                    ),
                    tooltip=f"{idx}. {p['name']}",
                    icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
                ).add_to(m)

            unique_map_key = f"kakao_map_{res['id']}_{int(top_pick['lat'] * 10000)}"
            st_folium(m, width="100%", height=420, key=unique_map_key, returned_objects=[])

        else:
            st.warning("⚠️ 지정된 반경 내에서 해당 메뉴를 취급하는 식당을 찾지 못했습니다. 반경을 넓혀보세요!")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        col_link1, col_link2 = st.columns(2)
        with col_link1:
            kakao_map_url = f"https://map.kakao.com/link/search/{urllib.parse.quote(res['region'] + ' ' + res['menu'])}"
            st.link_button("🟡 카카오맵에서 길찾기", kakao_map_url, use_container_width=True)
        with col_link2:
            naver_map_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(res['region'] + ' ' + res['menu'])}"
            st.link_button("🟢 네이버 지도에서 길찾기", naver_map_url, use_container_width=True)
