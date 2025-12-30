import time
import os
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY를 .env 파일에 설정해주세요.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Selenium 설정
service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# Naver login
print("네이버 로그인 페이지를 엽니다. 20초 내에 로그인해주세요...")
driver.get('https://www.naver.com/')
time.sleep(20)  # 로그인 대기 시간

# 브라우저가 닫혔는지 확인
try:
    _ = driver.current_window_handle
except:
    print("브라우저가 닫혔습니다. 스크립트를 종료합니다.")
    exit(1)

print("카페로 이동합니다...")
driver.get('https://cafe.naver.com/f-e/cafes/25274813/menus/0')
time.sleep(5)

# CSV 파일에서 URL 읽기
csv_file = "art_contents_all.csv"

# CSV 파일에서 URL 읽기
urls_to_crawl = []
test_mode = False  # 테스트 모드
test_limit = 2     # 테스트할 개수

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

# 이미 저장된 post_id 확인 (재시작 기능)
print("이미 저장된 데이터를 확인합니다...")
try:
    # 모든 저장된 ID를 가져오기 (페이징 처리)
    all_existing_ids = set()
    page_size = 1000
    offset = 0

    while True:
        response = supabase.table('art_post_contents').select('id').range(offset, offset + page_size - 1).execute()
        if not response.data:
            break
        all_existing_ids.update(row['id'] for row in response.data)
        if len(response.data) < page_size:
            break
        offset += page_size

    existing_ids = all_existing_ids
    print(f"  - 이미 저장된 게시글: {len(existing_ids)}개")

    # 아직 저장되지 않은 URL만 필터링
    urls_to_crawl = [url for url in urls_to_crawl
                     if int(re.search(r'/(\d+)$', url['url']).group(1)) not in existing_ids]
    print(f"  - 크롤링할 게시글: {len(urls_to_crawl)}개\n")
except Exception as e:
    print(f"  - 기존 데이터 확인 실패: {e}")
    print(f"  - 전체 크롤링을 진행합니다.\n")

# save main_window
main_window = driver.current_window_handle

success_count = 0
error_count = 0
contents_saved = 0
comments_saved = 0
skipped_count = 0

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
            print(f"  ✗ iframe을 찾을 수 없습니다.")
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
        post_id = int(post_id_match.group(1))

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

        # 본문 Supabase에 저장 (upsert 사용)
        try:
            content_data = {
                'id': post_id,
                'title': title,
                'content': body
            }
            supabase.table('art_post_contents').upsert(content_data, on_conflict='id').execute()
            contents_saved += 1
        except Exception as e:
            print(f"  ✗ 본문 저장 실패: {e}")

        # 댓글 크롤링
        comment_areas = content.select("div.comment_area")
        comments_data = []

        for comment_idx, comment_area in enumerate(comment_areas, 1):
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
                    'post_id': post_id,
                    'post_author': post_author,
                    'comment_author': comment_author,
                    'comment_text': comment_text,
                    'comment_date': comment_date,
                    'comment_order': comment_idx
                })

        # 댓글 Supabase에 저장 (배치 insert)
        if comments_data:
            try:
                supabase.table('art_post_comments').insert(comments_data).execute()
                comments_saved += len(comments_data)
            except Exception as e:
                print(f"  ✗ 댓글 저장 실패: {e}")

        print(f"  ✓ 완료: post_id={post_id}, 댓글={len(comments_data)}개")
        success_count += 1

        driver.close()
        driver.switch_to.window(original_window)

        # 진행 상황 출력 (100개마다)
        if idx % 100 == 0:
            print(f"\n진행 상황: {idx}/{len(urls_to_crawl)} ({success_count}개 성공, {error_count}개 실패)")
            print(f"  - 본문: {contents_saved}개, 댓글: {comments_saved}개\n")

    except Exception as e:
        print(f"  ✗ 에러 발생: {e}")
        error_count += 1
        try:
            driver.close()
            driver.switch_to.window(original_window)
        except:
            pass
        continue

try:
    driver.close()
except:
    pass

try:
    driver.quit()
except:
    pass

print("\n" + "=" * 60)
print(f"크롤링 완료!")
print(f"  - 성공: {success_count}개")
print(f"  - 실패: {error_count}개")
print(f"  - 본문 저장: {contents_saved}개")
print(f"  - 댓글 저장: {comments_saved}개")
print(f"  - 테이블: art_post_contents, art_post_comments")
print("=" * 60)
