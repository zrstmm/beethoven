from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends, Query, HTTPException
from app.database import supabase
from app.schemas import (
    AnalyticsOut, ConversionStats, TopRecording, City,
    EmployeePerformance, DirectionBreakdown, WeeklyTrend, ScoreDistribution,
)
from app.auth import verify_token

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsOut)
async def get_analytics(
    city: City = Query(...),
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: str = Query(..., description="YYYY-MM-DD"),
    _: str = Depends(verify_token),
):
    try:
        dt_from = datetime.strptime(date_from, "%Y-%m-%d")
        dt_to = datetime.strptime(date_to, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Клиенты за период
    clients = supabase.table("clients").select("*").eq(
        "city", city.value
    ).gte(
        "lesson_datetime", dt_from.isoformat()
    ).lte(
        "lesson_datetime", dt_to.isoformat()
    ).execute()

    # Конверсия
    bought = sum(1 for c in clients.data if c.get("result") == "bought")
    not_bought = sum(1 for c in clients.data if c.get("result") == "not_bought")
    prepayment = sum(1 for c in clients.data if c.get("result") == "prepayment")

    conversion = ConversionStats(
        bought=bought,
        not_bought=not_bought,
        prepayment=prepayment,
        total=len(clients.data),
    )

    # Записи с оценками за период
    client_ids = [c["id"] for c in clients.data]
    recordings = []
    if client_ids:
        recs = supabase.table("recordings").select(
            "*, employees!inner(name, role, directions), clients!inner(name, result, lesson_datetime)"
        ).in_("client_id", client_ids).eq("status", "done").not_.is_(
            "score", "null"
        ).execute()
        recordings = recs.data

    # Топ лучших и худших
    sorted_best = sorted(recordings, key=lambda r: r.get("score", 0), reverse=True)
    sorted_worst = sorted(recordings, key=lambda r: r.get("score", 10))

    def to_top_recording(r):
        return TopRecording(
            client_name=r.get("clients", {}).get("name", ""),
            client_id=r.get("client_id", ""),
            employee_name=r.get("employees", {}).get("name", ""),
            score=r.get("score", 0),
            result=r.get("clients", {}).get("result"),
            lesson_datetime=r.get("clients", {}).get("lesson_datetime", ""),
        )

    top_best = [to_top_recording(r) for r in sorted_best[:3]]
    top_worst = [to_top_recording(r) for r in sorted_worst[:3]]

    # Частые ошибки
    common_mistakes = []
    low_score_analyses = [
        r.get("analysis", "") for r in recordings
        if r.get("score", 10) <= 5 and r.get("analysis")
    ]
    if low_score_analyses:
        for analysis in low_score_analyses[:5]:
            lines = analysis.split("\n")
            for line in lines:
                line = line.strip()
                if line and ("1/" in line or "2/" in line or "3/" in line) and len(line) < 200:
                    common_mistakes.append(line)
                    break
        common_mistakes = common_mistakes[:5]

    # --- Расширенная аналитика ---

    # 1. Employee Performance
    emp_stats = defaultdict(lambda: {"scores": [], "name": "", "role": ""})
    for r in recordings:
        emp = r.get("employees", {})
        emp_id = r.get("employee_id", "")
        emp_stats[emp_id]["scores"].append(r.get("score", 0))
        emp_stats[emp_id]["name"] = emp.get("name", "")
        emp_stats[emp_id]["role"] = emp.get("role", "teacher")

    employee_performance = []
    for emp_id, data in emp_stats.items():
        scores = data["scores"]
        employee_performance.append(EmployeePerformance(
            employee_name=data["name"],
            role=data["role"],
            avg_score=round(sum(scores) / len(scores), 1) if scores else 0,
            recording_count=len(scores),
        ))
    employee_performance.sort(key=lambda x: x.avg_score, reverse=True)

    # 2. Direction Breakdown
    dir_stats = defaultdict(lambda: {"clients": set(), "bought": 0, "not_bought": 0, "prepayment": 0, "scores": []})
    for r in recordings:
        emp = r.get("employees", {})
        client_info = r.get("clients", {})
        directions = emp.get("directions", [])
        client_id = r.get("client_id", "")
        result_val = client_info.get("result")
        score = r.get("score", 0)

        for d in directions:
            dir_stats[d]["clients"].add(client_id)
            dir_stats[d]["scores"].append(score)
            if result_val == "bought":
                dir_stats[d]["bought"] += 1
            elif result_val == "not_bought":
                dir_stats[d]["not_bought"] += 1
            elif result_val == "prepayment":
                dir_stats[d]["prepayment"] += 1

    direction_breakdown = []
    dir_labels = {"guitar": "Гитара", "piano": "Фортепиано", "vocal": "Вокал", "dombra": "Домбра"}
    for d, data in dir_stats.items():
        scores = data["scores"]
        direction_breakdown.append(DirectionBreakdown(
            direction=dir_labels.get(d, d),
            client_count=len(data["clients"]),
            bought=data["bought"],
            not_bought=data["not_bought"],
            prepayment=data["prepayment"],
            avg_score=round(sum(scores) / len(scores), 1) if scores else 0,
        ))

    # 3. Weekly Trends
    week_data = defaultdict(lambda: {"total": 0, "bought": 0, "not_bought": 0, "prepayment": 0})
    for c in clients.data:
        dt = datetime.fromisoformat(c["lesson_datetime"].replace("Z", "+00:00"))
        # Monday of that week
        monday = dt - timedelta(days=dt.weekday())
        week_key = monday.strftime("%Y-%m-%d")
        week_data[week_key]["total"] += 1
        result_val = c.get("result")
        if result_val == "bought":
            week_data[week_key]["bought"] += 1
        elif result_val == "not_bought":
            week_data[week_key]["not_bought"] += 1
        elif result_val == "prepayment":
            week_data[week_key]["prepayment"] += 1

    weekly_trends = []
    for week_key in sorted(week_data.keys()):
        d = week_data[week_key]
        total = d["total"]
        conv_rate = round(d["bought"] / total * 100, 1) if total > 0 else 0
        weekly_trends.append(WeeklyTrend(
            week_start=week_key,
            total=total,
            bought=d["bought"],
            not_bought=d["not_bought"],
            prepayment=d["prepayment"],
            conversion_rate=conv_rate,
        ))

    # 4. Score Distribution
    score_counts = defaultdict(int)
    for r in recordings:
        s = r.get("score")
        if s is not None:
            score_counts[s] += 1

    score_distribution = [
        ScoreDistribution(score=i, count=score_counts.get(i, 0))
        for i in range(1, 11)
    ]

    return AnalyticsOut(
        conversion=conversion,
        top_best=top_best,
        top_worst=top_worst,
        common_mistakes=common_mistakes,
        employee_performance=employee_performance,
        direction_breakdown=direction_breakdown,
        weekly_trends=weekly_trends,
        score_distribution=score_distribution,
    )
