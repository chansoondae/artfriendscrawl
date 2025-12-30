import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# OpenAI API 키 설정
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def openai_summarize_with_month(body, comments_text):
    """
    OpenAI GPT-4o-mini를 사용하여 여행 게시글 내용을 요약하고 여행 월 추출
    """
    # 프롬프트 생성
    prompt = f"""다음 스위스 여행 게시글의 본문과 댓글을 읽고:
1) 핵심 내용을 3-4개의 짧은 포인트로 정리
2) 여행한 월을 추출 (JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC)

본문:
{body[:1500]}

댓글 (일부):
{comments_text[:800]}

요구사항:
<요약>
- 3-4개의 핵심 포인트로 정리 (필수)
- 각 포인트는 체언 종결 (명사로 끝나기, 마침표 없음)
- 각 포인트는 "- "로 시작 (마크다운 리스트 형식)
- 최대 50자 이내로 간결하게
- 여행 핵심 정보: 방문 장소, 주요 활동, 팁/추천사항, 비용/예산 등
- 구체적인 숫자와 명칭 포함 (예: "융프라우 3일권", "그린델발트 5박")
- "~입니다", "~됩니다" 같은 종결어미 사용 금지
- 인사말이나 감사 인사 절대 제외

<여행 월>
- 본문에서 여행한 달을 찾아 JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC 중 하나로 반환
- "6월", "June", "6개월" 등에서 추출
- 확실하지 않거나 찾을 수 없으면 NONE 반환
- 오직 하나의 월만 반환 (여러 개면 주요 여행 월)

응답 형식 (JSON):
{{
  "summary": "- 첫 번째 포인트\\n- 두 번째 포인트\\n- 세 번째 포인트",
  "travel_month": "JUN"
}}

예시:
{{
  "summary": "- 6월 스위스 렌트카+하프페어 조합으로 부모님과 8박9일 여행\\n- 그린델발트 5박 베이스로 융프라우, 쉴트호른, 마테호른 방문\\n- 60대 이상 부모님 여행지로 최고 만족도, 물가는 매우 비쌈",
  "travel_month": "JUN"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 스위스 여행 분석 전문가입니다. 여행 핵심 내용을 3-4개의 짧은 bullet point로 요약하고, 여행한 월을 추출합니다. 응답은 반드시 JSON 형식으로만 제공합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        summary = result.get('summary', '')
        travel_month = result.get('travel_month', 'NONE')

        # travel_month 유효성 검사
        valid_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                       'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'NONE']
        if travel_month not in valid_months:
            travel_month = 'NONE'

        return summary, travel_month

    except Exception as e:
        print(f"    ⚠️ API 오류: {e}")
        # 오류 시 fallback
        sentences = body[:200].split('.')[:3]
        summary = '. '.join(sentences) + "."
        return summary, 'NONE'

input_file = "swissfriends_all_merged.jsonl"
output_file = "swissfriends_all_summarized.jsonl"

# 전체 처리
test_mode = False
test_count = 5
skip_lines = 7637  # post_id 59797은 7638번째 라인

print(f"{input_file} 파일을 OpenAI GPT-4o-mini로 여행 핵심 포인트 정리 + 여행 월 추출합니다...")
print(f"⚠️ 라인 {skip_lines + 1}번째 (post_id 59797)부터 시작합니다.")
print(f"⚠️ 숙소/맛집/타국가 카테고리는 제외하고 처리합니다.\n")

success_count = 0
error_count = 0
total_cost_estimate = 0

# 월별 통계
month_stats = {}

with open(output_file, 'a', encoding='utf-8') as out_f:
    with open(input_file, 'r', encoding='utf-8') as in_f:
        for line_num, line in enumerate(in_f, 1):
            # 이미 처리된 라인 건너뛰기
            if line_num <= skip_lines:
                continue

            if test_mode and line_num > (skip_lines + test_count):
                break

            try:
                # JSON 파싱
                article = json.loads(line.strip())

                # 제외할 카테고리 체크
                exclude_categories = [
                    '🏨스위스 숙소 후기',
                    '🍽️스위스 맛집 후기',
                    '🇫🇷프랑스 France',
                    '🇮🇹이탈리아 Italia',
                    '🇩🇪독일 Germany',
                    '🇦🇹오스트리아 Austria',
                    '🇪🇸스페인 Spain',
                    '🇨🇿체코 Czech',
                    '🇬🇧영국 UK'
                ]

                category = article.get('category', '')
                if category in exclude_categories:
                    print(f"[{line_num}] {article.get('title', '')[:40]}... ⏭️ 카테고리 제외: {category}")
                    continue

                # post_contents와 comments_merged 추출
                body = article.get('post_contents', '')
                comments_text = article.get('comments_merged', '')

                print(f"[{line_num}] {article['title'][:40]}...")

                # OpenAI로 요약 + 월 추출
                summary, travel_month = openai_summarize_with_month(body, comments_text)

                # 비용 추정 (대략적)
                # gpt-4o-mini: $0.150 / 1M input tokens, $0.600 / 1M output tokens
                total_cost_estimate += 0.00007

                # 월별 통계 업데이트
                month_stats[travel_month] = month_stats.get(travel_month, 0) + 1

                # 새로운 객체 생성 (post_contents, comments_merged 제외)
                summarized_article = {
                    'category': article.get('category', ''),
                    'title': article.get('title', ''),
                    'author': article.get('author', ''),
                    'date': article.get('date', ''),
                    'view_count': article.get('view_count', ''),
                    'comments': article.get('comments', ''),
                    'url': article.get('url', ''),
                    'post_id': article.get('post_id', ''),
                    'travel_month': travel_month,
                    'summary': summary
                }

                # JSONL 형식으로 저장
                out_f.write(json.dumps(summarized_article, ensure_ascii=False) + '\n')

                success_count += 1
                print(f"  ✓ 여행 월: {travel_month}")
                print(f"  ✓ 요약:\n{summary}\n")

            except Exception as e:
                print(f"  ✗ 라인 {line_num} 오류: {e}\n")
                error_count += 1
                continue

print(f"\n✓ OpenAI 여행 게시글 요약 + 월 추출 완료!")
print(f"  - 입력 파일: {input_file}")
print(f"  - 출력 파일: {output_file}")
print(f"  - 성공: {success_count}개")
print(f"  - 실패: {error_count}개")
print(f"  - 예상 비용: ${total_cost_estimate:.4f}")

print(f"\n📊 월별 통계:")
for month in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'NONE']:
    count = month_stats.get(month, 0)
    if count > 0:
        print(f"  {month}: {count}개")

print(f"\n※ post_contents와 comments_merged 필드는 제거되었습니다.")
print(f"※ 각 게시글은 3-4개의 핵심 포인트로 요약되고 travel_month가 추가되었습니다.")
