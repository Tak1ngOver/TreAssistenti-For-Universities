import pytest
from core.compose import compose, pipe
from core.service import (
    TimetableService,
    DayReport,
    validate_day,
    select_slots_for_day,
    select_classes_for_slots,
    enrich_classes,
    summarize_day
)

# небольшой набор фиктивных данных (subset of seed.json)
SLOTS = [
    {"id":"MON1", "day":"monday", "start":"8:00", "end":"10:00"},
    {"id":"MON2", "day":"monday", "start":"10:00", "end":"12:00"},
    {"id":"TUE1", "day":"tuesday", "start":"8:00", "end":"10:00"},
]

CLASSES = [
    {"id":"A", "course_id":"PE101", "teacher_id":"T01", "group_id":"G01", "slot_id":"MON1", "room_id":"R02", "status":""},
    {"id":"B", "course_id":"EC101", "teacher_id":"T12", "group_id":"G02", "slot_id":"MON2", "room_id":"", "status":""},
    {"id":"C", "course_id":"IT101", "teacher_id":"T10", "group_id":"G03", "slot_id":"TUE1", "room_id":"R13", "status":""},
    {"id":"D", "course_id":"PH101", "teacher_id":"", "group_id":"G04", "slot_id":"", "room_id":"", "status":""},  # unscheduled
]

ROOMS = [
    {"id":"R02","name":"102"},
    {"id":"R13","name":"102-B"},
]

COURSES = [
    {"code":"PE101","title":"Физическая культура"},
    {"code":"EC101","title":"Экономика"},
    {"code":"IT101","title":"Инфотех"},
]

TEACHERS = [
    {"id":"T01","name":"T One"},
    {"id":"T12","name":"T Twelve"},
    {"id":"T10","name":"T Ten"},
]

DATA = {
    "slots": SLOTS,
    "classes": CLASSES,
    "rooms": ROOMS,
    "courses": COURSES,
    "teachers": TEACHERS
}

def test_compose_order():
    def f(x): return x + "f"
    def g(x): return x + "g"
    def h(x): return x + "h"
    c = compose(f, g, h)
    assert c("X") == "X" + "h" + "g" + "f"  # f(g(h(X)))

def test_compose_identity():
    idf = compose()
    assert idf("test") == "test"

def test_pipe_basic():
    def a(x): return x + 1
    def b(x): return x * 2
    out = pipe(3, a, b)  # (3+1)*2 = 8
    assert out == 8

def test_build_day_report_mon():
    validators = {"validate_day": validate_day}
    selectors = {
        "select_slots_for_day": select_slots_for_day,
        "select_classes_for_slots": select_classes_for_slots
    }
    calculators = {"enrich_classes": enrich_classes, "summarize_day": summarize_day}

    svc = TimetableService(validators, selectors, calculators, DATA)
    report = svc.build_day_report("monday")
    assert isinstance(report, DayReport)
    # slots for monday -> 2
    assert len(report.slots) == 2
    # classes scheduled on monday -> 2 (A and B)
    assert report.summary["classes_count"] == 2
    # stages must include 'validated_day' and 'summary'
    names = [name for name, _ in report.stages]
    assert "validated_day" in names and "summary" in names

def test_invalid_day_raises():
    validators = {"validate_day": validate_day}
    selectors = {
        "select_slots_for_day": select_slots_for_day,
        "select_classes_for_slots": select_classes_for_slots
    }
    calculators = {"enrich_classes": enrich_classes, "summarize_day": summarize_day}
    svc = TimetableService(validators, selectors, calculators, DATA)
    with pytest.raises(ValueError):
        # validate_day should raise ValueError
        svc.build_day_report("saturday")
