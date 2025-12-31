import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def verify_user_data(author_name: str):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY 환경변수를 설정해주세요.")

    supabase: Client = create_client(url, key)

    print("="*80)
    print(f"'{author_name}' 데이터 검증")
    print("="*80)

    # 1. art_contents_all 테이블에서 본인 작성 글 수 확인
    my_posts_response = supabase.table('art_contents_all').select(
        'id, title, author'
    ).eq('author', author_name).execute()

    print(f"\n📝 [art_contents_all] {author_name}이(가) 작성한 글:")
    print(f"   총 {len(my_posts_response.data)}개")

    if len(my_posts_response.data) <= 20:
        for i, post in enumerate(my_posts_response.data, 1):
            print(f"   {i}. ID:{post['id']} - {post['title']}")
    else:
        print(f"   (처음 10개만 표시)")
        for i, post in enumerate(my_posts_response.data[:10], 1):
            print(f"   {i}. ID:{post['id']} - {post['title']}")

    # 2. art_post_comments 테이블에서 본인이 단 댓글 수 확인
    my_comments_response = supabase.table('art_post_comments').select(
        'id, post_id, post_author, comment_author, comment_text'
    ).eq('comment_author', author_name).execute()

    print(f"\n💬 [art_post_comments] {author_name}이(가) 작성한 댓글:")
    print(f"   총 {len(my_comments_response.data)}개")

    # 본인 글에 단 댓글과 다른 사람 글에 단 댓글 구분
    own_post_comments = []
    other_post_comments = []

    for comment in my_comments_response.data:
        if comment['post_author'] == author_name:
            own_post_comments.append(comment)
        else:
            other_post_comments.append(comment)

    print(f"   - 본인 글에 단 댓글: {len(own_post_comments)}개")
    print(f"   - 다른 사람 글에 단 댓글: {len(other_post_comments)}개")

    # 다른 사람 글에 단 댓글의 고유 post_id 개수
    other_post_ids = list(set([c['post_id'] for c in other_post_comments]))
    print(f"   - 댓글을 단 다른 사람의 글 개수: {len(other_post_ids)}개")

    if len(other_post_ids) <= 20:
        print(f"\n   댓글을 단 다른 사람 글 목록:")
        for pid in other_post_ids[:10]:
            post_info = supabase.table('art_contents_all').select(
                'id, title, author'
            ).eq('id', pid).execute()
            if post_info.data:
                p = post_info.data[0]
                comment_count = len([c for c in other_post_comments if c['post_id'] == pid])
                print(f"   - ID:{p['id']} [{p['author']}] {p['title']} (댓글 {comment_count}개)")

    # 3. 본인 글에 달린 댓글 확인
    my_post_ids = [p['id'] for p in my_posts_response.data]

    if my_post_ids:
        comments_on_my_posts = supabase.table('art_post_comments').select(
            'id, post_id, comment_author, comment_text'
        ).in_('post_id', my_post_ids).execute()

        print(f"\n💭 [art_post_comments] {author_name}의 글에 달린 댓글:")
        print(f"   총 {len(comments_on_my_posts.data)}개")

        # 작성자별 통계
        comment_authors = {}
        for comment in comments_on_my_posts.data:
            author = comment['comment_author']
            comment_authors[author] = comment_authors.get(author, 0) + 1

        print(f"\n   댓글 작성자 분포 (총 {len(comment_authors)}명):")
        sorted_authors = sorted(comment_authors.items(), key=lambda x: x[1], reverse=True)
        for i, (author, count) in enumerate(sorted_authors[:10], 1):
            self_mark = " (본인)" if author == author_name else ""
            print(f"   {i}. {author}: {count}개{self_mark}")

    # 4. art_post_contents 테이블 확인
    if my_post_ids:
        try:
            contents_response = supabase.table('art_post_contents').select(
                'id, content'
            ).in_('id', my_post_ids).execute()

            print(f"\n📄 [art_post_contents] {author_name}의 글 본문:")
            print(f"   총 {len(contents_response.data)}개")

            missing_contents = set(my_post_ids) - set([c['id'] for c in contents_response.data])
            if missing_contents:
                print(f"   ⚠️ 본문이 없는 글: {len(missing_contents)}개")
                for pid in list(missing_contents)[:5]:
                    print(f"      - id: {pid}")
        except Exception as e:
            print(f"\n📄 [art_post_contents] 조회 중 오류: {str(e)}")
            print(f"   (테이블 스키마를 확인해주세요)")

    print("\n" + "="*80)
    print("검증 요약")
    print("="*80)
    print(f"✅ 본인 작성 글: {len(my_posts_response.data)}개")
    print(f"✅ 댓글을 단 다른 사람 글: {len(other_post_ids)}개")
    print(f"✅ 본인 글에 달린 총 댓글: {len(comments_on_my_posts.data)}개 (본인 댓글 포함)")
    print("="*80)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        author_name = sys.argv[1]
    else:
        author_name = input("확인할 작성자 이름을 입력하세요: ")

    try:
        verify_user_data(author_name)
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
