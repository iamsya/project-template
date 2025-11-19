#!/usr/bin/env python3
"""
Markdown 표를 HTML 표로 변환하는 스크립트
Confluence 호환성을 위해 Markdown 표 형식을 HTML로 변환합니다.
"""

import re
import sys
from pathlib import Path


def markdown_table_to_html(markdown_table: str) -> str:
    """Markdown 표를 HTML 표로 변환"""
    lines = markdown_table.strip().split('\n')
    
    if len(lines) < 2:
        return markdown_table
    
    # 헤더 추출
    header_line = lines[0]
    separator_line = lines[1]
    
    # 헤더 파싱
    headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
    
    # HTML 테이블 생성
    html = ['<table>']
    html.append('<thead>')
    html.append('<tr>')
    for header in headers:
        # **예**, **아니오** 같은 강조 제거하고 <strong> 태그로 변환
        header_clean = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', header)
        # `code` 형식을 <code> 태그로 변환
        header_clean = re.sub(r'`(.+?)`', r'<code>\1</code>', header_clean)
        html.append(f'<th>{header_clean}</th>')
    html.append('</tr>')
    html.append('</thead>')
    html.append('<tbody>')
    
    # 데이터 행 파싱
    for line in lines[2:]:
        if not line.strip() or line.strip().startswith('---'):
            continue
        
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        html.append('<tr>')
        for cell in cells:
            # **예**, **아니오** 같은 강조 제거하고 <strong> 태그로 변환
            cell_clean = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
            # `code` 형식을 <code> 태그로 변환
            cell_clean = re.sub(r'`(.+?)`', r'<code>\1</code>', cell_clean)
            html.append(f'<td>{cell_clean}</td>')
        html.append('</tr>')
    
    html.append('</tbody>')
    html.append('</table>')
    
    return '\n'.join(html)


def convert_file(file_path: Path):
    """파일의 모든 Markdown 표를 HTML로 변환"""
    content = file_path.read_text(encoding='utf-8')
    
    # Markdown 표 패턴 찾기
    # | 헤더1 | 헤더2 | ... |
    # |-------|-------|-----|
    # | 데이터1 | 데이터2 | ... |
    # 표 앞뒤에 빈 줄이 있을 수 있음
    pattern = r'(\n\|[^\n]+\|\n\|[-\s:|]+\|\n(?:\|[^\n]+\|\n?)+)'
    
    def replace_table(match):
        table_text = match.group(1).strip()
        html_table = markdown_table_to_html(table_text)
        return '\n' + html_table + '\n'
    
    new_content = re.sub(pattern, replace_table, content)
    
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')
        print(f"✅ 변환 완료: {file_path}")
        return True
    else:
        print(f"ℹ️  변환할 표가 없음: {file_path}")
        return False


def main():
    """메인 함수"""
    docs_dir = Path(__file__).parent / 'docs'
    
    # API 가이드 파일들
    api_guide_files = [
        'PLCS_API_GUIDE.md',
        'PLC_PGM_MAPPING_API_GUIDE.md',
        'PROGRAM_REGISTER_API_GUIDE.md',
        'PROGRAMS_API_GUIDE.md',
        'CHAT_HISTORY_API_GUIDE.md',
        # 화면별 API 가이드
        'PLC_REGISTER_SCREEN_API_GUIDE.md',
        'PLC_MAPPING_SCREEN_API_GUIDE.md',
        'PLC_VIEW_SCREEN_API_GUIDE.md',
        'PLC_CHAT_SCREEN_API_GUIDE.md',
    ]
    
    converted_count = 0
    
    for filename in api_guide_files:
        file_path = docs_dir / filename
        if file_path.exists():
            if convert_file(file_path):
                converted_count += 1
        else:
            print(f"⚠️  파일 없음: {file_path}")
    
    print(f"\n총 {converted_count}개 파일 변환 완료")


if __name__ == '__main__':
    main()

