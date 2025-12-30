import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# OpenAI API 키 설정
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def openai_summarize(body, comments_text):
    """
    OpenAI GPT-4o-mini를 사용하여 여행 게시글 내용을 2-3개 핵심 포인트로 정리
    """
    # 프롬프트 생성
    prompt = f"""다음 스위스 여행 게시글의 본문과 댓글을 읽고 핵심 내용을 3-4개의 짧은 포인트로 정리해주세요.

본문:
{body[:1500]}

댓글 (일부):
{comments_text[:800]}

요구사항:
- 3-4개의 핵심 포인트로 정리 (필수)
- 각 포인트는 체언 종결 (명사로 끝나기, 마침표 없음)
- 각 포인트는 "- "로 시작 (마크다운 리스트 형식)
- 최대 50자 이내로 간결하게
- 여행 핵심 정보: 방문 장소, 주요 활동, 팁/추천사항, 비용/예산 등
- 구체적인 숫자와 명칭 포함 (예: "융프라우 3일권", "그린델발트 5박")
- "~입니다", "~됩니다" 같은 종결어미 사용 금지
- 인사말이나 감사 인사 절대 제외

예시:
- 6월 스위스 렌트카+하프페어 조합으로 부모님과 8박9일 여행
- 그린델발트 5박 베이스로 융프라우, 쉴트호른, 마테호른 방문
- 60대 이상 부모님 여행지로 최고 만족도, 물가는 매우 비쌈

핵심 포인트:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 스위스 여행 분석 전문가입니다. 여행 핵심 내용만 3-4개의 짧은 bullet point로 정리합니다. 각 포인트는 체언 종결(명사로 끝남)하며 마침표 없이 작성합니다. '~입니다', '~됩니다' 같은 종결어미 사용 금지. 최대 50자 이내. 구체적 숫자와 팩트 위주. 여행지, 주요 활동, 실용 팁, 예산 정보 포함."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        print(f"    ⚠️ API 오류: {e}")
        # 오류 시 fallback
        sentences = body[:200].split('.')[:3]
        return '. '.join(sentences) + "."

input_file = "swissfriends_all_merged.jsonl"
output_file = "swissfriends_all_summarized.jsonl"

# 전체 처리
test_mode = False
test_count = 0

print(f"{input_file} 파일을 OpenAI GPT-4o-mini로 여행 핵심 포인트 정리합니다...")
if test_mode:
    print(f"⚠️ 테스트 모드: 처음 {test_count}개만 처리합니다.\n")
else:
    print(f"전체 게시글을 처리합니다.\n")

success_count = 0
error_count = 0
total_cost_estimate = 0

with open(output_file, 'w', encoding='utf-8') as out_f:
    with open(input_file, 'r', encoding='utf-8') as in_f:
        for line_num, line in enumerate(in_f, 1):
            if test_mode and line_num > test_count:
                break

            try:
                # JSON 파싱
                article = json.loads(line.strip())

                # post_contents와 comments_merged 추출
                body = article.get('post_contents', '')
                comments_text = article.get('comments_merged', '')

                print(f"[{line_num}] {article['title'][:40]}...")

                # OpenAI로 요약 (2-3개 핵심 포인트)
                summary = openai_summarize(body, comments_text)

                # 비용 추정 (대략적)
                # gpt-4o-mini: $0.150 / 1M input tokens, $0.600 / 1M output tokens
                # 평균 1000자 입력 + 200자 출력 = 약 400 tokens
                # 100개 처리 시 약 40,000 tokens = $0.006 정도
                total_cost_estimate += 0.00006

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
                    'summary': summary
                }

                # JSONL 형식으로 저장
                out_f.write(json.dumps(summarized_article, ensure_ascii=False) + '\n')

                success_count += 1
                print(f"  ✓ 요약:\n{summary}\n")

            except Exception as e:
                print(f"  ✗ 라인 {line_num} 오류: {e}\n")
                error_count += 1
                continue

print(f"\n✓ OpenAI 여행 게시글 요약 완료!")
print(f"  - 입력 파일: {input_file}")
print(f"  - 출력 파일: {output_file}")
print(f"  - 성공: {success_count}개")
print(f"  - 실패: {error_count}개")
print(f"  - 예상 비용: ${total_cost_estimate:.4f}")
print(f"\n※ post_contents와 comments_merged 필드는 제거되었습니다.")
print(f"※ 각 게시글은 3-4개의 핵심 포인트로 요약되었습니다.")
