import json

input_file = "swissfriends_all_summarized.jsonl"
output_file = "swissfriends_all_summarized.html"

print(f"{input_file} 파일을 읽어서 HTML 파일을 생성합니다...")

# JSONL 파일 읽기
articles = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            articles.append(json.loads(line.strip()))

print(f"총 {len(articles)}개의 게시글을 읽었습니다.")

# 월별 통계 계산
month_stats = {}
for article in articles:
    month = article.get('travel_month', 'NONE')
    month_stats[month] = month_stats.get(month, 0) + 1

# 카테고리별 통계 계산
category_stats = {}
for article in articles:
    category = article.get('category', '기타')
    category_stats[category] = category_stats.get(category, 0) + 1

# 카테고리를 카운트 순으로 정렬
sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)

# HTML 생성
html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>스위스 여행 카페 게시글 요약</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #E3F2FD 0%, #FFF9E6 50%, #FFE8F0 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            text-align: center;
            color: #1976d2;
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 700;
        }}

        .subtitle {{
            text-align: center;
            color: #555;
            margin-bottom: 30px;
            font-size: 1.1em;
            font-weight: 500;
        }}

        .filter-section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}

        .filter-title {{
            font-size: 1.2em;
            font-weight: 700;
            color: #1976d2;
            margin-bottom: 16px;
        }}

        .filter-options {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }}

        .checkbox-label {{
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            border: 2px solid rgba(25, 118, 210, 0.2);
            background: rgba(255, 255, 255, 0.8);
            border-radius: 24px;
            cursor: pointer;
            font-size: 0.95em;
            transition: all 0.3s ease;
            color: #555;
        }}

        .checkbox-label:hover {{
            border-color: #42a5f5;
            color: #1976d2;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(66, 165, 245, 0.2);
        }}

        .checkbox-label input[type="checkbox"] {{
            margin-right: 6px;
        }}

        .checkbox-label input[type="checkbox"]:checked + span {{
            font-weight: 600;
        }}

        input[type="checkbox"]:checked ~ .checkbox-label,
        .checkbox-label:has(input[type="checkbox"]:checked) {{
            background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
            color: white;
            border-color: #1976d2;
            box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3);
        }}

        .count {{
            font-weight: 600;
            margin-left: 4px;
        }}

        .card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid rgba(255, 255, 255, 0.5);
            transition: all 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-6px);
            box-shadow: 0 8px 30px rgba(25, 118, 210, 0.15);
            border-color: rgba(66, 165, 245, 0.3);
        }}

        .card.hidden {{
            display: none;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 12px;
        }}

        .category {{
            display: inline-block;
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            color: #1565c0;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(25, 118, 210, 0.15);
        }}

        .month-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            color: #e65100;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 700;
            margin-left: 8px;
            box-shadow: 0 2px 8px rgba(245, 124, 0, 0.15);
        }}

        .title {{
            font-size: 1.5em;
            font-weight: 700;
            color: #1a237e;
            margin: 12px 0;
            line-height: 1.4;
        }}

        .meta {{
            display: flex;
            gap: 16px;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .summary {{
            color: #444;
            line-height: 2.2;
            font-size: 1em;
        }}

        .stats {{
            display: flex;
            gap: 16px;
            margin-top: 16px;
        }}

        .stat {{
            display: flex;
            align-items: center;
            gap: 6px;
            color: #666;
            font-size: 0.9em;
        }}

        .card-number {{
            color: #90a4ae;
            font-size: 0.9em;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .url-link {{
            color: #666;
            font-size: 1em;
            margin: 8px 0 12px 0;
            word-break: break-all;
        }}

        .url-link a {{
            color: #666;
            text-decoration: none;
        }}

        .url-link a:hover {{
            color: #1976d2;
            text-decoration: underline;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 12px;
            }}

            h1 {{
                font-size: 1.8em;
            }}

            .card {{
                padding: 16px;
            }}

            .title {{
                font-size: 1.2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🇨🇭 스위스 여행 카페 게시글 요약</h1>
        <p class="subtitle">총 <span id="totalCount">{len(articles)}</span>개의 게시글</p>

        <div class="filter-section">
            <div class="filter-title">📅 여행 월 필터 (다중 선택 가능)</div>
            <div class="filter-options">
                <label class="checkbox-label">
                    <input type="checkbox" class="month-filter" value="ALL" checked onchange="applyFilters()">
                    <span>전체 <span class="count">({len(articles)})</span></span>
                </label>"""

# 월별 라디오 버튼 생성
month_names = {
    'JAN': '1월', 'FEB': '2월', 'MAR': '3월', 'APR': '4월',
    'MAY': '5월', 'JUN': '6월', 'JUL': '7월', 'AUG': '8월',
    'SEP': '9월', 'OCT': '10월', 'NOV': '11월', 'DEC': '12월',
    'NONE': '미확인'
}

for month_key in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'NONE']:
    count = month_stats.get(month_key, 0)
    if count > 0:
        month_name = month_names[month_key]
        html_content += f"""
                <label class="checkbox-label">
                    <input type="checkbox" class="month-filter" value="{month_key}" onchange="applyFilters()">
                    <span>{month_name} <span class="count">({count})</span></span>
                </label>"""

html_content += """
            </div>
        </div>

        <div class="filter-section">
            <div class="filter-title">📂 카테고리 필터 (다중 선택 가능)</div>
            <div class="filter-options">
                <label class="checkbox-label">
                    <input type="checkbox" class="category-filter" value="ALL" checked onchange="applyFilters()">
                    <span>전체 <span class="count">({total_count})</span></span>
                </label>""".format(total_count=len(articles))

# 카테고리별 체크박스 생성
for category, count in sorted_categories:
    # 카테고리 이름이 너무 길면 축약
    display_category = category[:30] + '...' if len(category) > 30 else category
    html_content += f"""
                <label class="checkbox-label">
                    <input type="checkbox" class="category-filter" value="{category}" onchange="applyFilters()">
                    <span>{display_category} <span class="count">({count})</span></span>
                </label>"""

html_content += """
            </div>
        </div>
"""

# 각 게시글 카드 생성
for idx, article in enumerate(articles, 1):
    category = article.get('category', '카테고리 없음')
    title = article.get('title', '제목 없음')
    author = article.get('author', '작성자 미상')
    date = article.get('date', '')
    view_count = article.get('view_count', '0')
    comments = article.get('comments', '0')
    summary = article.get('summary', '')
    url = article.get('url', '#')
    post_id = article.get('post_id', '')
    travel_month = article.get('travel_month', 'NONE')

    # travel_month 한글 변환
    month_display = month_names.get(travel_month, '미확인')

    # summary에서 "- "를 "✅ "로 변경하고 줄바꿈 처리
    summary = summary.replace('- ', '✅ ').replace('\n', '<br>')

    html_content += f"""
        <div class="card" data-month="{travel_month}" data-category="{category}">
            <div class="card-number">#{idx}</div>
            <div class="card-header">
                <div>
                    <span class="category">{category}</span>
                    <span class="month-badge">🗓️ {month_display}</span>
                </div>
            </div>
            <h2 class="title">
                {title}
            </h2>
            <div class="url-link">
                <a href="{url}" target="_blank">{url}</a>
            </div>
            <div class="meta">
                <span class="meta-item">👤 {author}</span>
                <span class="meta-item">📅 {date}</span>
            </div>
            <div class="summary">
                {summary}
            </div>
            <div class="stats">
                <span class="stat">👁️ 조회 <span class="count">{view_count}</span></span>
                <span class="stat">💬 댓글 <span class="count">{comments}</span></span>
            </div>
        </div>
"""

html_content += """
    </div>

    <script>
        function applyFilters() {
            // 선택된 월들 가져오기
            const monthCheckboxes = document.querySelectorAll('.month-filter:checked');
            const selectedMonths = Array.from(monthCheckboxes).map(cb => cb.value);

            // 선택된 카테고리들 가져오기
            const categoryCheckboxes = document.querySelectorAll('.category-filter:checked');
            const selectedCategories = Array.from(categoryCheckboxes).map(cb => cb.value);

            // "전체" 체크박스 처리
            const allMonthChecked = selectedMonths.includes('ALL');
            const allCategoryChecked = selectedCategories.includes('ALL');

            // 모든 카드 필터링
            const cards = document.querySelectorAll('.card');
            let visibleCount = 0;

            cards.forEach(card => {
                const cardMonth = card.getAttribute('data-month');
                const cardCategory = card.getAttribute('data-category');

                // 월 필터 체크 (전체 선택 또는 선택된 월에 포함)
                const monthMatch = allMonthChecked || selectedMonths.length === 0 || selectedMonths.includes(cardMonth);

                // 카테고리 필터 체크 (전체 선택 또는 선택된 카테고리에 포함)
                const categoryMatch = allCategoryChecked || selectedCategories.length === 0 || selectedCategories.includes(cardCategory);

                // 둘 다 매치되면 표시
                if (monthMatch && categoryMatch) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            });

            // 표시되는 게시글 수 업데이트
            document.getElementById('totalCount').textContent = visibleCount;
        }
    </script>
</body>
</html>
"""

# HTML 파일 저장
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✓ HTML 파일 생성 완료!")
print(f"  - 출력 파일: {output_file}")
print(f"  - 총 게시글: {len(articles)}개")
print(f"\n📊 월별 통계:")
for month_key in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'NONE']:
    count = month_stats.get(month_key, 0)
    if count > 0:
        print(f"  {month_names[month_key]}: {count}개")

print(f"\n📂 카테고리 통계 (상위 10개):")
for category, count in sorted_categories[:10]:
    print(f"  {category}: {count}개")
