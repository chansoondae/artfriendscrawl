#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONL 파일을 CSV 형식으로 변환하는 스크립트
"""

import csv
import json


def jsonl_to_csv(jsonl_path, csv_path):
    """JSONL 파일을 CSV로 변환"""
    count = 0

    # 먼저 첫 번째 라인을 읽어서 필드명 확인
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        if first_line.strip():
            first_item = json.loads(first_line.strip())
            fieldnames = list(first_item.keys())

    # CSV 파일로 변환
    with open(jsonl_path, 'r', encoding='utf-8') as jsonl_file:
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for line in jsonl_file:
                if line.strip():
                    item = json.loads(line.strip())
                    writer.writerow(item)
                    count += 1

    return count, fieldnames


def main():
    jsonl_path = "swissfriends_all_summarized.jsonl"
    csv_path = "swissfriends_all_summarized.csv"

    print(f"JSONL 파일 읽기: {jsonl_path}")
    print(f"CSV 파일로 변환 중...\n")

    count, fieldnames = jsonl_to_csv(jsonl_path, csv_path)

    print(f"✓ 변환 완료!")
    print(f"총 {count}개 행 변환됨")
    print(f"출력 파일: {csv_path}")
    print(f"\n컬럼 목록:")
    for i, field in enumerate(fieldnames, 1):
        print(f"  {i}. {field}")


if __name__ == "__main__":
    main()
