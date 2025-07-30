import re
import json
from google import genai


def analyze_moat(company_name: str, date_kr_ymd: str) -> str:
    prompt = f"""
당신은 기업 분석에 능숙한 전문 주식 애널리스트입니다. 반드시 한국어로 답변하십시오.

{date_kr_ymd} 기준 "{company_name}"의 정보를 검색한 뒤 그 내용을 바탕으로 해당 기업의 **중장기 핵심 경쟁 우위(Moat)** 를 분석해 주세요.

### 출력 형식은 아래와 같이 JSON 객체로 제공해 주세요:
{{ "moat_analysis": "여기에 간결한 경쟁 우위 요약 문장을 2~3줄 이내로 작성하세요.", "moat_score": 숫자 }}
    
반드시 위의 JSON 형식과 기준을 따르세요.
"""
    return prompt.strip()


def parse_moat_response(response_text: str) -> dict:
    result = {"moat_analysis": response_text.strip(), "moat_score": None}
    try:
        match = re.search(r"\{.*?\}", response_text, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            result["moat_analysis"] = parsed.get(
                "moat_analysis", result["moat_analysis"]
            ).strip()
            result["moat_score"] = (
                int(parsed.get("moat_score"))
                if parsed.get("moat_score") is not None
                else None
            )
            return result
    except Exception:
        pass
    lower_text = response_text.lower()
    # ...fallback logic...
    if any(
        kw in lower_text
        for kw in ["절대적 독점", "완전한 독점", "대체 불가", "진입 불가", "특허 보호"]
    ):
        result["moat_score"] = 10
    elif any(
        kw in lower_text
        for kw in ["지속적 독점", "지속적인 독점", "강력한 진입 장벽", "규제 보호"]
    ):
        result["moat_score"] = 9
    elif any(
        kw in lower_text
        for kw in ["뚜렷한 경쟁 우위", "브랜드 파워", "규모의 경제", "전환 비용"]
    ):
        result["moat_score"] = 8
    elif any(
        kw in lower_text
        for kw in ["강한 경쟁력", "기술력", "유통망", "경쟁사 대비 우위"]
    ):
        result["moat_score"] = 7
    elif any(
        kw in lower_text for kw in ["상당한 경쟁 우위", "우위 요소 존재", "대체 가능성"]
    ):
        result["moat_score"] = 6
    elif any(
        kw in lower_text for kw in ["평균 이상의 경쟁력", "차별화 미약", "유지 불확실"]
    ):
        result["moat_score"] = 5
    elif any(
        kw in lower_text for kw in ["부분적 경쟁력", "일시적 수익성", "대체재 존재"]
    ):
        result["moat_score"] = 4
    elif any(
        kw in lower_text for kw in ["경쟁 우위 낮음", "차별화 거의 없음", "방어력 낮음"]
    ):
        result["moat_score"] = 3
    elif any(
        kw in lower_text for kw in ["미미한 경쟁 우위", "단기 유행", "구조적 우위 없음"]
    ):
        result["moat_score"] = 2
    elif any(
        kw in lower_text
        for kw in [
            "경쟁 우위 없음",
            "진입 장벽 없음",
            "브랜드 없음",
            "기술력 없음",
            "commoditized",
        ]
    ):
        result["moat_score"] = 1
    elif any(
        kw in lower_text for kw in ["commodity", "완전한 commodity", "완전 경쟁 시장"]
    ):
        result["moat_score"] = 0
    else:
        result["moat_score"] = -1
    return result


def query_gemini(prompt: str) -> str:
    response = genai.Client(api_key=None).models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text
