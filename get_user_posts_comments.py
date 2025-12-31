import os
from supabase import create_client, Client
from datetime import datetime
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def get_user_posts_and_comments(author_name: str):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY 환경변수를 설정해주세요.")

    supabase: Client = create_client(url, key)

    # 1. 본인 작성 글, 본문, 댓글을 한 번의 쿼리로 조회 (Join 활용)
    # 관계가 설정되어 있다면 아래와 같이 하위 테이블을 한 번에 select 할 수 있습니다.
    my_posts_response = supabase.table('art_contents_all').select(
        'id, category, title, view_count, post_date, comments,'
        'art_post_contents(content),'
        'art_post_comments(comment_author, comment_text)'
    ).eq('author', author_name).execute()

    my_posts = []
    for post in my_posts_response.data:
        post_id = post['id']
        
        # 날짜 포맷팅
        post_date = post.get('post_date', '')
        if post_date:
            try:
                dt = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y/%m/%d')
            except:
                formatted_date = post_date.split('T')[0] if 'T' in post_date else post_date
        else:
            formatted_date = ''

        # Join으로 가져온 데이터 정리
        content_data = post.get('art_post_contents')
        content = ''
        
        if content_data:
            # 리스트로 온 경우 (상태: [ {'content': '...'} ])
            if isinstance(content_data, list) and len(content_data) > 0:
                content = content_data[0].get('content', '')
            # 딕셔너리로 바로 온 경우 (상태: {'content': '...'})
            elif isinstance(content_data, dict):
                content = content_data.get('content', '')

        # 댓글 리스트 처리
        comments_list = post.get('art_post_comments', [])
        # 만약 댓글이 딕셔너리 단일 객체로 온다면 리스트로 감싸줌 (방어 코드)
        if isinstance(comments_list, dict):
            comments_list = [comments_list]

        my_posts.append({
            '글번호': post_id,
            '카테고리': post.get('category', ''),
            '제목': post.get('title', ''),
            '조회수': post.get('view_count', 0),
            '댓글수': post.get('comments', 0),
            '작성날짜': formatted_date,
            '본문내용': content,
            '댓글': [
                {
                    'comment_author': c.get('comment_author', ''),
                    'comment_text': c.get('comment_text', '')
                }
                for c in comments_list
            ]
        })

    # 2. 내가 댓글 단 글 조회 (중복 요청 최소화)
    my_comments_all = supabase.table('art_post_comments').select(
        'post_id, post_author, comment_text'
    ).eq('comment_author', author_name).execute()

    # 댓글 단 글들의 ID만 추출 (본인 글 제외)
    other_post_ids = list(set([
        c['post_id'] for c in my_comments_all.data 
        if c['post_author'] != author_name
    ]))

    my_commented_posts = []
    if other_post_ids:
        # IN 연산자를 사용하여 원글 정보를 한 번에 조회
        posts_info_response = supabase.table('art_contents_all').select(
            'id, title, author'
        ).in_('id', other_post_ids).execute()
        
        # 빠른 검색을 위한 dict 변환
        posts_info_map = {p['id']: p for p in posts_info_response.data}

        for pid in other_post_ids:
            if pid in posts_info_map:
                original_post = posts_info_map[pid]
                my_commented_posts.append({
                    '원글_제목': original_post.get('title', ''),
                    '원글_작성자': original_post.get('author', ''),
                    '내_댓글': [
                        {'comment_text': c['comment_text']}
                        for c in my_comments_all.data if c['post_id'] == pid
                    ]
                })

    return {
        '본인_작성_글': my_posts,
        '댓글_단_글': my_commented_posts
    }


def print_results(results: dict):
    """결과를 보기 좋게 출력"""
    print("\n" + "="*80)
    print("본인이 작성한 글 전체 목록")
    print("="*80)

    for i, post in enumerate(results['본인_작성_글'], 1):
        print(f"\n[{i}] 글번호: {post['글번호']}")
        print(f"    카테고리: {post['카테고리']}")
        print(f"    제목: {post['제목']}")
        print(f"    조회수: {post['조회수']}")
        print(f"    댓글수: {post['댓글수']}")
        print(f"    작성날짜: {post['작성날짜']}")
        print(f"    본문내용: {post['본문내용'][:100]}..." if len(post['본문내용']) > 100 else f"    본문내용: {post['본문내용']}")

        if post['댓글']:
            print(f"    댓글:")
            for j, comment in enumerate(post['댓글'], 1):
                print(f"      [{j}] {comment['comment_author']}: {comment['comment_text'][:50]}..." if len(comment['comment_text']) > 50 else f"      [{j}] {comment['comment_author']}: {comment['comment_text']}")

    print("\n" + "="*80)
    print("내가 댓글 단 글 (다른 사람 작성)")
    print("="*80)

    for i, post in enumerate(results['댓글_단_글'], 1):
        print(f"\n[{i}] 원글 제목: {post['원글_제목']}")
        print(f"    원글 작성자: {post['원글_작성자']}")
        print(f"    내 댓글:")
        for j, comment in enumerate(post['내_댓글'], 1):
            print(f"      [{j}] {comment['comment_text'][:100]}..." if len(comment['comment_text']) > 100 else f"      [{j}] {comment['comment_text']}")


def save_to_json(results: dict, author_name: str):
    """결과를 JSON 파일로 저장"""
    # output 폴더에 저장
    os.makedirs('output', exist_ok=True)
    filename = f"output/{author_name}_posts_comments.json"

    # 프롬프트 추가
    prompt = f"""네이버카페 아트프렌즈 '{author_name}'의 글과 댓글 목록이야.

예술가로 비유한다면 어떤 사람과 비슷할까?
아래 목록을 보고 유추하고, 그 이유를 들어줘.
'{author_name}'의 특징이 잘 드러나면 좋겠어. 
르네상스, 바로크, 로코코, 인상주의, 후기 인상주의, 현대미술, 동시대미술 다 고려해봐. 
오랫동안 생각하고 알려줘."""

    # 프롬프트와 데이터를 함께 저장
    output_data = {
        "프롬프트": prompt,
        "데이터": results
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n결과가 {filename}에 저장되었습니다.")


if __name__ == "__main__":
    # 작성자 이름 입력받기
    author_name = input("조회할 작성자 이름을 입력하세요: ")

    try:
        results = get_user_posts_and_comments(author_name)

                # 통계 계산
        print("="*12)
        print(f"📊 {author_name}님의 소통 통계 (최근 100일동안)")
        print("="*12)

        print(f"\n총 {len(results['본인_작성_글'])}개의 작성 글이 있습니다.")
        print(f"총 {len(results['댓글_단_글'])}개의 다른 글에 댓글을 달았습니다.\n")

        # 본인 글에 달린 댓글 작성자 통계 (본인 제외)
        comment_authors = {}
        for post in results['본인_작성_글']:
            for comment in post['댓글']:
                author = comment['comment_author']
                if author != author_name:  # 본인 제외
                    comment_authors[author] = comment_authors.get(author, 0) + 1

        print(f"\n✅ {author_name}님의 글에 댓글을 남긴 사람 (총 {len(comment_authors)}명, 본인 제외):\n")
        sorted_authors = sorted(comment_authors.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (author, count) in enumerate(sorted_authors, 1):
            print(f"  {i}. {author}: {count}개")

        # 내가 댓글 단 원글 작성자 통계
        post_authors = {}
        for post in results['댓글_단_글']:
            author = post['원글_작성자']
            post_authors[author] = post_authors.get(author, 0) + 1

        print(f"\n✅ {author_name}님이 댓글을 남긴 사람 (총 {len(post_authors)}명):\n")
        sorted_post_authors = sorted(post_authors.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (author, count) in enumerate(sorted_post_authors, 1):
            print(f"  {i}. {author}: {count}개 글에 댓글")

        # 결과 출력
        # print_results(results)

        # JSON 파일로 저장
        save_to_json(results, author_name)

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
