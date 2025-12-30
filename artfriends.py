import time
import os
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
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
driver.get('https://cafe.naver.com/f-e/cafes/25274813/menus/0')
time.sleep(5)

numOfPost = 24000

# Create directory for md files
output_dir = "art_contest_posts"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

targetUrl = "https://cafe.naver.com/f-e/cafes/25274813/articles/78072?referrerAllArticles=true"
# save main_window
main_window = driver.current_window_handle

for cnt in range(numOfPost):

    try:
        original_window = driver.current_window_handle
        # open new blank tab
        driver.switch_to.new_window('tab')
        driver.get(targetUrl);
        time.sleep(7) # Let the user actually see something!
        driver.switch_to.frame("cafe_main")
        r = driver.page_source
        content = BeautifulSoup(r, "html.parser")

        # Check if elements exist before accessing
        title_elem = content.select("h3.title_text")
        if not title_elem:
            print(f"제목을 찾을 수 없습니다. URL: {targetUrl}")
            driver.close()
            driver.switch_to.window(original_window)
            break

        title = title_elem[0].text

        dataUrl_elem = content.select("a#spiButton")
        if not dataUrl_elem:
            print(f"URL을 찾을 수 없습니다.")
            driver.close()
            driver.switch_to.window(original_window)
            break
        dataUrl = dataUrl_elem[0].attrs['data-url']

        nickname_elem = content.select("button.nickname")
        nickname = nickname_elem[0].text if nickname_elem else "익명"

        likes_elem = content.select("em.u_cnt._count")
        likes = likes_elem[0].text if likes_elem else "0"

        # Extract all comment areas (entire comments with author, text, date)
        comment_areas = content.select("div.comment_area")
        comments_data = []

        for comment_area in comment_areas:
            # Extract comment author
            comment_author_elem = comment_area.select_one("a.comment_nickname")
            if not comment_author_elem:
                comment_author_elem = comment_area.select_one("button.comment_nickname")
            comment_author = comment_author_elem.text.strip() if comment_author_elem else "익명"

            # Extract comment text
            comment_text_elem = comment_area.select_one("span.text_comment")
            comment_text = comment_text_elem.text.strip() if comment_text_elem else ""

            # Extract comment date
            comment_date_elem = comment_area.select_one("span.comment_info_date")
            comment_date = comment_date_elem.text.strip() if comment_date_elem else ""

            if comment_text:  # Only add if there's actual comment text
                comments_data.append({
                    'author': comment_author,
                    'text': comment_text,
                    'date': comment_date
                })

        # For backward compatibility, keep the old comments list (just nicknames)
        comments = content.select("a.comment_nickname")

        # Extract additional information
        # Date
        date_elem = content.select("span.date")
        date = date_elem[0].text.strip() if date_elem else "날짜 없음"

        # Category
        category_elem = content.select("a.link_path")
        category = category_elem[0].text.strip() if category_elem else "카테고리 없음"

        # View count
        view_elem = content.select("span.count")
        view_count = view_elem[0].text.strip() if view_elem else "0"

        # Content body
        body_elem = content.select("div.se-main-container")
        if not body_elem:
            body_elem = content.select("div#articleBody")
        if not body_elem:
            body_elem = content.select("div.se-component")

        body = ""
        if body_elem:
            # Extract text content
            body = body_elem[0].get_text(strip=False, separator="\n")
            # Remove excessive blank lines (3+ consecutive newlines -> 2 newlines)
            body = re.sub(r'\n\s*\n\s*\n+', '\n\n', body)
            # Remove leading/trailing whitespace from each line while preserving structure
            body = '\n'.join(line.rstrip() for line in body.split('\n'))
            body = body.strip()
        else:
            body = "본문 없음"

        # Get next post URL
        next_btn = content.select("a.btn_next")
        if next_btn:
            targetUrl = next_btn[0].attrs['href']
        else:
            print("다음 글 버튼을 찾을 수 없습니다. 크롤링을 종료합니다.")
            driver.close()
            driver.switch_to.window(original_window)
            break

        print('===============')
        print('- 제목', title.strip())
        print('- url \n', dataUrl,'\n')
        print('- 작성자', nickname.strip())
        print('- 날짜', date)
        print('- 카테고리', category)
        print('- 조회수', view_count)
        print('- 좋아요 갯수', likes)
        print('- 총댓글 갯수', len(comments))
        print('- 실질댓글 갯수', len(comments_data))

        # Print comment details
        if len(comments_data) > 0:
            for comment in comments_data:
                print(f"  [{comment['author']}] {comment['text'][:50]}...")
        else:
            print("comments is empty")

        # Extract post number from URL (last 5 digits)
        post_number = re.search(r'(\d{5})$', dataUrl)
        if post_number:
            filename = f"{post_number.group(1)}.md"
        else:
            # Fallback: use counter if pattern doesn't match
            filename = f"post_{cnt+1}.md"

        # Create markdown content
        md_content = f"""# {title.strip()}

## 메타 정보
- **작성자**: {nickname.strip()}
- **날짜**: {date}
- **카테고리**: {category}
- **조회수**: {view_count}
- **좋아요**: {likes}
- **총 댓글 수**: {len(comments_data)}
- **URL**: {dataUrl}

## 본문

{body.strip()}

---

## 댓글

"""

        # Add full comment details
        if len(comments_data) > 0:
            for idx, comment in enumerate(comments_data, 1):
                md_content += f"### {idx}. {comment['author']}\n"
                md_content += f"**날짜**: {comment['date']}\n\n"
                md_content += f"{comment['text']}\n\n"
                md_content += "---\n\n"
        else:
            md_content += "댓글 없음\n"

        # Write to markdown file
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f'✓ 저장 완료: {filename}')

        driver.close()
        driver.switch_to.window(original_window)

    except Exception as e:
        print(f"에러 발생: {e}")
        try:
            driver.close()
            driver.switch_to.window(original_window)
        except:
            pass
        continue



driver.close()
driver.quit()
print(f'\n모든 크롤링 완료! {output_dir} 폴더에 md 파일들이 저장되었습니다.')