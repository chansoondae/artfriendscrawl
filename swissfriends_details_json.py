import time
import os
import re
import csv
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup


service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)


# Naver login
driver.get('https://www.naver.com/')
# driver.get('https://nid.naver.com/nidlogin.login?mode=form&url=https%3A%2F%2Fwww.naver.com')
time.sleep(20)

# CSV 파일 읽기
csv_input = "swissfriends_all_revised.csv"
jsonl_output = "swissfriends_all_detailed.jsonl"

print(f"{csv_input} 파일에서 URL을 읽어서 상세 정보를 수집합니다...")

# CSV 읽기
articles = []
skip_count = 359  # 이미 처리된 개수
with open(csv_input, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    for idx, row in enumerate(reader, 1):
        if idx <= skip_count:
            continue
        articles.append(row)

test_count = len(articles)  # 전체 처리
print(f"총 {len(articles)}개의 게시글을 처리합니다. ({skip_count}개 건너뜀)\n")

# JSONL 파일 열기 (append mode로 기존 데이터에 추가)
jsonl_file = open(jsonl_output, 'a', encoding='utf-8')

success_count = 0
error_count = 0

for idx, article in enumerate(articles[:test_count], 1):
    url = article['url']

    try:
        print(f"[{idx}/{test_count}] {url} 크롤링 중...")

        # 새 탭에서 열기
        driver.switch_to.new_window('tab')
        driver.get(url)
        time.sleep(5)

        # iframe으로 전환
        driver.switch_to.frame("cafe_main")

        # 페이지 소스 파싱
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # 제목
        title_elem = soup.select_one("h3.title_text")
        title = title_elem.text.strip() if title_elem else article.get('title', '')

        # 작성자
        author_elem = soup.select_one("button.nickname")
        if not author_elem:
            author_elem = soup.select_one("a.nickname")
        author = author_elem.text.strip() if author_elem else article.get('author', '')

        # 날짜
        date_elem = soup.select_one("span.date")
        date = date_elem.text.strip() if date_elem else article.get('date', '')

        # 조회수
        view_elem = soup.select_one("span.count")
        view_count = view_elem.text.strip() if view_elem else article.get('view_count', '')

        # 좋아요 갯수
        likes_elem = soup.select_one("em.u_cnt._count")
        likes = likes_elem.text.strip() if likes_elem else "0"

        # 카테고리 (수정된 방식)
        category_elem = soup.select_one("a.link_board")
        category = category_elem.text.strip() if category_elem else "카테고리 없음"
        # 화살표 제거
        category = re.sub(r'\s*›\s*$', '', category).strip()

        # 본문 내용 (text만)
        body_elem = soup.select_one("div.se-main-container")
        if not body_elem:
            body_elem = soup.select_one("div#articleBody")
        if not body_elem:
            body_elem = soup.select_one("div.se-component")

        body = ""
        if body_elem:
            body = body_elem.get_text(strip=False, separator="\n")
            # 과도한 공백 제거
            body = re.sub(r'\n\s*\n\s*\n+', '\n\n', body)
            body = '\n'.join(line.rstrip() for line in body.split('\n'))
            body = body.strip()
        else:
            body = "본문 없음"

        # 댓글 수집 (구조화된 형태로)
        comments_list = []
        comment_areas = soup.select("div.comment_area")

        for comment_area in comment_areas:
            # 댓글 작성자
            comment_author_elem = comment_area.select_one("a.comment_nickname")
            if not comment_author_elem:
                comment_author_elem = comment_area.select_one("button.comment_nickname")
            comment_author = comment_author_elem.text.strip() if comment_author_elem else "익명"

            # 댓글 내용
            comment_text_elem = comment_area.select_one("span.text_comment")
            comment_text = comment_text_elem.text.strip() if comment_text_elem else ""

            if comment_text:
                comments_list.append({
                    "author": comment_author,
                    "text": comment_text
                })

        # JSON 객체 생성 (CSV 기존 값 활용)
        detail_info = {
            'category': article.get('category', category),
            'title': article.get('title', title),
            'author': article.get('author', author),
            'date': article.get('date', date),
            'view_count': article.get('view_count', view_count),
            'likes': likes,
            'total_comments': article.get('comments', str(len(comments_list))),
            'url': url,
            'body': body,
            'commentslist': comments_list
        }

        # JSONL 파일에 한 줄씩 저장
        jsonl_file.write(json.dumps(detail_info, ensure_ascii=False) + '\n')
        jsonl_file.flush()  # 즉시 디스크에 기록
        success_count += 1

        print(f"  ✓ 제목: {title[:40]}...")
        print(f"  - 카테고리: {category}")
        print(f"  - 작성자: {author}")
        print(f"  - 날짜: {date}")
        print(f"  - 조회수: {view_count}")
        print(f"  - 좋아요: {likes}")
        print(f"  - 댓글수: {len(comments_list)}")
        print(f"  - 본문 길이: {len(body)}자\n")

        # 탭 닫기
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        print(f"  ✗ 오류 발생: {e}\n")
        error_count += 1
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        continue

# 파일 닫기
jsonl_file.close()

print(f"\n✓ 저장 완료: {jsonl_output}")
print(f"  - 성공: {success_count}개")
print(f"  - 실패: {error_count}개")

driver.quit()
print("크롤링 완료!")
