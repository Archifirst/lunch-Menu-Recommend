def is_dinner_only_restaurant(place_name: str, address: str) -> bool:
    """
    웹 검색(다음/카카오 상세 및 웹 스니펫)을 통해
    오픈 시간이 14:00 이후(저녁/야간 전용)인 매장인지 실시간 판별.
    - 14:00 이후 오픈(15:00, 16:30, 17:00 등) 감지 시: True 반환 (탈락 대상)
    - 점심 오픈(11:00, 11:30 등)이거나 시간 정보 없을 시: False 반환 (통과)
    """
    clean_name = place_name.split()[0]
    region_chunk = " ".join(address.split()[:2]) if address else ""
    query = f"{region_chunk} {clean_name} 영업시간".strip()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    
    # 1. 다음 모바일 실시간 검색(통합검색 플레이스 블록 스크래핑)
    url = f"https://m.search.daum.net/search?w=tot&q={urllib.parse.quote(query)}"
    
    try:
        res = requests.get(url, headers=headers, timeout=0.8)
        if res.status_code == 200:
            text = res.text
            
            # 패턴 A: "16:30 ~ ", "17:00 ~ ", "16:30에 영업 시작" 등 24시간 형식 매칭
            time_matches = re.findall(r"(\d{1,2}):(\d{2})\s*(?:~|에|오픈|영업)", text)
            for h_str, m_str in time_matches:
                h = int(h_str)
                # 14시 이상 24시 이하 오픈인 경우 저녁/술집 매장으로 판정
                if 14 <= h <= 23:
                    return True
                # 점심 오픈(오전 9시 ~ 13시 사이) 시간대가 감지되면 안전한 점심 식당으로 통과
                if 9 <= h <= 13:
                    return False
            
            # 패턴 B: "오후 4시", "오후 5시", "오후 4:30" 등 한글 표기 매칭
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
