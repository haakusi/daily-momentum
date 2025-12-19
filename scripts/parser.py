#!/usr/bin/env python3
import os
import re
import json
from datetime import datetime
from pathlib import Path
import pytz

# 한국 시간대
KST = pytz.timezone('Asia/Seoul')

def parse_time(time_str):
    """시간 문자열을 분(minutes)으로 변환"""
    if not time_str:
        return 0
    
    # 패턴: 1h, 1시간, 30m, 30분, 1.5h, 1시간 30분 등
    hours = 0
    minutes = 0
    
    # 1.5h, 2.5h 같은 소수점 형식
    decimal_pattern = r'(\d+\.?\d*)h'
    decimal_match = re.search(decimal_pattern, time_str)
    if decimal_match:
        hours = float(decimal_match.group(1))
        return int(hours * 60)
    
    # 1h, 2h, 1시간 형식
    hour_pattern = r'(\d+)\s*(?:h|시간)'
    hour_match = re.search(hour_pattern, time_str)
    if hour_match:
        hours = int(hour_match.group(1))
    
    # 30m, 45분 형식
    min_pattern = r'(\d+)\s*(?:m|분)'
    min_match = re.search(min_pattern, time_str)
    if min_match:
        minutes = int(min_match.group(1))
    
    return hours * 60 + minutes

def parse_issue_body(body):
    """Issue 본문 파싱"""
    lines = body.split('\n')
    
    result = {
        'fitness': {'time': 0, 'note': ''},
        'english': {'time': 0, 'note': ''},
        'research': {'time': 0, 'note': ''},
        'reading': {'title': '', 'note': ''}
    }
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('```'):
            continue
        
        # 💪 헬스
        if '💪' in line:
            parts = line.split('💪', 1)[1].strip()
            time_part = parts.split('-')[0].strip() if '-' in parts else parts
            result['fitness']['time'] = parse_time(time_part)
            if '-' in parts:
                result['fitness']['note'] = parts.split('-', 1)[1].strip()
        
        # 🗣️ 영어
        elif '🗣️' in line or '🗣' in line:
            parts = line.split('🗣️' if '🗣️' in line else '🗣', 1)[1].strip()
            time_part = parts.split('-')[0].strip() if '-' in parts else parts
            result['english']['time'] = parse_time(time_part)
            if '-' in parts:
                result['english']['note'] = parts.split('-', 1)[1].strip()
        
        # 🔬 연구
        elif '🔬' in line:
            parts = line.split('🔬', 1)[1].strip()
            time_part = parts.split('-')[0].strip() if '-' in parts else parts
            result['research']['time'] = parse_time(time_part)
            if '-' in parts:
                result['research']['note'] = parts.split('-', 1)[1].strip()
        
        # 📚 독서
        elif '📚' in line:
            parts = line.split('📚', 1)[1].strip()
            if '-' in parts:
                result['reading']['title'] = parts.split('-')[0].strip()
                result['reading']['note'] = parts.split('-', 1)[1].strip()
            else:
                result['reading']['title'] = parts
    
    return result

def get_week_number(date):
    """ISO 주차 계산"""
    return date.isocalendar()[1]

def ensure_dir(path):
    """디렉토리 생성"""
    Path(path).mkdir(parents=True, exist_ok=True)

def format_time(minutes):
    """분을 시간 형식으로 변환"""
    if minutes == 0:
        return "0h"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"

def update_weekly_log(date, data):
    """주간 로그 업데이트"""
    year = date.year
    month = date.month
    week = get_week_number(date)
    
    log_dir = f"logs/{year}/{month:02d}"
    ensure_dir(log_dir)
    
    week_file = f"{log_dir}/week-{week}.md"
    date_str = date.strftime('%Y-%m-%d')
    day_name = date.strftime('%A')
    
    # 기존 파일 읽기
    if os.path.exists(week_file):
        with open(week_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = f"# Week {week} - {year}.{month:02d}\n\n"
    
    # 오늘 날짜 섹션 추가/업데이트
    day_section = f"\n## {date_str} ({day_name})\n\n"
    
    if data['fitness']['time'] > 0:
        day_section += f"💪 **헬스**: {format_time(data['fitness']['time'])}"
        if data['fitness']['note']:
            day_section += f" - {data['fitness']['note']}"
        day_section += "\n"
    
    if data['english']['time'] > 0:
        day_section += f"🗣️ **영어**: {format_time(data['english']['time'])}"
        if data['english']['note']:
            day_section += f" - {data['english']['note']}"
        day_section += "\n"
    
    if data['research']['time'] > 0:
        day_section += f"🔬 **연구**: {format_time(data['research']['time'])}"
        if data['research']['note']:
            day_section += f" - {data['research']['note']}"
        day_section += "\n"
    
    if data['reading']['title']:
        day_section += f"📚 **독서**: {data['reading']['title']}"
        if data['reading']['note']:
            day_section += f" - {data['reading']['note']}"
        day_section += "\n"
    
    # 기존 날짜 섹션 제거하고 새로 추가
    pattern = f"## {date_str}.*?(?=\n## |\Z)"
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    content += day_section
    
    with open(week_file, 'w', encoding='utf-8') as f:
        f.write(content)

def update_stats(date, data):
    """통계 JSON 업데이트"""
    stats_file = "logs/stats.json"
    ensure_dir("logs")
    
    # 기존 통계 읽기
    if os.path.exists(stats_file):
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
    else:
        stats = {
            'daily': {},
            'weekly': {},
            'monthly': {},
            'yearly': {},
            'books': []
        }
    
    date_str = date.strftime('%Y-%m-%d')
    year_str = str(date.year)
    month_str = f"{date.year}-{date.month:02d}"
    week_str = f"{date.year}-W{get_week_number(date):02d}"
    
    # 일간 통계
    stats['daily'][date_str] = {
        'fitness': data['fitness']['time'],
        'english': data['english']['time'],
        'research': data['research']['time'],
        'reading': data['reading']['title'] if data['reading']['title'] else None
    }
    
    # 주간 통계
    if week_str not in stats['weekly']:
        stats['weekly'][week_str] = {'fitness': 0, 'english': 0, 'research': 0, 'days': 0}
    stats['weekly'][week_str]['fitness'] += data['fitness']['time']
    stats['weekly'][week_str]['english'] += data['english']['time']
    stats['weekly'][week_str]['research'] += data['research']['time']
    stats['weekly'][week_str]['days'] = len([d for d in stats['daily'] if d.startswith(week_str.replace('W', '-W'))])
    
    # 월간 통계
    if month_str not in stats['monthly']:
        stats['monthly'][month_str] = {'fitness': 0, 'english': 0, 'research': 0, 'days': 0}
    stats['monthly'][month_str]['fitness'] += data['fitness']['time']
    stats['monthly'][month_str]['english'] += data['english']['time']
    stats['monthly'][month_str]['research'] += data['research']['time']
    stats['monthly'][month_str]['days'] = len([d for d in stats['daily'] if d.startswith(month_str)])
    
    # 연간 통계
    if year_str not in stats['yearly']:
        stats['yearly'][year_str] = {'fitness': 0, 'english': 0, 'research': 0, 'days': 0}
    stats['yearly'][year_str]['fitness'] += data['fitness']['time']
    stats['yearly'][year_str]['english'] += data['english']['time']
    stats['yearly'][year_str]['research'] += data['research']['time']
    stats['yearly'][year_str]['days'] = len([d for d in stats['daily'] if d.startswith(year_str)])
    
    # 독서 목록
    if data['reading']['title']:
        book_exists = False
        for book in stats['books']:
            if book['title'] == data['reading']['title']:
                book['last_read'] = date_str
                if data['reading']['note']:
                    if 'notes' not in book:
                        book['notes'] = []
                    book['notes'].append({
                        'date': date_str,
                        'note': data['reading']['note']
                    })
                book_exists = True
                break
        
        if not book_exists:
            new_book = {
                'title': data['reading']['title'],
                'first_read': date_str,
                'last_read': date_str,
                'notes': []
            }
            if data['reading']['note']:
                new_book['notes'].append({
                    'date': date_str,
                    'note': data['reading']['note']
                })
            stats['books'].append(new_book)
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def update_book_log(data):
    """독서 로그 업데이트"""
    if not data['reading']['title']:
        return
    
    books_dir = "books"
    ensure_dir(books_dir)
    
    # 파일명 생성 (특수문자 제거)
    safe_title = re.sub(r'[^\w\s-]', '', data['reading']['title'])
    safe_title = re.sub(r'[-\s]+', '-', safe_title).lower()
    book_file = f"{books_dir}/{safe_title}.md"
    
    # 기존 파일 읽기
    if os.path.exists(book_file):
        with open(book_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = f"# {data['reading']['title']}\n\n## 📖 독서 기록\n\n"
    
    # 오늘 날짜 섹션 추가
    if data['reading']['note']:
        date_str = datetime.now(KST).strftime('%Y-%m-%d')
        note_section = f"### {date_str}\n{data['reading']['note']}\n\n"
        content += note_section
    
    with open(book_file, 'w', encoding='utf-8') as f:
        f.write(content)

def parse_date_from_title(title):
    """Issue 제목에서 날짜 추출"""
    if not title:
        return None
    
    # 다양한 날짜 형식 지원
    patterns = [
        r'(\d{4})[-./ ](\d{1,2})[-./ ](\d{1,2})',  # 2024-12-19, 2024.12.19, 2024/12/19
        r'(\d{1,2})[-./ ](\d{1,2})',  # 12-19, 12.19, 12/19
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            else:
                # 현재 년도 사용
                year = datetime.now(KST).year
                month, day = int(groups[0]), int(groups[1])
            
            try:
                return KST.localize(datetime(year, month, day))
            except ValueError:
                continue
    
    return None

def main():
    # 환경 변수에서 Issue 내용 가져오기
    issue_body = os.environ.get('ISSUE_BODY', '')
    issue_title = os.environ.get('ISSUE_TITLE', '')
    
    if not issue_body:
        print("No issue body found")
        return
    
    # 제목에서 날짜 파싱 시도, 없으면 현재 시간 사용
    now = parse_date_from_title(issue_title)
    if now is None:
        now = datetime.now(KST)
        print(f"Using current date: {now.strftime('%Y-%m-%d')}")
    else:
        print(f"Using date from title: {now.strftime('%Y-%m-%d')}")
    
    # Issue 파싱
    data = parse_issue_body(issue_body)
    
    # 로그 업데이트
    update_weekly_log(now, data)
    update_stats(now, data)
    update_book_log(data)
    
    print(f"✅ Log updated for {now.strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    main()
