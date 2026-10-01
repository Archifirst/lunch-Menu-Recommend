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

# --- 술집 및 부적합 업종 차단용 키워드 (카테고리 & 상호명) ---
EXCLUDED_CATEGORIES = [
    "술집", "주점", "호프", "포차", "이자카야", "바(BAR)", "요리주점", "와인바",
    "칵테일바", "민속주점", "맥주", "룸살롱", "단란주점", "유흥주점", "라이브카페", "나이트클럽"
]

EXCLUDED_NAME_KEYWORDS = [
    "포차", "주점", "호프", "이자카야", "술집", "맥주", "와인", "펍", "PUB", "비어",
    "BEER", "라운지", "BAR", "룸", "노래방", "포장마차", "야시장", "소주"
]

# 메뉴 정의 및 카테고리 선별 힌트
DEFAULT_FOODS = [
    ("제육볶음", "🥓", "제육볶음", ["한식", "백반", "식당"]),
    ("김치찌개", "🥘", "김치찌개", ["찌개", "한식", "백반"]),
    ("순대국", "🍲", "순대국", ["순대", "국밥", "한식"]),
    ("뼈해장국", "🍖", "뼈해장국", ["감자탕", "해장국", "국밥"]),
    ("돈까스", "🍱", "돈까스", ["돈가스", "일식", "경양식", "양식"]),
    ("초밥", "🍣", "초밥", ["초밥", "스시", "일식"]),
    ("짜장면", "🥢", "중국집", ["중식", "중화요리", "중국집"]),
    ("짬뽕", "🌶️", "짬뽕", ["중식", "중화요리", "짬뽕"]),
    ("칼국수", "🍜", "칼국수", ["칼국수", "국수", "한식"]),
    ("파스타", "🍝", "파스타", ["양식", "이탈리안", "패밀리레스토랑"]),
    ("피자", "🍕", "피자", ["피자", "양식", "이탈리안"]),
    ("햄버거", "🍔", "수제버거", ["햄버거", "패스트푸드"]),
    ("쌀국수", "🍜", "쌀국수", ["아시아음식", "베트남음식", "쌀국수"]),
    ("떡볶이", "🌶", "떡볶이", ["분식", "떡볶이"]),
    ("닭갈비", "🥘", "닭갈비", ["닭갈비", "한식"]),
    ("백반", "🍱", "백반", ["백반", "가정식", "한식"])
]

MOOD_DATA = {
    "🥳 기분좋음": ("양식·특식", ["파스타", "피자", "햄버거", "초밥", "돈까스"]),
    "🤯 스트레스": ("매콤·화끈", ["짬뽕", "떡볶이", "제육볶음", "닭갈비"]),
    "😴 피곤·보양": ("든든한 한식", ["순대국", "뼈해장국", "백반", "김치찌개"]),
    "☔ 흐림·비": ("따끈한 국물", ["칼국수", "김치찌개", "순대국", "짬뽕"])
}

# --- 점심 식당 적합성 엄격 검증 함수 ---
def is_valid_lunch_restaurant(place_name: str, category_name: str, preferred_tags: list = None) -> bool:
    """술집, 주점, 펍 등을 완전 배제하고 점심 식당만 통과시킴"""
    # 1. 카카오 카테고리 경로에서 술집/주점 제외
    if any(ex in category_name for ex in EXCLUDED_CATEGORIES):
        return False

    # 2. 상호명에서 술집 키워드 제외
    clean_name = place_name.replace(" ", "").upper()
    if any(bad in clean_name for bad in [k.upper() for k in EXCLUDED_NAME_KEYWORDS]):
        return False

    # 3. 카페/디저트 제외 (빙수, 커피 전문점 등)
    if "카페" in category_name or "디저트" in category_name or "제과,베이커리" in category_name:
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


def kakao_search_places(lat: float, lng: float, keyword: str, radius_km: float = 1.8, category_tags: list = None):
    """
    반경 내 음식점 중 '술집/주점'을 완전 필터링하고 진짜 점심 밥집만 수집
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    radius_meters = int(radius_km * 1000)

    params = {
        "query": keyword,
        "category_group_code": "FD6", # 음식점 카테고리
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

                # 💡 핵심: 점심 식당 적합성 검증 (술집 완전 차단)
                if not is_valid_lunch_restaurant(p_name, cat_name, category_tags):
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
st.caption("술집·주점은 쏙 빼고, 점심 식사에 최적화된 진짜 맛집만 추천합니다.")
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
            region_warning_spot.warning("⚠️ 지역명을 입력하거나 '내 위치 찾기'를 눌러주세요!")
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

        with st.spinner("술집/호프집을 제외하고 순수 밥집만 선별 중입니다..."):
            for m_name, m_emoji, m_kw, m_tags in shuffled:
                # 1차: 키워드로 검색 (엄격한 점심 식당 필터 적용)
                found = kakao_search_places(c_lat, c_lng, m_kw, radius_km=radius_km, category_tags=m_tags)
                if found:
                    final_menu = (m_name, m_emoji)
                    places = found
                    break

            # 개별 메뉴에 밥집이 부족하면 한식/백반 등으로 안전하게 백업
            if not places:
                fallback_found = kakao_search_places(c_lat, c_lng, "백반", radius_km=radius_km)
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
                        <p style="color: #888; font-size: 13px; margin: 0;">{radius_display_text} 기준 맛집 찾는 중... 🎲</p>
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
            region_warning_spot.warning(f"⚠️ '{region}' 반경 내에 등록된 적합한 식당을 찾지 못했습니다. 탐색 반경을 넓혀보세요!")

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
                '{res['region']}' ({res['radius_text']}) 반경 추천 결과입니다!
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
                    <span style="font-size: 13px; color: #2E7D32; font-weight: bold;">⭐ 오늘의 1픽 추천 점심</span>
                    <span style="font-size: 12px; background: #C8E6C9; color: #1B5E20; padding: 2px 6px; border-radius: 4px;">
                        {top_pick.get('category', '일반음식점')}
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
                f"<b>{i+1}.</b> <a href='{p.get('place_url', '#')}' target='_blank' style='color:#333;text-decoration:none;'>{p['name']}</a> <span style='color:#888;font-size:12px;'>({p.get('category', '')}, {p['dist']}km)</span>"
                for i, p in enumerate(places[1:10])
            ]
            st.markdown(
                f"<div style='font-size: 13.5px; color: #444; line-height: 1.9; margin-bottom: 20px;'>"
                f"<b>근처 다른 추천 후보 ({len(places)-1}곳):</b><br/>"
                f"{'<br/>'.join(candidate_names)}"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("<h3 style='margin-bottom: 4px;'>🗺️️ 추천 식당 카카오맵 좌표 지도</h3>", unsafe_allow_html=True)
        st.caption("🔴 빨간 핀: 1픽 맛집 / 🔵 파란 핀: 주변 후보 (클릭 시 카카오 상세 페이지 링크)")

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
