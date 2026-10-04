from concurrent.futures import ThreadPoolExecutor

def check_is_real_lunch_restaurant(place_id: str) -> bool:
    """카카오 상세 페이지에서 영업시간을 분석해 점심 장사를 안 하는 술집을 철저히 배제"""
    if not place_id:
        return True
    
    url = f"https://place.map.kakao.com/main/v/{place_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://map.kakao.com/"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=1.2)
        if res.status_code != 200:
            return True  # 조회 실패 시 일단 보류
        
        data = res.json()
        basic_info = data.get("basicInfo", {})
        open_hour = basic_info.get("openHour", {})
        period_list = open_hour.get("periodList", [])
        
        # 1. 영업시간 정보가 아예 없는 경우 통과
        if not period_list:
            return True
            
        has_lunch_slot = False
        is_night_only = False
        
        for period in period_list:
            for t in period.get("timeList", []):
                time_se = t.get("timeSE", "")
                times = re.findall(r"(\d{1,2}):(\d{2})", time_se)
                if len(times) >= 2:
                    start_h = int(times[0][0]) + int(times[0][1]) / 60.0
                    end_h = int(times[1][0]) + int(times[1][1]) / 60.0
                    
                    # 새벽 마감 처리 (예: 16:30 ~ 04:30)
                    if end_h < start_h:
                        end_h += 24.0
                    
                    # 핵심 조건 1: 오픈 시간이 14:30 이후면 100% 저녁/술집 매장이므로 즉시 탈락!
                    if start_h >= 14.5:
                        is_night_only = True
                        break
                    
                    # 핵심 조건 2: 점심 황금 시간대(11:30 ~ 13:30) 사이에 온전히 영업 중이어야 함
                    if start_h <= 12.5 and end_h >= 13.0:
                        has_lunch_slot = True
            
            if is_night_only:
                return False
                
        # 영업시간이 등록되어 있는데 점심 슬롯이 전혀 없으면 탈락
        if not has_lunch_slot:
            return False
            
        return True
    except Exception:
        return True
