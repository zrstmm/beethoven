from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from app.database import supabase
from app.schemas import AnalyticsOut, ConversionStats, TopRecording, City
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
            "*, employees!inner(name, role), clients!inner(name, result, lesson_datetime)"
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

    # Частые ошибки — собираем из анализов
    # Простой подход: берём анализы с низкой оценкой и ищем паттерны
    common_mistakes = []
    low_score_analyses = [
        r.get("analysis", "") for r in recordings
        if r.get("score", 10) <= 5 and r.get("analysis")
    ]
    if low_score_analyses:
        # Простая аггрегация — возвращаем первые строки из анализов с низкой оценкой
        # В будущем можно отправить в LLM для суммаризации
        for analysis in low_score_analyses[:5]:
            lines = analysis.split("\n")
            for line in lines:
                line = line.strip()
                if line and ("1/" in line or "2/" in line or "3/" in line) and len(line) < 200:
                    common_mistakes.append(line)
                    break
        common_mistakes = common_mistakes[:5]

    return AnalyticsOut(
        conversion=conversion,
        top_best=top_best,
        top_worst=top_worst,
        common_mistakes=common_mistakes,
    )
