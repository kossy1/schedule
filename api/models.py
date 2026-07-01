from pydantic import BaseModel
from typing import List, Optional

class Course(BaseModel):
    id: str
    name: str
    lecturer: str
    semester: int

class Timetable(BaseModel):
    schedule: List[dict]  # List of {course_id, lecturer, day, time, venue}
    fitness_score: float
    conflicts_resolved: int