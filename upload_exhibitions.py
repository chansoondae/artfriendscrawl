import os
import csv
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

# CSV 파일 읽기
csv_file = "grouped_exhibitions.csv"

print(f"{csv_file} 파일을 읽어옵니다...")

exhibitions_data = []
with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        exhibitions_data.append({
            'original_name': row['original_name'],
            'grouped_name': row['grouped_name']
        })

print(f"  - 총 {len(exhibitions_data)}개의 전시 그룹핑 데이터를 읽었습니다.")

# Supabase에 배치 업로드
print("\nSupabase에 데이터를 업로드합니다...")

batch_size = 500
total_batches = (len(exhibitions_data) + batch_size - 1) // batch_size

for i in range(0, len(exhibitions_data), batch_size):
    batch = exhibitions_data[i:i + batch_size]
    batch_num = (i // batch_size) + 1

    try:
        response = supabase.table('grouped_exhibitions').insert(batch).execute()
        print(f"  - 배치 {batch_num}/{total_batches} 완료 ({len(batch)}개)")
    except Exception as e:
        print(f"  ✗ 배치 {batch_num} 업로드 실패: {e}")
        break

print(f"\n✓ 업로드 완료!")
print(f"  - 총 {len(exhibitions_data)}개의 전시 그룹핑 데이터")
print(f"  - 테이블: grouped_exhibitions")
