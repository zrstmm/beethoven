from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Optional


class EmployeeRole(str, Enum):
    teacher = "teacher"
    sales_manager = "sales_manager"


class City(str, Enum):
    astana = "astana"
    ust_kamenogorsk = "ust_kamenogorsk"


class Direction(str, Enum):
    guitar = "guitar"
    piano = "piano"
    vocal = "vocal"
    dombra = "dombra"


class ClientResult(str, Enum):
    bought = "bought"
    not_bought = "not_bought"
    prepayment = "prepayment"


class RecordingStatus(str, Enum):
    pending = "pending"
    transcribing = "transcribing"
    analyzing = "analyzing"
    done = "done"
    error = "error"


# --- Employee ---

class EmployeeCreate(BaseModel):
    telegram_id: int
    name: str
    role: EmployeeRole
    city: City
    directions: list[Direction] = []


class EmployeeOut(BaseModel):
    id: str
    telegram_id: int
    name: str
    role: EmployeeRole
    city: City
    directions: list[str]
    created_at: datetime


# --- Recording ---

class RecordingCreate(BaseModel):
    employee_telegram_id: int
    client_name: str
    lesson_datetime: str  # "DD.MM.YYYY HH:MM"
    result: Optional[ClientResult] = None
    city: City


class RecordingOut(BaseModel):
    id: str
    client_id: str
    employee_id: str
    audio_path: Optional[str] = None
    transcription: Optional[str] = None
    analysis: Optional[str] = None
    score: Optional[int] = None
    status: RecordingStatus
    created_at: datetime


class RecordingStatusOut(BaseModel):
    id: str
    status: RecordingStatus


# --- Client ---

class ClientCard(BaseModel):
    id: str
    name: str
    city: City
    lesson_datetime: datetime
    result: Optional[ClientResult] = None
    teacher_name: Optional[str] = None
    manager_name: Optional[str] = None
    teacher_score: Optional[int] = None
    manager_score: Optional[int] = None
    teacher_status: Optional[RecordingStatus] = None
    manager_status: Optional[RecordingStatus] = None


class RecordingDetail(BaseModel):
    id: str
    employee_name: str
    employee_role: EmployeeRole
    directions: list[str] = []
    transcription: Optional[str] = None
    analysis: Optional[str] = None
    score: Optional[int] = None
    status: RecordingStatus


class ClientDetail(BaseModel):
    id: str
    name: str
    city: City
    lesson_datetime: datetime
    result: Optional[ClientResult] = None
    recordings: list[RecordingDetail] = []


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    lesson_datetime: Optional[str] = None
    result: Optional[ClientResult] = None


# --- Auth ---

class LoginRequest(BaseModel):
    password: str


class TokenOut(BaseModel):
    token: str


# --- Settings ---

class SettingUpdate(BaseModel):
    value: str


class SettingOut(BaseModel):
    key: str
    value: str
    updated_at: datetime


# --- Analytics ---

class ConversionStats(BaseModel):
    bought: int
    not_bought: int
    prepayment: int
    total: int


class TopRecording(BaseModel):
    client_name: str
    client_id: str
    employee_name: str
    score: int
    result: Optional[ClientResult] = None
    lesson_datetime: datetime


class EmployeePerformance(BaseModel):
    employee_name: str
    role: EmployeeRole
    avg_score: float
    recording_count: int


class DirectionBreakdown(BaseModel):
    direction: str
    client_count: int
    bought: int
    not_bought: int
    prepayment: int
    avg_score: float


class WeeklyTrend(BaseModel):
    week_start: str
    total: int
    bought: int
    not_bought: int
    prepayment: int
    conversion_rate: float


class ScoreDistribution(BaseModel):
    score: int
    count: int


class AnalyticsOut(BaseModel):
    conversion: ConversionStats
    top_best: list[TopRecording]
    top_worst: list[TopRecording]
    common_mistakes: list[str]
    employee_performance: list[EmployeePerformance] = []
    direction_breakdown: list[DirectionBreakdown] = []
    weekly_trends: list[WeeklyTrend] = []
    score_distribution: list[ScoreDistribution] = []
