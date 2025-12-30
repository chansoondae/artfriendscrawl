import time
import os
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)


# Naver login
driver.get('https://www.naver.com/')
# driver.get('https://nid.naver.com/nidlogin.login?mode=form&url=https%3A%2F%2Fwww.naver.com')
time.sleep(20) 
# access Naver cafe
driver.get('https://cafe.naver.com/f-e/cafes/25274813/menus/0?viewType=L')
time.sleep(5)

numOfPages = 21

# Create directory for CSV files
output_dir = "artbus_pages"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

targetUrl = "https://cafe.naver.com/f-e/cafes/25274813/menus/0?viewType=L&ta=ARTICLE_COMMENT&page=1&q=%EC%95%84%ED%8A%B8%EB%B2%84%EC%8A%A4&size=50"
# save main_window
main_window = driver.current_window_handle

# iframe 찾아서 전환
iframes = driver.find_elements(By.TAG_NAME, "iframe")
if len(iframes) > 0:
    driver.switch_to.frame(iframes[0])
    time.sleep(2)
else:
    print("경고: iframe을 찾을 수 없습니다.")

for page in range(1, numOfPages + 1):
    try:
        # 페이지별 CSV 파일 준비
        csv_filename = os.path.join(output_dir, f"artbus_page_{page:04d}.csv")
        csv_file = open(csv_filename, 'w', newline='', encoding='utf-8-sig')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['article_number', 'title', 'author', 'date', 'view_count', 'comments', 'url'])

        page_url = f"https://cafe.naver.com/f-e/cafes/25274813/menus/0?viewType=L&ta=ARTICLE_COMMENT&page={page}&q=%EC%95%84%ED%8A%B8%EB%B2%84%EC%8A%A4&size=50"
        print(f'\n[페이지 {page}/{numOfPages}] 크롤링 중...')

        driver.execute_script(f"window.location.href = '{page_url}';")
        time.sleep(10)  # 페이지 로딩 대기 시간 증가

        # 게시글 리스트가 로드될 때까지 대기
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.article, div.article-board"))
            )
            print("  게시글 로딩 완료")
        except:
            print("  경고: 게시글 요소를 찾지 못했습니다")

        # BeautifulSoup으로 HTML 파싱
        r = driver.page_source
        content = BeautifulSoup(r, "html.parser")

        # 디버그: 첫 페이지 HTML 저장
        if page == 1:
            with open("debug_page1.html", "w", encoding="utf-8") as f:
                f.write(r)
            driver.save_screenshot("debug_screenshot.png")
            print("  디버그: HTML과 스크린샷 저장 완료")

        # 테이블의 모든 행 찾기
        rows = content.select("tr")
        print(f'  발견된 행(tr) 수: {len(rows)}')

        post_count = 0
        for row in rows:
            try:
                # 글 번호 추출
                article_num_elem = row.select_one("td.td_normal")
                if not article_num_elem:
                    continue

                article_number = article_num_elem.text.strip()
                if not article_number.isdigit():
                    continue

                # 제목 및 URL 추출
                article_elem = row.select_one("a.article")
                if not article_elem:
                    continue

                title = article_elem.text.strip()
                article_href = article_elem.get('href', '')

                # URL 생성
                url = f"https://cafe.naver.com/amateurmagician/{article_number}"

                # 작성자 추출
                author_elem = row.select_one("span.nickname")
                author = author_elem.text.strip() if author_elem else ""

                # 날짜 추출 - td 태그에서 날짜 형식 찾기
                date = ""
                date_td = row.select("td.td_normal")
                for td in date_td:
                    text = td.text.strip()
                    # 날짜 형식 체크 (예: 2025.11.30 또는 20:21)
                    if '.' in text or ':' in text:
                        if text != article_number:
                            date = text
                            break

                # 조회수 추출
                view_count = "0"
                for td in row.select("td.td_normal"):
                    text = td.text.strip()
                    # 숫자만 있고 날짜/시간이 아닌 경우
                    if text.isdigit() and text != article_number:
                        view_count = text
                        break

                # 댓글 수 추출
                cmt_elem = row.select_one("a.cmt")
                comments = "0"
                if cmt_elem:
                    cmt_text = cmt_elem.text.strip()
                    # [2] 형태에서 숫자만 추출
                    cmt_match = re.search(r'\[(\d+)\]', cmt_text)
                    if cmt_match:
                        comments = cmt_match.group(1)

                # CSV에 쓰기
                csv_writer.writerow([article_number, title, author, date, view_count, comments, url])
                post_count += 1

                if page == 1 and post_count <= 3:
                    print(f'    저장: [{article_number}] {title[:30]}... (작성자: {author})')

            except Exception as e:
                if page == 1:
                    print(f'    에러: {e}')
                continue

        # 페이지별 CSV 파일 닫기
        csv_file.close()
        print(f'  완료: {post_count}개 게시글 저장 -> {csv_filename}')

    except Exception as e:
        print(f'  에러 발생: {e}')
        try:
            csv_file.close()
        except:
            pass
        continue

driver.close()
driver.quit()
print(f'\n모든 크롤링 완료! {output_dir} 폴더에 저장되었습니다.')