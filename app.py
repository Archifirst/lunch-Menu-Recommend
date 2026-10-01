import streamlit as st
import random
import time
import requests
import urllib.parse
import folium
from streamlit_folium import st_folium

KAKAO_REST_KEY = "bb9c8bfabfc3d5a4c0dbdb3312d8ca30".strip()

st.set_page_config(page_title="오늘 점심 뭐 먹지?", page_icon="🍱", layout="centered")

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

# --- 2. 점심 부적합 업종 (숯불구이, 고깃집, 치킨집, 꼬치집 등) 제외 ---
NON_LUNCH_CATEGORIES = [
    "삼겹살", "갈비", "육류,고기구이", "곱창,막창", "양꼬치", "조개구이",
    "치킨", "닭요리 > 치킨", "닭꼬치", "꼬치구이"
]

NON_LUNCH_NAME_KEYWORDS = [
    "숯불", "연탄", "화로", "짚불", "구이", "삼겹살", "오겹살", "목살", "뒷고기", "생고기",
    "차돌", "대패", "정육식당", "갈비", "갈매기", "소고기", "한우", "곱창", "막창",
    "대창", "특양", "양꼬치", "양갈비", "조개구이", "장어구이",
    "꼬치", "닭꼬치", "수제꼬치", "야키토리", "쿠시카츠",
    "치킨", "통닭", "닭강정", "켄터키", "BHC", "BBQ", "교촌", "굽네", "처갓집", "노랑통닭"
]

# --- 3. 종합 다메뉴 프랜차이즈 (국수나무, 미소야, 김밥천국 등) ---
# 돈까스, 찌개, 파스타, 짬뽕 등의 전문 요리가 당첨되었을 때 차단하고 '분식'에서만 허용
MULTI_MENU_FRANCHISES = [
    "국수나무", "미소야", "역전우동", "한솥", "도시락",
    "김밥천국", "고봉민", "김가네", "얌샘", "싸다김밥", "종로김밥", 
    "선비꼬마김밥", "마녀김밥", "바르다김선생", "밥버거", "토마토김밥",
    "분식천국", "나드리김밥", "소풍김밥"
]

# 위 다메뉴 프랜차이즈가 허용되는 메뉴군
BUNSIK_ALLOW_MENUS = {"김밥", "떡볶이", "라면", "분식"}

# --- 4. 메뉴 목록 ---
DEFAULT_FOODS = [
    ("제육볶음", "🥓", "제육볶음 정식", ["한식", "백반", "식당"]),
    ("김치찌개", "🥘", "김치찌개 전문점", ["찌개", "한식", "백반"]),
    ("순대국", "🍲", "순대국 전문점", ["순대", "국밥", "한식"]),
    ("뼈해장국", "🍖", "뼈해장국", ["감자탕", "해장국", "국밥"]),
    ("돈까스", "🍱", "돈까스 전문점", ["돈가스", "일식", "경양식", "양식"]),
    ("초밥", "🍣", "초밥 전문점", ["초밥", "스시", "일식"]),
    ("짜장면", "🥢", "중국집", ["중식", "중화요리", "중국집"]),
    ("짬뽕", "🌶️", "짬뽕 전문점", ["중식", "중화요리", "짬뽕"]),
    ("칼국수", "🍜", "칼국수 전문점", ["칼국수", "국수", "한식"]),
    ("파스타", "🍝", "파스타 레스토랑", ["양식", "이탈리안", "패밀리레스토랑"]),
    ("피자", "🍕", "화덕피자", ["피자", "양식", "이탈리안"]),
    ("햄버거", "🍔", "수제버거", ["햄버거", "패스트푸드"]),
    ("쌀국수", "🍜", "베트남 쌀국수", ["아시아음식", "베트남음식", "쌀국수"]),
    ("떡볶이", "🌶", "떡볶이 맛집", ["분식", "떡볶이"]),
    ("김밥", "🍙", "김밥 맛집", ["분식", "김밥"]),
    ("닭갈비", "🥘", "닭갈비 전문점", ["닭갈비", "한식"]),
    ("백반", "🍱", "백반 가정식", ["백반", "가정식", "한식", "기사식당"])
]

MOOD_DATA = {
    "🥳 기분좋음": ("양식·특식 전문", ["파스타", "피자", "햄버거", "초밥", "돈까스"]),
    "🤯 스트레스": ("화끈·전문 매콤", ["짬뽕", "떡볶이", "제육볶음", "닭갈비"]),
    "😴 피곤·보양": ("든든한 뚝배기", ["순대국", "뼈해장국", "백반", "김치찌개"]),
    "☔ 흐림·비": ("따끈한 전문 국물", ["칼국수", "김치찌개", "순대국", "짬뽕"])
}

# --- 점심 전문 식당 판정 엔진 ---
def is_valid_specialized_restaurant(menu_name: str, place_name: str, category_name: str) -> bool:
    clean_name = place_name.replace(" ", "").upper()

    # [1] 술집 및 유흥주점 제외
    if any(ex in category_name for ex in EXCLUDED_CATEGORIES):
        return False
    if any(bad in clean_name for bad in [k.upper() for k in EXCLUDED_NAME_KEYWORDS]):
        return False

    # [2] 카페/디저트 제외
    if any(c in category_name for c in ["카페", "디저트", "제과,베이커리"]):
        return False

    # [3] 고깃집, 구이집, 치킨, 꼬치 제외
    if any(non in category_name for non in NON_LUNCH_CATEGORIES):
        return False
    if any(bad in clean_name for bad in [k.upper() for k in NON_LUNCH_NAME_KEYWORDS]):
        return False

    # [4] 종합 다메뉴 프랜차이즈(국수나무, 미소야, 김밥천국 등) 필터링
    # 김밥, 떡볶이, 라면 등 분식 메뉴가 아닐 때는 무조건 배제
    if menu_name not in BUNSIK_ALLOW_MENUS:
        if any(brand in clean_name for brand in MULTI_MENU_FRANCHISES):
            return False
        # 카카오 카테고리가 '분식' 단독인 곳에서 돈까스/파스타/찌개 등 전문 요리 검색 시 제외
        if "분식" in category_name and not any(k in category_name for k in ["일식", "양식", "한식", "중식"]):
            return False

    return True


# --- 카카오 공식 API 연동 함수 ---

def kakao_get_coordinates(query: str):
    """지명/건물명 중심 좌표 획득"""
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
    """좌표를 행정동 이름으로 변환"""
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
    """
    반경 내 음식점 중 술집, 고깃집, 치킨집, 다메뉴 프랜차이즈(국수나무 등)를 제외한 단품 전문점 수집
    """
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
                p_name = d.get("place_name", "")
                cat_name = d.get("category_name", "")

                # 다메뉴 프랜차이즈 및 점심 부적합 업종 검증
                if not is_valid_specialized_restaurant(menu_name, p_name, cat_name):
                    continue

                dist_m = float(d.get("distance", 0))
                places.append({
                    "name": p_name,
                    "category": cat_name.split(">")[-1].strip() if ">" in cat_name else cat_name,
                    "lat": float(d.get("y")),
                    "lng": float(d.get("x")),
                    "dist": round(dist_m / 1000, 2) if dist_m > 0 else 0.1,
                    "address": d.get("road_address_name") or d.get("address_name", ""),
                    "place_url": d.get("place_url", "")
                })
            return places
    except Exception:
        pass
    return []


# 브라우저 GPS 수신 처리
qp = st.query_params
if "action" in qp and qp["action"] == "gps" and "lat" in qp and "lng" in qp:
    try:
        lat_f = float(qp["lat"])
        lng_f = float(qp["lng"])
        if st.session_state.gps_coords != (lat_f, lng_f):
            st.session_state.gps_coords = (lat_f, lng_f)
            detected_name = kakao_reverse_geocode(lat_f, lng_f)
            st.session_state.region_input_val = detected_name
            st.toast(f"현재 위치: '{detected_name}' 감지 완료!", icon="✅")
    except Exception:
        pass
    del st.query_params["action"]
    del st.query_params["lat"]
    del st.query_params["lng"]


# --- 화면 레이아웃 ---
st.title("🍱 오늘 점심 뭐 먹지?")
st.caption("국수나무·김밥천국 같은 다메뉴 매장은 제외하고, 해당 요리 '전문점'만 엄선합니다.")
st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# 1. 위치 입력창 & GPS 버튼
col_input, col_gps = st.columns([3.3, 1.2])

with col_input:
    region = st.text_input(
        "📍 기준 지역, 동 이름 또는 건물명",
        value=st.session_state.region_input_val,
        placeholder="예시) 후평동, 역삼역, 판교유스페이스",
        key="main_region_input"
    )
    if region != st.session_state.region_input_val:
        st.session_state.gps_coords = None

with col_gps:
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; justify-content:flex-end; height:100%;">
            <div style="height:25px;"></div>
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
            " style="width:100%; height:42px; background-color:#2E7D32; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">
                내 위치 찾기
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

# 2. 반경 선택
st.markdown("<h5 style='margin: 12px 0 6px 0; font-size: 15px;'>📏 카카오 탐색 반경</h5>", unsafe_allow_html=True)
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
    manual_radius = st.number_input("희망 반경 (단위: km)", min_value=0.2, max_value=10.0, value=2.0, step=0.2)
    radius_km = float(manual_radius)
    radius_display_text = f"직접 입력 {radius_km:.1f}km"
else:
    radius_km = PRESET_RADIUS[selected_preset]
    name_map = {"🚶": "도보 700m", "🚲": "자전거 1.8km", "🚗": "차량 3.5km"}
    radius_display_text = name_map[selected_preset]

region_warning_spot = st.empty()
st.write("---")

# 3. 룰렛 탭
tab1, tab2 = st.tabs(["🎲 완전 랜덤 룰렛", "😊 기분 맞춤 룰렛"])

spin_triggered = False
selected_candidates = []

with tab1:
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    if st.button("🎲 주사위 굴리기", use_container_width=True, type="primary", key="btn_random"):
        if not region.strip() and not st.session_state.gps_coords:
            region_warning_spot.warning("⚠️ 지역명을 입력하거나 '내 위치 찾기'를 눌러주세요!")
        else:
            region_warning_spot.empty()
            selected_candidates = DEFAULT_FOODS.copy()
            spin_triggered = True

with tab2:
    selected_mood = None
    st.markdown("<h5 style='margin: 8px 0 6px 0; font-size: 15px;'>😊 오늘의 기분/상황</h5>", unsafe_allow_html=True)
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        for k in ["🥳 기분좋음", "😴 피곤·보양"]:
            desc, _ = MOOD_DATA[k]
            if st.button(f"{k}\n\n({desc})", use_container_width=True, key=f"btn_{k}"):
                selected_mood = k
    with col_m2:
        for k in ["🤯 스트레스", "☔ 흐림·비"]:
            desc, _ = MOOD_DATA[k]
            if st.button(f"{k}\n\n({desc})", use_container_width=True, key=f"btn_{k}"):
                selected_mood = k

    if selected_mood:
        if not region.strip() and not st.session_state.gps_coords:
            region_warning_spot.warning("⚠️️ 지역명을 입력하거나 '내 위치 찾기'를 눌러주세요!")
        else:
            region_warning_spot.empty()
            _, allowed_names = MOOD_DATA[selected_mood]
            filtered = [f for f in DEFAULT_FOODS if f[0] in allowed_names]
            selected_candidates = filtered if filtered else DEFAULT_FOODS
            spin_triggered = True

card_spot = st.empty()
detail_spot = st.empty()

# 4. 탐색 및 추첨 실행
if spin_triggered and selected_candidates:
    detail_spot.empty()

    if st.session_state.gps_coords:
        c_lat, c_lng = st.session_state.gps_coords
    else:
        with st.spinner(f"카카오맵에서 '{region}' 위치를 확인하고 있습니다..."):
            c_lat, c_lng = kakao_get_coordinates(region)

    if not c_lat:
        region_warning_spot.error(f"⚠️ '{region}' 위치를 찾지 못했습니다. 구체적인 지명이나 동 이름을 입력해 보세요.")
    else:
        final_menu = None
        places = []

        shuffled = selected_candidates.copy()
        random.shuffle(shuffled)

        with st.spinner("국수나무·김밥천국을 제외하고 전문 식당을 찾는 중입니다..."):
            for m_name, m_emoji, m_kw, m_tags in shuffled:
                found = kakao_search_places(c_lat, c_lng, m_name, m_kw, radius_km=radius_km)
                if found:
                    final_menu = (m_name, m_emoji)
                    places = found
                    break

            if not places:
                fallback_found = kakao_search_places(c_lat, c_lng, "백반", "백반 가정식", radius_km=radius_km)
                if fallback_found:
                    final_menu = ("백반·가정식", "🍱")
                    places = fallback_found

        if final_menu and places:
            for i in range(6):
                temp = random.choice(selected_candidates)
                card_spot.markdown(
                    f"""
                    <div style="text-align: center; margin: 25px 0; padding: 20px; 
                                background: #FFF9E6; border-radius: 20px; border: 4px solid #FF9800;">
                        <div style="font-size: 65px; margin-bottom: 4px;">{temp[1]}</div>
                        <h2 style="color: #FF5722; margin: 4px 0 6px 0; font-size: 24px;">{temp[0]}</h2>
                        <p style="color: #888; font-size: 13px; margin: 0;">{radius_display_text} 기준 전문점 찾는 중... 🎲</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                time.sleep(0.04 + (i * 0.015))

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
            region_warning_spot.warning(f"⚠️ '{region}' 반경 내에 등록된 전문 식당을 찾지 못했습니다. 탐색 반경을 넓혀보세요!")

# 5. 결과 화면 출력
res = st.session_state.saved_result
if res is not None and res.get("places"):
    card_spot.markdown(
        f"""
        <div style="text-align: center; margin: 25px 0; padding: 22px; 
                    background: #FFF9E6; border-radius: 20px; border: 4px solid #E65100; 
                    box-shadow: 0 4px 18px rgba(230, 81, 0, 0.25);">
            <div style="font-size: 75px; margin-bottom: 4px;">{res['emoji']}</div>
            <h1 style="color: #E65100; margin: 4px 0 6px 0; font-size: 30px;">🎉 {res['menu']} 당첨! 🎉</h1>
            <p style="color: #795548; font-size: 14px; font-weight: bold; margin: 0;">
                '{res['region']}' ({res['radius_text']}) 반경 전문 식당 추천 결과입니다!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with detail_spot.container():
        places = res["places"]
        top_pick = places[0]

        st.markdown(
            f"""
            <div style="margin-bottom: 15px; padding: 14px 18px; 
                        background-color: #F1F8E9; border-left: 5px solid #2E7D32; border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: #2E7D32; font-weight: bold;">⭐ 오늘의 1픽 단품 전문점</span>
                    <span style="font-size: 12px; background: #C8E6C9; color: #1B5E20; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
                        {top_pick.get('category', '전문음식점')}
                    </span>
                </div>
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
                f"<b>{i+1}.</b> <a href='{p.get('place_url', '#')}' target='_blank' style='color:#333;text-decoration:none;'>{p['name']}</a> <span style='color:#666;font-size:12px;'>({p.get('category', '')}, {p['dist']}km)</span>"
                for i, p in enumerate(places[1:10])
            ]
            st.markdown(
                f"<div style='font-size: 13.5px; color: #444; line-height: 1.9; margin-bottom: 20px;'>"
                f"<b>근처 다른 전문 후보 ({len(places)-1}곳):</b><br/>"
                f"{'<br/>'.join(candidate_names)}"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("<h3 style='margin-bottom: 4px;'>🗺 추천 식당 카카오맵 위치 지도</h3>", unsafe_allow_html=True)
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
                icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
            ).add_to(m)

        unique_map_key = f"map_{res['id']}_{int(top_pick['lat'] * 10000)}"
        st_folium(m, width="100%", height=420, key=unique_map_key, returned_objects=[])

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        kakao_map_url = f"https://map.kakao.com/link/search/{urllib.parse.quote(res['region'] + ' ' + res['menu'])}"
        st.link_button("🟡 카카오맵 길찾기 바로가기", kakao_map_url, use_container_width=True)
