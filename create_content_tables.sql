-- 게시글 본문 테이블 생성
CREATE TABLE IF NOT EXISTS art_post_contents (
    id BIGINT PRIMARY KEY,  -- art_contents_all 테이블의 id와 동일 (post_id)
    title TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_post_id FOREIGN KEY (id) REFERENCES art_contents_all(id) ON DELETE CASCADE
);

-- 댓글 테이블 생성
CREATE TABLE IF NOT EXISTS art_post_comments (
    id BIGSERIAL PRIMARY KEY,  -- 자동 증가 ID
    post_id BIGINT NOT NULL,  -- 게시글 ID
    post_author TEXT,  -- 글 작성자
    comment_author TEXT,  -- 댓글 작성자
    comment_text TEXT,  -- 댓글 내용
    comment_date TEXT,  -- 댓글 작성일 (원본 텍스트)
    comment_order INTEGER,  -- 댓글 순서 (게시글 내에서)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_post_id FOREIGN KEY (post_id) REFERENCES art_contents_all(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_post_contents_id ON art_post_contents(id);
CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON art_post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_author ON art_post_comments(comment_author);

-- RLS 정책 설정 (모든 사용자 읽기 가능)
ALTER TABLE art_post_contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE art_post_comments ENABLE ROW LEVEL SECURITY;

-- 읽기 정책
CREATE POLICY "Enable read access for all users"
ON art_post_contents
FOR SELECT
USING (true);

CREATE POLICY "Enable read access for all users"
ON art_post_comments
FOR SELECT
USING (true);

-- 삽입 정책
CREATE POLICY "Enable insert for all users"
ON art_post_contents
FOR INSERT
WITH CHECK (true);

CREATE POLICY "Enable insert for all users"
ON art_post_comments
FOR INSERT
WITH CHECK (true);

-- 업데이트 정책
CREATE POLICY "Enable update for all users"
ON art_post_contents
FOR UPDATE
USING (true)
WITH CHECK (true);

CREATE POLICY "Enable update for all users"
ON art_post_comments
FOR UPDATE
USING (true)
WITH CHECK (true);

-- 테이블 코멘트
COMMENT ON TABLE art_post_contents IS '아트프렌즈 게시글 본문 내용';
COMMENT ON TABLE art_post_comments IS '아트프렌즈 게시글 댓글';

COMMENT ON COLUMN art_post_contents.id IS '게시글 ID (art_contents_all.id와 동일)';
COMMENT ON COLUMN art_post_contents.title IS '게시글 제목';
COMMENT ON COLUMN art_post_contents.content IS '게시글 본문 내용';

COMMENT ON COLUMN art_post_comments.id IS '댓글 고유 ID (자동 증가)';
COMMENT ON COLUMN art_post_comments.post_id IS '게시글 ID';
COMMENT ON COLUMN art_post_comments.post_author IS '글 작성자';
COMMENT ON COLUMN art_post_comments.comment_author IS '댓글 작성자';
COMMENT ON COLUMN art_post_comments.comment_text IS '댓글 내용';
COMMENT ON COLUMN art_post_comments.comment_date IS '댓글 작성일';
COMMENT ON COLUMN art_post_comments.comment_order IS '댓글 순서';
