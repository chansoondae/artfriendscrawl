-- 테스트 데이터 삭제

-- 댓글 테이블 전체 삭제
DELETE FROM art_post_comments;

-- 본문 테이블 전체 삭제
DELETE FROM art_post_contents;

-- 확인
SELECT COUNT(*) as content_count FROM art_post_contents;
SELECT COUNT(*) as comment_count FROM art_post_comments;
