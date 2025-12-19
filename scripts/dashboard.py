#!/usr/bin/env python3
import os
import json
from datetime import datetime, timedelta
import pytz

KST = pytz.timezone('Asia/Seoul')

def format_time(minutes):
    """분을 시간 형식으로 변환"""
    if minutes == 0:
        return "0h"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"

def get_achievement_rate(actual, target):
    """달성률 계산"""
    if target == 0:
        return 0
    return int((actual / target) * 100)

def get_emoji_bar(rate):
    """달성률을 이모지 바로 표현"""
    if rate >= 100:
        return "🟩🟩🟩🟩🟩"
    elif rate >= 80:
        return "🟩🟩🟩🟩⬜"
    elif rate >= 60:
        return "🟩🟩🟩⬜⬜"
    elif rate >= 40:
        return "🟩🟩⬜⬜⬜"
    elif rate >= 20:
        return "🟩⬜⬜⬜⬜"
    else:
        return "⬜⬜⬜⬜⬜"

def get_week_number(date):
    """ISO 주차 계산"""
    return date.isocalendar()[1]

def get_habit_week_number(stats):
    """습관 시작 후 몇 주차인지 계산"""
    if not stats.get('daily'):
        return 1
    
    # 첫 기록 날짜 찾기
    first_date_str = min(stats['daily'].keys())
    first_date = datetime.strptime(first_date_str, '%Y-%m-%d')
    
    # 시간대 정보 추가
    first_date = KST.localize(first_date)
    
    # 현재 날짜
    now = datetime.now(KST)
    
    # 주차 계산 (1부터 시작)
    days_diff = (now - first_date).days
    week_number = (days_diff // 7) + 1
    
    return week_number

def ordinal_suffix(n):
    """숫자를 서수로 변환 (1st, 2nd, 3rd, 4th...)"""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def generate_dashboard():
    """README 대시보드 생성"""
    
    # 통계 파일 읽기
    stats_file = "logs/stats.json"
    if not os.path.exists(stats_file):
        return generate_initial_readme()
    
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    now = datetime.now(KST)
    current_week = f"{now.year}-W{get_week_number(now):02d}"
    current_month = f"{now.year}-{now.month:02d}"
    current_year = str(now.year)
    
    # 주간 목표
    weekly_targets = {
        'fitness': 3,  # 3회
        'english': 4,  # 4회
        'research': 5   # 5회
    }
    
    # 이번 주 통계 계산
    week_fitness_count = 0
    week_english_count = 0
    week_research_count = 0
    week_fitness_time = 0
    week_english_time = 0
    week_research_time = 0
    
    for date_str, day_data in stats['daily'].items():
        if date_str.startswith(f"{now.year}-"):
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if get_week_number(date) == get_week_number(now):
                if day_data.get('fitness', 0) > 0:
                    week_fitness_count += 1
                    week_fitness_time += day_data['fitness']
                if day_data.get('english', 0) > 0:
                    week_english_count += 1
                    week_english_time += day_data['english']
                if day_data.get('research', 0) > 0:
                    week_research_count += 1
                    week_research_time += day_data['research']
    
    # 이번 달 통계
    month_fitness_time = 0
    month_english_time = 0
    month_research_time = 0
    month_fitness_days = 0
    month_english_days = 0
    month_research_days = 0
    
    for date_str, day_data in stats['daily'].items():
        if date_str.startswith(current_month):
            if day_data.get('fitness', 0) > 0:
                month_fitness_days += 1
                month_fitness_time += day_data['fitness']
            if day_data.get('english', 0) > 0:
                month_english_days += 1
                month_english_time += day_data['english']
            if day_data.get('research', 0) > 0:
                month_research_days += 1
                month_research_time += day_data['research']
    
    # 연간 통계
    year_fitness_time = 0
    year_english_time = 0
    year_research_time = 0
    year_active_days = set()
    
    for date_str, day_data in stats['daily'].items():
        if date_str.startswith(current_year):
            year_fitness_time += day_data.get('fitness', 0)
            year_english_time += day_data.get('english', 0)
            year_research_time += day_data.get('research', 0)
            if any([day_data.get('fitness', 0) > 0, day_data.get('english', 0) > 0, day_data.get('research', 0) > 0]):
                year_active_days.add(date_str)
    
    # 최근 7일 활동
    recent_days = []
    for i in range(6, -1, -1):
        date = now - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        day_data = stats['daily'].get(date_str, {})
        
        activities = []
        if day_data.get('fitness', 0) > 0:
            activities.append('💪')
        if day_data.get('english', 0) > 0:
            activities.append('🗣️')
        if day_data.get('research', 0) > 0:
            activities.append('🔬')
        if day_data.get('reading'):
            activities.append('📚')
        
        recent_days.append({
            'date': date.strftime('%m/%d'),
            'day': date.strftime('%a'),
            'activities': ''.join(activities) if activities else '⬜'
        })
    
    # 독서 목록
    books = stats.get('books', [])
    recent_books = sorted(books, key=lambda x: x['last_read'], reverse=True)[:3]
    
    # 습관 주차 계산
    habit_week = get_habit_week_number(stats)
    habit_week_text = ordinal_suffix(habit_week)
    
    # 최근 8주 활동 히트맵 생성 (깃허브 잔디 스타일)
    heatmap_weeks = []
    today = datetime.now(KST).date()
    
    # 8주 전부터 오늘까지
    for week_offset in range(7, -1, -1):
        week_days = []
        for day_offset in range(7):
            # 주의 시작일 계산 (월요일 기준)
            target_date = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset) + timedelta(days=day_offset)
            date_str = target_date.strftime('%Y-%m-%d')
            
            # 미래 날짜는 표시 안 함
            if target_date > today:
                week_days.append('⬜')
                continue
            
            day_data = stats['daily'].get(date_str, {})
            
            # 활동 여부만 체크 (했다 / 안했다)
            has_activity = (
                day_data.get('fitness', 0) > 0 or
                day_data.get('english', 0) > 0 or
                day_data.get('research', 0) > 0
            )
            
            # 심플하게 2가지만
            if has_activity:
                week_days.append('🟢')  # 활동함
            else:
                week_days.append('⚫')  # 활동 안 함
        
        heatmap_weeks.append(week_days)
    
    # 히트맵 HTML 생성 (미니멀하고 세련되게)
    heatmap_html = '<table><tr><td>\n\n'
    heatmap_html += '```\n'
    heatmap_html += '     Mon Tue Wed Thu Fri Sat Sun\n'
    
    for i, week in enumerate(heatmap_weeks):
        week_label = f"W-{7-i}" if i < 7 else "Now"
        heatmap_html += f"{week_label:3s}  " + "  ".join(week) + "\n"
    
    heatmap_html += '```\n'
    heatmap_html += '\n</td></tr></table>\n\n'
    heatmap_html += '<sub>⚫ No activity   🟢 Active</sub>\n'
    
    # README 생성 - 더 깔끔하고 심플하게
    readme = f"""<div align="center">

# 🎯 Daily Momentum

**매일매일 조금씩, 꾸준히 나아가는 PhD 여정**

</div>

---

## 📅 Activity Heatmap

{heatmap_html}

---

## 📊 {habit_week_text} Week

<table>
<tr>
<td align="center"><b>💪 헬스</b></td>
<td align="center"><b>🗣️ 영어</b></td>
<td align="center"><b>🔬 연구</b></td>
</tr>
<tr>
<td align="center">{week_fitness_count}/{weekly_targets['fitness']}회<br>{format_time(week_fitness_time)}</td>
<td align="center">{week_english_count}/{weekly_targets['english']}회<br>{format_time(week_english_time)}</td>
<td align="center">{week_research_count}/{weekly_targets['research']}회<br>{format_time(week_research_time)}</td>
</tr>
<tr>
<td align="center">{get_emoji_bar(get_achievement_rate(week_fitness_count, weekly_targets['fitness']))}</td>
<td align="center">{get_emoji_bar(get_achievement_rate(week_english_count, weekly_targets['english']))}</td>
<td align="center">{get_emoji_bar(get_achievement_rate(week_research_count, weekly_targets['research']))}</td>
</tr>
</table>

## 📈 이번 달 ({now.month}월)

| 💪 헬스 | 🗣️ 영어 | 🔬 연구 |
|:---:|:---:|:---:|
| {format_time(month_fitness_time)} | {format_time(month_english_time)} | {format_time(month_research_time)} |
| {month_fitness_days}일 | {month_english_days}일 | {month_research_days}일 |

## 🏆 {now.year}년 통계

<div align="center">

| 총 활동 일수 | 헬스 | 영어 | 연구 |
|:---:|:---:|:---:|:---:|
| **{len(year_active_days)}일** | {format_time(year_fitness_time)} | {format_time(year_english_time)} | {format_time(year_research_time)} |

</div>

## 📅 최근 7일

<div align="center">

"""
    
    for day in recent_days:
        readme += f"`{day['date']}` {day['activities']}&nbsp;&nbsp;"
    
    readme += "\n\n</div>\n\n"
    
    # 독서 목록
    if recent_books:
        readme += "## 📚 읽고 있는 책\n\n"
        for book in recent_books:
            readme += f"- **{book['title']}**"
            if book.get('notes'):
                readme += f" _(마지막: {book['last_read']})_"
            readme += "\n"
        readme += "\n"
    
    readme += """---

<div align="center">

### 🎮 빠른 시작

**[➕ 오늘 기록하기](../../issues/new/choose)**

</div>

<details>
<summary><b>📝 입력 형식</b></summary>

### 제목
```
2025-12-20
```

### 본문
```
💪 1.5h
🗣️ 45m
🔬 3h - VQE 회로 최적화 실험
📚 Quantum Computing - Ch.3 양자 게이트
```

### 시간 입력 방법
- `1h` 또는 `1시간` → 1시간
- `30m` 또는 `30분` → 30분  
- `1.5h` 또는 `1시간 30분` → 1시간 30분

</details>

---

<div align="center">

**📈 Consistency is the key to momentum! 🚀**

[![Star this repo](https://img.shields.io/github/stars/haakusi/daily-momentum?style=social)](https://github.com/haakusi/daily-momentum)

</div>
"""
    
    return readme

def generate_initial_readme():
    """초기 README 생성"""
    return """# 🎯 Daily Momentum

> 매일매일 조금씩, 꾸준히 나아가는 PhD 여정 🚀

## 🎮 시작하기

### 1️⃣ 첫 기록 남기기
1. [New Issue](../../issues/new/choose) 클릭
2. "📝 Daily Log" 템플릿 선택
3. 오늘의 활동 입력
4. Submit!

### 2️⃣ 입력 형식
```
💪 1.5h
🗣️ 45m
🔬 3h - VQE 회로 최적화 실험
📚 Quantum Computing - Ch.3 양자 게이트
```

### 3️⃣ 자동으로 처리되는 것들
- ✅ 주간/월간/연간 로그 자동 생성
- ✅ 통계 자동 계산
- ✅ 대시보드 자동 업데이트
- ✅ 독서 기록 자동 정리
- ✅ Issue 자동 닫기

---

## 📊 통계

첫 기록을 남기면 여기에 통계가 표시됩니다!

---

<div align="center">

**📈 Consistency is the key to momentum! 🚀**

</div>
"""

def main():
    readme_content = generate_dashboard()
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ Dashboard updated")

if __name__ == '__main__':
    main()
