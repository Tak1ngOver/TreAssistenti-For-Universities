# core/service.py
from dataclasses import dataclass
from typing import Callable, Tuple, Dict, Any, Iterable
from core.compose import compose, pipe

@dataclass(frozen=True)
class DayReport:
    day: str
    slots: Tuple[dict, ...]
    classes: Tuple[dict, ...]
    summary: Dict[str, Any]
    stages: Tuple[Any, ...]  # промежуточные результаты (для UI)

class TimetableService:
    """
    Фасад (без бизнес-логики). Конструируется с набором чистых функций (DI).
    validators: dict[str, Callable]
    selectors: dict[str, Callable]
    calculators: dict[str, Callable]

    data: словарь исходных коллекций (slots, classes, rooms, teachers, groups, courses)
    """

    def __init__(self, validators: Dict[str, Callable], selectors: Dict[str, Callable],
                 calculators: Dict[str, Callable], data: Dict[str, Iterable]):
        self.validators = validators
        self.selectors = selectors
        self.calculators = calculators
        self.data = data

    def build_day_report(self, day: str) -> DayReport:
        """
        Собирает DayReport как pipeline чистых функций.
        Возвращаемые промежуточные значения собираются в stages (tuple).
        """
        stages = []

        # 1. validate day
        validate_day = self.validators.get("validate_day")
        if validate_day is None:
            raise RuntimeError("Validator 'validate_day' not provided")
        validated = validate_day(day)
        stages.append(("validated_day", validated))

        # 2. select slots for the day
        select_slots = self.selectors.get("select_slots_for_day")
        if select_slots is None:
            raise RuntimeError("Selector 'select_slots_for_day' not provided")
        slots = tuple(select_slots(self.data.get("slots", ()), day))
        stages.append(("slots", slots))

        # 3. select classes scheduled into these slots (pure selector)
        select_classes = self.selectors.get("select_classes_for_slots")
        if select_classes is None:
            raise RuntimeError("Selector 'select_classes_for_slots' not provided")
        classes = tuple(select_classes(self.data.get("classes", ()), slots))
        stages.append(("classes", classes))

        # 4. enrich classes with room/course/teacher names if calculators provided
        enrich = self.calculators.get("enrich_classes")
        if enrich:
            enriched_classes = tuple(enrich(classes, self.data))
        else:
            enriched_classes = classes
        stages.append(("enriched_classes", enriched_classes))

        # 5. calculate summary (load, room utilization, teacher load)
        summarize = self.calculators.get("summarize_day")
        if summarize:
            summary = summarize(enriched_classes, slots, self.data)
        else:
            summary = {}
        stages.append(("summary", summary))

        report = DayReport(
            day=day,
            slots=slots,
            classes=enriched_classes,
            summary=summary,
            stages=tuple(stages)
        )
        return report

# ---- Примеры простых чистых функций, которые можно передать через DI ----
# Эти функции сделаны чистыми и простыми, чтобы их легко тестировать и комбинировать.

def validate_day(day: str) -> str:
    allowed = {"monday","tuesday","wednesday","thursday","friday"}
    d = (day or "").lower()
    if d not in allowed:
        raise ValueError(f"Invalid day: {day!r}")
    return d

def select_slots_for_day(slots: Iterable[dict], day: str) -> Iterable[dict]:
    for s in slots:
        if s.get("day","").lower() == day.lower():
            yield s

def select_classes_for_slots(classes: Iterable[dict], slots: Iterable[dict]) -> Iterable[dict]:
    slot_ids = {s["id"] for s in slots}
    for c in classes:
        # class may have empty slot_id -> treat as unscheduled (skip)
        sid = c.get("slot_id") or ""
        if sid in slot_ids:
            yield c

def enrich_classes(classes: Iterable[dict], data: dict) -> Iterable[dict]:
    # добавим human-readable поля: room_name, course_title, teacher_name
    rooms = {r["id"]: r for r in data.get("rooms", ())}
    courses = {c["code"]: c for c in data.get("courses", ())}
    teachers = {t["id"]: t for t in data.get("teachers", ())}

    for cl in classes:
        room = rooms.get(cl.get("room_id")) or {}
        course = courses.get(cl.get("course_id")) or {}
        teacher = teachers.get(cl.get("teacher_id")) or {}
        enriched = dict(cl)  # shallow copy
        enriched["room_name"] = room.get("name", "")
        enriched["course_title"] = course.get("title", "")
        enriched["teacher_name"] = teacher.get("name", "")
        yield enriched

def summarize_day(classes: Iterable[dict], slots: Iterable[dict], data: dict) -> dict:
    # простая сводка: число слотов, число занятых слотов, load per teacher
    slots_count = len(tuple(slots))
    occupied = len(tuple({c["slot_id"] for c in classes if c.get("slot_id")}))
    teacher_load = {}
    for c in classes:
        tid = c.get("teacher_id") or "UNASSIGNED"
        teacher_load[tid] = teacher_load.get(tid, 0) + 1
    return {
        "slots_total": slots_count,
        "slots_occupied": occupied,
        "classes_count": len(tuple(classes)),
        "teacher_load": teacher_load
    }