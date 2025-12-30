import time
import os
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)


# Naver login
driver.get('https://www.naver.com/')
time.sleep(20)  # 로그인 대기 시간
driver.get('https://cafe.naver.com/f-e/cafes/25274813/menus/0')
time.sleep(5)

# CSV 파일에서 URL 읽기
csv_file = "art_contents_all.csv"

# 출력 디렉토리 생성
contents_dir = "art_posts_contents"
comments_dir = "art_posts_comments"
if not os.path.exists(contents_dir):
    os.makedirs(contents_dir)
if not os.path.exists(comments_dir):
    os.makedirs(comments_dir)

# 본문 CSV 파일 준비
contents_csv = open(os.path.join(contents_dir, "posts_contents.csv"), 'w', newline='', encoding='utf-8-sig')
contents_writer = csv.writer(contents_csv)
contents_writer.writerow(['post_id', 'title', 'content'])

# 댓글 CSV 파일 준비
comments_csv = open(os.path.join(comments_dir, "posts_comments.csv"), 'w', newline='', encoding='utf-8-sig')
comments_writer = csv.writer(comments_csv)
comments_writer.writerow(['post_id', 'post_author', 'comment_author', 'comment_text', 'comment_date'])

# CSV 파일에서 URL 읽기
urls_to_crawl = []
test_mode = True  # 테스트 모드
test_limit = 2    # 테스트할 개수

with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        urls_to_crawl.append({
            'url': row['url'],
            'author': row['author'],
            'title': row['title']
        })
        if test_mode and len(urls_to_crawl) >= test_limit:
            break

print(f"{'[테스트 모드] ' if test_mode else ''}총 {len(urls_to_crawl)}개의 URL을 크롤링합니다.\n")

# save main_window
main_window = driver.current_window_handle

success_count = 0
error_count = 0

for idx, post_info in enumerate(urls_to_crawl, 1):
    targetUrl = post_info['url']
    post_author = post_info['author']
    original_title = post_info['title']

    try:
        print(f"[{idx}/{len(urls_to_crawl)}] {targetUrl}")

        original_window = driver.current_window_handle
        # open new blank tab
        driver.switch_to.new_window('tab')
        driver.get(targetUrl)
        time.sleep(5)

        # iframe으로 전환
        try:
            driver.switch_to.frame("cafe_main")
        except:
            print("  ✗ iframe을 찾을 수 없습니다.")
            driver.close()
            driver.switch_to.window(original_window)
            error_count += 1
            continue

        r = driver.page_source
        content = BeautifulSoup(r, "html.parser")

        # 제목
        title_elem = content.select("h3.title_text")
        if not title_elem:
            print(f"  ✗ 제목을 찾을 수 없습니다.")
            driver.close()
            driver.switch_to.window(original_window)
            error_count += 1
            continue
        title = title_elem[0].text.strip()

        # URL에서 post_id 추출
        post_id_match = re.search(r'/(\d+)$', targetUrl)
        if not post_id_match:
            print(f"  ✗ URL에서 post_id를 추출할 수 없습니다.")
            driver.close()
            driver.switch_to.window(original_window)
            error_count += 1
            continue
        post_id = post_id_match.group(1)

        # 본문 내용
        body_elem = content.select("div.se-main-container")
        if not body_elem:
            body_elem = content.select("div#articleBody")
        if not body_elem:
            body_elem = content.select("div.se-component")

        body = ""
        if body_elem:
            body = body_elem[0].get_text(strip=False, separator="\n")
            body = re.sub(r'\n\s*\n\s*\n+', '\n\n', body)
            body = '\n'.join(line.rstrip() for line in body.split('\n'))
            body = body.strip()
        else:
            body = ""

        # 본문 CSV에 저장
        contents_writer.writerow([post_id, title, body])

        # 댓글 크롤링
        comment_areas = content.select("div.comment_area")
        comments_data = []

        for comment_area in comment_areas:
            # 댓글 작성자
            comment_author_elem = comment_area.select_one("a.comment_nickname")
            if not comment_author_elem:
                comment_author_elem = comment_area.select_one("button.comment_nickname")
            comment_author = comment_author_elem.text.strip() if comment_author_elem else "익명"

            # 댓글 내용
            comment_text_elem = comment_area.select_one("span.text_comment")
            comment_text = comment_text_elem.text.strip() if comment_text_elem else ""

            # 댓글 날짜
            comment_date_elem = comment_area.select_one("span.comment_info_date")
            comment_date = comment_date_elem.text.strip() if comment_date_elem else ""

            if comment_text:
                comments_data.append({
                    'author': comment_author,
                    'text': comment_text,
                    'date': comment_date
                })

        # 댓글 CSV에 저장
        for comment in comments_data:
            comments_writer.writerow([
                post_id,
                post_author,
                comment['author'],
                comment['text'],
                comment['date']
            ])

        print(f"  ✓ 완료: post_id={post_id}, 댓글={len(comments_data)}개")
        success_count += 1

        driver.close()
        driver.switch_to.window(original_window)

        # 진행 상황 출력 (100개마다)
        if idx % 100 == 0:
            print(f"\n진행 상황: {idx}/{len(urls_to_crawl)} ({success_count}개 성공, {error_count}개 실패)\n")

    except Exception as e:
        print(f"  ✗ 에러 발생: {e}")
        error_count += 1
        try:
            driver.close()
            driver.switch_to.window(original_window)
        except:
            pass
        continue

# 파일 닫기
contents_csv.close()
comments_csv.close()

driver.close()
driver.quit()

print("\n" + "=" * 60)
print(f"크롤링 완료!")
print(f"  - 성공: {success_count}개")
print(f"  - 실패: {error_count}개")
print(f"  - 본문: {contents_dir}/posts_contents.csv")
print(f"  - 댓글: {comments_dir}/posts_comments.csv")
print("=" * 60)
