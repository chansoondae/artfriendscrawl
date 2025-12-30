import os
import csv
import glob

# 입력/출력 설정
input_dir = "art_contest_pages"
output_file = "art_contest_all.csv"
test_mode = False  # 테스트 모드 (True: 2개만, False: 전체)

# CSV 파일 목록 가져오기 (정렬)
csv_files = sorted(glob.glob(os.path.join(input_dir, "art_contest_page_*.csv")))

# 테스트 모드: 처음 2개만
if test_mode:
    csv_files = csv_files[:2]
    output_file = "art_contest_test.csv"

if not csv_files:
    print(f"❌ {input_dir} 폴더에 CSV 파일이 없습니다.")
    exit(1)

print(f"총 {len(csv_files)}개의 CSV 파일을 하나로 병합합니다.\n")

# 모든 데이터 병합
all_data = []
header = None
total_count = 0

for idx, csv_file in enumerate(csv_files, 1):
    try:
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)

            # 헤더는 첫 번째 파일에서만 가져오기
            if header is None:
                header = reader.fieldnames

            # 데이터 추가
            file_count = 0
            for row in reader:
                all_data.append(row)
                file_count += 1

            total_count += file_count
            print(f"[{idx}/{len(csv_files)}] {os.path.basename(csv_file)}: {file_count}개 게시글")

    except Exception as e:
        print(f"  ⚠️  {csv_file} 읽기 실패: {e}")
        continue

# 병합된 파일 저장
if all_data and header:
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"\n✓ 병합 완료!")
    print(f"  - 출력 파일: {output_file}")
    print(f"  - 총 게시글 수: {total_count:,}개")
    print(f"  - 파일 크기: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
else:
    print("❌ 병합할 데이터가 없습니다.")
