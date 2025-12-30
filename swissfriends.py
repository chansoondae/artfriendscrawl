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
# driver.find_element_by_xpath('//*[@id="frmNIDLogin"]/fieldset/input').click()
# access Naver cafe
driver.get('https://cafe.naver.com/f-e/cafes/28335242/menus/0?viewType=L')
time.sleep(5)

numOfPages = 1000

# Create directory for CSV files
output_dir = "swissfriends_pages"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

targetUrl = "https://cafe.naver.com/f-e/cafes/28335242/menus/0?viewType=L&page=1"
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
        csv_filename = os.path.join(output_dir, f"swissfriends_page_{page:04d}.csv")
        csv_file = open(csv_filename, 'w', newline='', encoding='utf-8-sig')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['category', 'title', 'author', 'date', 'view_count', 'comments', 'url'])

        page_url = f"https://cafe.naver.com/f-e/cafes/28335242/menus/0?viewType=L&page={page}&size=50"
        print(f'\n[페이지 {page}/{numOfPages}] 크롤링 중...')

        driver.execute_script(f"window.location.href = '{page_url}';")
        time.sleep(5)

        r = driver.page_source
        content = BeautifulSoup(r, "html.parser")

        # 테이블의 모든 행 찾기
        rows = content.select("tr")

        post_count = 0
        for row in rows:
            try:
                # 공지글 체크 (notice 클래스가 있으면 공지글)
                if 'notice' in row.get('class', []):
                    continue

                # 카테고리 추출
                category_elem = row.select_one("td a.board_name")
                if not category_elem:
                    continue
                category = category_elem.text.strip()

                # 제목 및 URL 추출
                article_elem = row.select_one("a.article")
                if not article_elem:
                    continue
                title = article_elem.text.strip()
                article_href = article_elem.get('href', '')

                # URL에서 글 번호 추출
                article_match = re.search(r'/articles/(\d+)', article_href)
                if not article_match:
                    continue
                article_number = article_match.group(1)
                url = f"https://cafe.naver.com/swissfriends/{article_number}"

                # 작성자 추출
                author_elem = row.select_one("span.nickname")
                author = author_elem.text.strip() if author_elem else ""

                # 날짜 추출
                date_elem = row.select_one("td.td_normal.type_date")
                date = date_elem.text.strip() if date_elem else ""

                # 조회수 추출
                view_elem = row.select_one("td.td_normal.type_readCount")
                view_count = view_elem.text.strip() if view_elem else "0"

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
                csv_writer.writerow([category, title, author, date, view_count, comments, url])
                post_count += 1

            except Exception as e:
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