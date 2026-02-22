from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from app.database import supabase
from app.schemas import ClientCard, ClientDetail, RecordingDetail, City
from app.auth import verify_token

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientCard])
async def get_clients(
    city: City = Query(...),
    week_start: str = Query(..., description="Monday date in YYYY-MM-DD format"),
    _: str = Depends(verify_token),
):
    """Клиенты за неделю для канбан-доски."""
    try:
        start = datetime.strptime(week_start, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    end = start + timedelta(days=7)

    clients = supabase.table("clients").select("*").eq(
        "city", city.value
    ).gte(
        "lesson_datetime", start.isoformat()
    ).lt(
        "lesson_datetime", end.isoformat()
    ).order("lesson_datetime").execute()

    cards = []
    for c in clients.data:
        # Получаем записи для этого клиента
        recs = supabase.table("recordings").select(
            "*, employees!inner(name, role)"
        ).eq("client_id", c["id"]).execute()

        teacher_name = None
        manager_name = None
        teacher_score = None
        manager_score = None
        teacher_status = None
        manager_status = None

        for r in recs.data:
            emp = r.get("employees", {})
            if emp.get("role") == "teacher":
                teacher_name = emp.get("name")
                teacher_score = r.get("score")
                teacher_status = r.get("status")
            elif emp.get("role") == "sales_manager":
                manager_name = emp.get("name")
                manager_score = r.get("score")
                manager_status = r.get("status")

        cards.append(ClientCard(
            id=c["id"],
            name=c["name"],
            city=c["city"],
            lesson_datetime=c["lesson_datetime"],
            result=c.get("result"),
            teacher_name=teacher_name,
            manager_name=manager_name,
            teacher_score=teacher_score,
            manager_score=manager_score,
            teacher_status=teacher_status,
            manager_status=manager_status,
        ))

    return cards


@router.get("/{client_id}", response_model=ClientDetail)
async def get_client_detail(client_id: str, _: str = Depends(verify_token)):
    """Детальная информация о клиенте с записями."""
    client = supabase.table("clients").select("*").eq(
        "id", client_id
    ).single().execute()
    if not client.data:
        raise HTTPException(status_code=404, detail="Client not found")

    recs = supabase.table("recordings").select(
        "*, employees!inner(name, role, directions)"
    ).eq("client_id", client_id).execute()

    recordings = []
    for r in recs.data:
        emp = r.get("employees", {})
        recordings.append(RecordingDetail(
            id=r["id"],
            employee_name=emp.get("name", ""),
            employee_role=emp.get("role", "teacher"),
            directions=emp.get("directions", []),
            transcription=r.get("transcription"),
            analysis=r.get("analysis"),
            score=r.get("score"),
            status=r["status"],
        ))

    return ClientDetail(
        id=client.data["id"],
        name=client.data["name"],
        city=client.data["city"],
        lesson_datetime=client.data["lesson_datetime"],
        result=client.data.get("result"),
        recordings=recordings,
    )
