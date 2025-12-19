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
    
    # 이번 주 통계
    week_stats = stats['weekly'].get(current_week, {'fitness': 0, 'english': 0, 'research': 0, 'days': 0})
    week_fitness_count = sum(1 for d, v in stats['daily'].items() 
                            if d.startswith(current_week.replace('W', '-W')) and v['fitness'] > 0)
    week_english_count = sum(1 for d, v in stats['daily'].items() 
                            if d.startswith(current_week.replace('W', '-W')) and v['english'] > 0)
    week_research_count = sum(1 for d, v in stats['daily'].items() 
                             if d.startswith(current_week.replace('W', '-W')) and v['research'] > 0)
    
    # 이번 달 통계
    month_stats = stats['monthly'].get(current_month, {'fitness': 0, 'english': 0, 'research': 0, 'days': 0})
    
    # 연간 통계
    year_stats = stats['yearly'].get(current_year, {'fitness': 0, 'english': 0, 'research': 0, 'days': 0})
    
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
    recent_books = sorted(books, key=lambda x: x['last_read'], reverse=True)[:5]
    
    # README 생성
    readme = f"""# 🎯 Daily Momentum

> 매일매일 조금씩, 꾸준히 나아가는 PhD 여정 🚀

## 📊 이번 주 현황 (Week {get_week_number(now)})

| 카테고리 | 현황 | 목표 | 달성 |
|---------|------|------|------|
| 💪 헬스 | {week_fitness_count}회 ({format_time(week_stats['fitness'])}) | {weekly_targets['fitness']}회 | {get_emoji_bar(get_achievement_rate(week_fitness_count, weekly_targets['fitness']))} |
| 🗣️ 영어 | {week_english_count}회 ({format_time(week_stats['english'])}) | {weekly_targets['english']}회 | {get_emoji_bar(get_achievement_rate(week_english_count, weekly_targets['english']))} |
| 🔬 연구 | {week_research_count}회 ({format_time(week_stats['research'])}) | {weekly_targets['research']}회 | {get_emoji_bar(get_achievement_rate(week_research_count, weekly_targets['research']))} |

## 📈 이번 달 누적 ({now.month}월)

| 카테고리 | 총 시간 | 활동 일수 |
|---------|---------|----------|
| 💪 헬스 | {format_time(month_stats['fitness'])} | {sum(1 for d, v in stats['daily'].items() if d.startswith(current_month) and v['fitness'] > 0)}일 |
| 🗣️ 영어 | {format_time(month_stats['english'])} | {sum(1 for d, v in stats['daily'].items() if d.startswith(current_month) and v['english'] > 0)}일 |
| 🔬 연구 | {format_time(month_stats['research'])} | {sum(1 for d, v in stats['daily'].items() if d.startswith(current_month) and v['research'] > 0)}일 |

## 🏆 올해 통계 ({now.year}년)

- 💪 **총 헬스 시간**: {format_time(year_stats['fitness'])}
- 🗣️ **총 영어 시간**: {format_time(year_stats['english'])}
- 🔬 **총 연구 시간**: {format_time(year_stats['research'])}
- 📚 **읽은 책**: {len(books)}권
- 📅 **활동 일수**: {year_stats['days']}일

## 📅 최근 7일 활동

```
"""
    
    for day in recent_days:
        readme += f"{day['date']} ({day['day']}): {day['activities']}\n"
    
    readme += "```\n\n"
    
    # 독서 목록
    if recent_books:
        readme += "## 📚 최근 독서\n\n"
        for i, book in enumerate(recent_books, 1):
            readme += f"{i}. **{book['title']}**\n"
            if book.get('notes'):
                last_note = book['notes'][-1]
                readme += f"   - 최근: {last_note['note'][:50]}{'...' if len(last_note['note']) > 50 else ''}\n"
            readme += f"   - 마지막 읽음: {book['last_read']}\n\n"
    
    readme += """---

## 🎮 사용 방법

### 1️⃣ 일일 기록하기
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

<div align="center">

**📈 Consistency is the key to momentum! 🚀**

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
