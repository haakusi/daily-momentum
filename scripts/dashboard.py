#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime, timedelta
import pytz

KST = pytz.timezone("Asia/Seoul")


# -----------------------------
# Formatting helpers
# -----------------------------
def format_time(minutes: int) -> str:
    """분을 시간 형식으로 변환"""
    if not minutes:
        return "0h"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def get_achievement_rate(actual: int, target: int) -> int:
    """달성률 계산"""
    if target <= 0:
        return 0
    return int((actual / target) * 100)


def get_week_number(date: datetime) -> int:
    """ISO 주차 계산"""
    return date.isocalendar()[1]


def ordinal_suffix(n: int) -> str:
    """숫자를 서수로 변환 (1st, 2nd, 3rd, 4th...)"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def get_habit_week_number(stats: dict) -> int:
    """습관 시작 후 몇 주차인지 계산"""
    daily = stats.get("daily", {})
    if not daily:
        return 1

    first_date_str = min(daily.keys())
    first_date = datetime.strptime(first_date_str, "%Y-%m-%d")
    first_date = KST.localize(first_date)

    now = datetime.now(KST)
    days_diff = (now - first_date).days
    return (days_diff // 7) + 1


def progress_bar(count: int, target: int, width: int = 5) -> str:
    """고정폭 진행바 생성"""
    if target <= 0:
        return "░" * width
    filled = int((count / target) * width)
    filled = max(0, min(width, filled))
    return ("▰" * filled) + ("░" * (width - filled))


def clamp(s: str, max_len: int = 76) -> str:
    """과도하게 긴 텍스트를 줄여 README 가로 스크롤을 예방"""
    return s if len(s) <= max_len else (s[: max_len - 1] + "…")


# -----------------------------
# Stats helpers
# -----------------------------
def safe_daily(stats: dict) -> dict:
    daily = stats.get("daily", {})
    return daily if isinstance(daily, dict) else {}


def has_any_activity(day_data: dict) -> bool:
    return any(
        [
            day_data.get("fitness", 0) > 0,
            day_data.get("english", 0) > 0,
            day_data.get("research", 0) > 0,
        ]
    )


def compute_week_stats(daily: dict, now: datetime) -> dict:
    """이번 주(ISO week) 카운트/시간 계산"""
    w = get_week_number(now)
    y = now.year

    counts = {"fitness": 0, "english": 0, "research": 0}
    times = {"fitness": 0, "english": 0, "research": 0}

    for date_str, day_data in daily.items():
        if not date_str.startswith(f"{y}-"):
            continue
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        if get_week_number(d) != w:
            continue

        for k in ["fitness", "english", "research"]:
            minutes = int(day_data.get(k, 0) or 0)
            if minutes > 0:
                counts[k] += 1
                times[k] += minutes

    total_time = times["fitness"] + times["english"] + times["research"]
    return {"counts": counts, "times": times, "total_time": total_time}


def compute_month_stats(daily: dict, now: datetime) -> dict:
    """이번 달 시간/일수 계산"""
    prefix = f"{now.year}-{now.month:02d}"
    times = {"fitness": 0, "english": 0, "research": 0}
    days = {"fitness": 0, "english": 0, "research": 0}

    for date_str, day_data in daily.items():
        if not date_str.startswith(prefix):
            continue
        for k in ["fitness", "english", "research"]:
            minutes = int(day_data.get(k, 0) or 0)
            if minutes > 0:
                times[k] += minutes
                days[k] += 1

    return {"times": times, "days": days}


def compute_year_stats(daily: dict, now: datetime) -> dict:
    """올해 시간/활동일수 계산"""
    prefix = f"{now.year}-"
    times = {"fitness": 0, "english": 0, "research": 0}
    active_days = set()

    for date_str, day_data in daily.items():
        if not date_str.startswith(prefix):
            continue
        for k in ["fitness", "english", "research"]:
            times[k] += int(day_data.get(k, 0) or 0)
        if has_any_activity(day_data):
            active_days.add(date_str)

    return {"times": times, "active_days": active_days}


def compute_streak(daily: dict) -> dict:
    """
    스트릭 계산:
    - 'daily'에 기록된 날짜 기준으로 연속 활동일수
    - 마지막 날짜가 활동이면 current_streak 반영
    """
    if not daily:
        return {"current": 0, "best": 0}

    sorted_dates = sorted(daily.keys())
    best = 0
    temp = 0
    current = 0

    for i, date_str in enumerate(sorted_dates):
        day_data = daily.get(date_str, {})
        active = has_any_activity(day_data)

        if active:
            temp += 1
            best = max(best, temp)
        else:
            temp = 0

        if i == len(sorted_dates) - 1 and active:
            current = temp

    return {"current": current, "best": best}


def compute_recent_7days(daily: dict, now: datetime) -> list:
    """최근 7일 활동 이모지 라인 생성"""
    rows = []
    for i in range(6, -1, -1):
        d = now - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        dd = daily.get(date_str, {}) or {}

        icons = []
        if int(dd.get("fitness", 0) or 0) > 0:
            icons.append("💪")
        if int(dd.get("english", 0) or 0) > 0:
            icons.append("🗣️")
        if int(dd.get("research", 0) or 0) > 0:
            icons.append("🔬")
        if dd.get("reading"):
            icons.append("📚")

        rows.append(
            {
                "md": d.strftime("%m/%d"),
                "icons": " ".join(icons) if icons else "⬜",
            }
        )
    return rows


def get_recent_books(stats: dict, n: int = 3) -> list:
    books = stats.get("books", [])
    if not isinstance(books, list):
        return []
    valid = [b for b in books if isinstance(b, dict) and b.get("title")]
    return sorted(valid, key=lambda x: x.get("last_read", ""), reverse=True)[:n]


# -----------------------------
# README generation
# -----------------------------
def generate_dashboard() -> str:
    """README 대시보드 생성"""

    stats_file = "logs/stats.json"
    if not os.path.exists(stats_file):
        return generate_initial_readme()

    with open(stats_file, "r", encoding="utf-8") as f:
        stats = json.load(f)

    now = datetime.now(KST)
    daily = safe_daily(stats)

    # Targets (weekly)
    weekly_targets = {"fitness": 3, "english": 4, "research": 5}

    # Compute stats
    habit_week_no = get_habit_week_number(stats)
    habit_week_text = ordinal_suffix(habit_week_no)

    streak = compute_streak(daily)
    year_stats = compute_year_stats(daily, now)
    month_stats = compute_month_stats(daily, now)
    week_stats = compute_week_stats(daily, now)
    recent_7 = compute_recent_7days(daily, now)
    recent_books = get_recent_books(stats, n=3)

    # Weekly rates
    wc = week_stats["counts"]
    wt = week_stats["times"]
    total_week_time = week_stats["total_time"]

    fitness_rate = get_achievement_rate(wc["fitness"], weekly_targets["fitness"])
    english_rate = get_achievement_rate(wc["english"], weekly_targets["english"])
    research_rate = get_achievement_rate(wc["research"], weekly_targets["research"])

    # Build sections (keep lines short to avoid horizontal scrolling)
    hero_line = clamp(
        f"🔥 **Streak**: **{streak['current']} days**  •  🏆 **Best**: **{streak['best']} days**  •  📅 **Total Active**: **{len(year_stats['active_days'])} days**",
        120,
    )

    week_table = f"""### 📅 This Week · {habit_week_text} Week

| Habit | Progress | Goal | Status |
|---|---:|---:|---:|
| 💪 Fitness | {progress_bar(wc["fitness"], weekly_targets["fitness"])} | {wc["fitness"]} / {weekly_targets["fitness"]} | {fitness_rate}% |
| 🗣️ English | {progress_bar(wc["english"], weekly_targets["english"])} | {wc["english"]} / {weekly_targets["english"]} | {english_rate}% |
| 🔬 Research | {progress_bar(wc["research"], weekly_targets["research"])} | {wc["research"]} / {weekly_targets["research"]} | {research_rate}% |

**⏱ Total:** **{format_time(total_week_time)}** active this week
"""

    month_t = month_stats["times"]
    month_d = month_stats["days"]
    month_section = f"""### 📈 This Month ({now.month}월)

| 💪 Fitness | 🗣️ English | 🔬 Research |
|:--:|:--:|:--:|
| **{format_time(month_t["fitness"])}** | **{format_time(month_t["english"])}** | **{format_time(month_t["research"])}** |
| {month_d["fitness"]} day(s) | {month_d["english"]} day(s) | {month_d["research"]} day(s) |
"""

    year_t = year_stats["times"]
    year_section = f"""### 🏆 {now.year} Overview

<div align="center">

| Active Days | 💪 Fitness | 🗣️ English | 🔬 Research |
|---:|---:|---:|---:|
| **{len(year_stats["active_days"])}** | {format_time(year_t["fitness"])} | {format_time(year_t["english"])} | **{format_time(year_t["research"])}** |

</div>
"""

    last7_lines = []
    for r in recent_7:
        last7_lines.append(f"`{r['md']}`  {r['icons']}")
    last7_block = "\n".join(last7_lines)

    books_section = ""
    if recent_books:
        books_section = "### 📚 Reading\n\n"
        for b in recent_books:
            title = b.get("title", "").strip()
            last_read = b.get("last_read", "").strip()
            notes = b.get("notes")
            if last_read:
                books_section += f"- **{title}** _(last: {last_read})_\n"
            else:
                books_section += f"- **{title}**\n"
            if notes:
                # notes가 길어질 수 있으니 한 줄로만
                books_section += f"  - {clamp(str(notes).strip(), 120)}\n"
        books_section += "\n"

    # Final README
    readme = f"""<div align="center">

# 🎯 Daily Momentum

**매일매일 조금씩, 꾸준히 나아가는 습관 만들기**

</div>

---

## 📊 Progress Dashboard

<div align="center">

{hero_line}

</div>

{week_table}

{month_section}

{year_section}

### 📆 Last 7 Days

{last7_block}

{books_section}---

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
