# SPDX-FileCopyrightText: © 2025 Hyungsuk Choi <chs_3411@naver[dot]com>, University of Maryland 
# SPDX-License-Identifier: MIT

import re
import json

def parse_moat_response(response_text: str) -> dict:
    """
    LLM 응답에서 moat_analysis와 moat_score를 안전하게 추출합니다.
    JSON이 혼합되어 있거나 형식이 불완전할 경우에도 처리합니다.
    """
    # 기본값
    result = {
        "moat_analysis": response_text.strip(),
        "moat_score": None
    }

    # JSON 형식 추출 시도
    try:
        # 중괄호로 된 JSON 블럭 추출
        match = re.search(r'\{.*?\}', response_text, re.DOTALL)
        if match:
            json_block = match.group(0)
            parsed = json.loads(json_block)
            result["moat_analysis"] = parsed.get("moat_analysis", result["moat_analysis"]).strip()
            result["moat_score"] = int(parsed.get("moat_score")) if parsed.get("moat_score") is not None else None
            return result
    except (json.JSONDecodeError, ValueError, TypeError):
        pass  # continue to fallback logic

    # fallback 점수 추정 로직 (텍스트 기반 추론)
    lower_text = response_text.lower()
    if "매우 강력" in lower_text or "독점" in lower_text or "지속적" in lower_text:
        result["moat_score"] = 5
    elif "뚜렷한 경쟁 우위" in lower_text or "브랜드" in lower_text or "진입 장벽" in lower_text:
        result["moat_score"] = 4
    elif "일정 수준" in lower_text or "경쟁력 있으나" in lower_text:
        result["moat_score"] = 3
    elif "쉽게 대체" in lower_text or "약함" in lower_text:
        result["moat_score"] = 1
    elif "없음" in lower_text or "commoditized" in lower_text:
        result["moat_score"] = 0

    return result

resp = '삼성전자는 메모리 반도체 시장에서 높은 점유율과 규모의 경제를 기반으로 뚜렷한 경쟁 우위를 보유하고 있습니다. { \"moat_analysis\": \"규모의 경제와 브랜드 인지도를 기반으로 경쟁 우위를 확보하고 있습니다.\", \"moat_score\": 4 }'
parsed = parse_moat_response(resp)
print(parsed)