import json

input_file = "swissfriends_openai_summarized.jsonl"
output_file = "swissfriends_summary.html"

print(f"{input_file} 파일을 읽어서 HTML 파일을 생성합니다...")

# JSONL 파일 읽기
articles = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            articles.append(json.loads(line.strip()))

print(f"총 {len(articles)}개의 게시글을 읽었습니다.")

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
            background-color: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}

        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 12px;
        }}

        .category {{
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85em;
            font-weight: 500;
        }}

        .title {{
            font-size: 1.5em;
            font-weight: 600;
            color: #222;
            margin: 12px 0;
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

        .count {{
            font-weight: 600;
            color: #333;
        }}

        .card-number {{
            color: #999;
            font-size: 0.9em;
            font-weight: 500;
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
        <p class="subtitle">총 {len(articles)}개의 게시글</p>
"""

# 각 게시글 카드 생성
for idx, article in enumerate(articles, 1):
    category = article.get('category', '카테고리 없음')
    title = article.get('title', '제목 없음')
    author = article.get('author', '작성자 미상')
    date = article.get('date', '')
    view_count = article.get('view_count', '0')
    likes = article.get('likes', '0')
    total_comments = article.get('total_comments', '0')
    summary = article.get('summary', '')
    url = article.get('url', '#')

    # summary에서 "- "를 "✅ "로 변경하고 줄바꿈 처리
    summary = summary.replace('- ', '✅ ').replace('\n', '<br>')

    html_content += f"""
        <div class="card">
            <div class="card-number">#{idx}</div>
            <div class="card-header">
                <span class="category">{category}</span>
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
                <span class="stat">❤️ 좋아요 <span class="count">{likes}</span></span>
                <span class="stat">💬 댓글 <span class="count">{total_comments}</span></span>
            </div>
        </div>
"""

html_content += """
    </div>
</body>
</html>
"""

# HTML 파일 저장
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✓ HTML 파일 생성 완료!")
print(f"  - 출력 파일: {output_file}")
print(f"  - 총 게시글: {len(articles)}개")
