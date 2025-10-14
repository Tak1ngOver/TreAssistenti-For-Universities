import pytest
import time
from core.domain import *
from core.memo import *


def test_empty_classes_returns_zero():
    res = compute_timetable_stats("k1", (), ())
    assert res == (("conflicts", 0), ("windows", 0))


def test_no_conflicts_no_windows():
    slots = (
        Slot(id="MON1", day="monday", start="8:00", end="10:00"),
        Slot(id="MON2", day="monday", start="10:00", end="12:00"),
    )
    classes = (
        Class(id="C1", course_id="X", needs=(), teacher_id="T1", group_id="G1", slot_id="MON1", room_id="R1", status=""),
        Class(id="C2", course_id="X", needs=(), teacher_id="T2", group_id="G2", slot_id="MON2", room_id="R2", status=""),
    )
    res = compute_timetable_stats("k2", classes, slots)
    assert res == (("conflicts", 0), ("windows", 0))


def test_conflict_and_window_detected():
    slots = (
        Slot(id="MON1", day="monday", start="8:00", end="10:00"),
        Slot(id="MON3", day="monday", start="12:00", end="14:00"),
    )
    classes = (
        Class(id="A", course_id="Y", needs=(), teacher_id="T1", group_id="G1", slot_id="MON1", room_id="R1", status=""),
        Class(id="B", course_id="Y", needs=(), teacher_id="T1", group_id="G2", slot_id="MON1", room_id="R2", status=""),
        Class(id="C", course_id="Y", needs=(), teacher_id="T3", group_id="G1", slot_id="MON3", room_id="R3", status=""),
    )
    res = compute_timetable_stats("k3", classes, slots)
    assert res == (("conflicts", 1), ("windows", 1))


def test_measure_cache_performance_reads_json():
    measure_cache_performance()  # просто должен выполниться без ошибок


def test_compute_timetable_stats_cache_speed():
    slots = (
        Slot(id="MON1", day="monday", start="8:00", end="10:00"),
    )
    classes = (
        Class(id="C1", course_id="X", needs=(), teacher_id="T1", group_id="G1", slot_id="MON1", room_id="R1", status=""),
    )
    compute_timetable_stats.cache_clear()

    start = time.perf_counter()
    compute_timetable_stats("cached_run", classes, slots)
    t1 = time.perf_counter() - start

    start = time.perf_counter()
    compute_timetable_stats("cached_run", classes, slots)
    t2 = time.perf_counter() - start

    assert t2 < t1
