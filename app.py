# --- 2. 반경 노출 및 즉각 반응형 선택기 ---
clean_region = region.strip()
is_admin_region = False

if clean_region:
    # 역, 출구, 거리, 센터 등 명확한 장소는 반경 노출
    is_spot = bool(re.search(r"(역|출구|거리|센터|스퀘어|타워|빌딩|공원|마트|백화점)$", clean_region))
    # 순수 행정단위(시, 군, 구, 읍, 면, 동 및 행정명 '가') 판별
    is_pure_admin = bool(re.search(r"([시군구읍면동]|\b\w+[0-9]*가)$", clean_region))
    if is_pure_admin and not is_spot:
        is_admin_region = True

should_show_radius = bool(clean_region and not is_admin_region)

if should_show_radius:
    st.markdown("<div class='radius-wrapper'>", unsafe_allow_html=True)
    st.markdown("<div style='margin: 10px 0 6px 0; font-size: 13.5px; font-weight: 600; color: #4A4036;'>📏 탐색 반경</div>", unsafe_allow_html=True)
    
    # 4개 버튼을 가로 컬럼 배치
    c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.0, 1.2], vertical_alignment="center")

    current_preset = st.session_state.selected_radius_preset

    with c1:
        if st.button("🚶 도보 700m", key="rbtn_walk", type="primary" if current_preset == "🚶" else "secondary", use_container_width=True):
            if st.session_state.selected_radius_preset != "🚶":
                st.session_state.selected_radius_preset = "🚶"
                st.rerun()

    with c2:
        if st.button("🚲 자전거 1.8km", key="rbtn_bike", type="primary" if current_preset == "🚲" else "secondary", use_container_width=True):
            if st.session_state.selected_radius_preset != "🚲":
                st.session_state.selected_radius_preset = "🚲"
                st.rerun()

    with c3:
        if st.button("🚗 차량 3.5km", key="rbtn_car", type="primary" if current_preset == "🚗" else "secondary", use_container_width=True):
            if st.session_state.selected_radius_preset != "🚗":
                st.session_state.selected_radius_preset = "🚗"
                st.rerun()

    with c4:
        if st.button("직접 입력", key="rbtn_custom", type="primary" if current_preset == "직접 입력" else "secondary", use_container_width=True):
            if st.session_state.selected_radius_preset != "직접 입력":
                st.session_state.selected_radius_preset = "직접 입력"
                st.rerun()

    # 선택값에 따른 반경 km 및 텍스트 결정
    if st.session_state.selected_radius_preset == "직접 입력":
        manual_radius = st.number_input(
            "희망 반경 (단위: km)", 
            min_value=0.2, 
            max_value=10.0, 
            value=2.0, 
            step=0.2,
            key="custom_radius_num"
        )
        radius_km = float(manual_radius)
        radius_display_text = f"직접 입력 {radius_km:.1f}km"
    else:
        radius_km = PRESET_RADIUS[st.session_state.selected_radius_preset]
        name_map = {"🚶": "도보 700m", "🚲": "자전거 1.8km", "🚗": "차량 3.5km"}
        radius_display_text = name_map[st.session_state.selected_radius_preset]

    st.markdown("</div>", unsafe_allow_html=True)
else:
    radius_km = 1.8
    radius_display_text = "지역 인근"
