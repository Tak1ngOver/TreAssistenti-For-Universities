# tests/test_async_schedule_fixed.py
import pytest
import asyncio

from core.domain import Room, Slot, Group, Class
from core.async_schedule import (
    _room_matches_needs,
    _group_size_ok,
    _find_slot_room_combination,
    schedule_batch,
    generate_period_report,
)

pytestmark = pytest.mark.asyncio


# ---- factories ----
def mk_room(id="R1", building_id="B1", name="101", capacity=20, features=None):
    if features is None:
        features = ("none",)
    # ensure tuple for features
    return Room(id=id, building_id=building_id, name=name, capacity=capacity, features=tuple(features))


def mk_slot(id="S1", day="monday", start="8:00", end="10:00"):
    return Slot(id=id, day=day, start=start, end=end)


def mk_group(id="G1", name="G1", size=18, track="t"):
    return Group(id=id, name=name, size=size, track=track)


def mk_class(
    id="C1",
    course_id="X",
    needs="",
    teacher_id="T1",
    group_id="G1",
    slot_id="",
    room_id="",
    status="planned",
):
    return Class(
        id=id,
        course_id=course_id,
        needs=needs,
        teacher_id=teacher_id,
        group_id=group_id,
        slot_id=slot_id,
        room_id=room_id,
        status=status,
    )


# ---- tests for helpers ----
def test_room_matches_needs_exact_and_partial():
    r = mk_room(features=("projector", "lectoruim"))
    # string need that matches partially (lectoruim ~ lectorium)
    assert _room_matches_needs(r, "projector") is True
    assert _room_matches_needs(r, "lectoruim") is True
    # need that doesn't match
    assert _room_matches_needs(r, "lab") is False
    # empty need should pass
    assert _room_matches_needs(r, "") is True
    # list of needs - all must be satisfied
    assert _room_matches_needs(r, ["projector", "lectoruim"]) is True
    assert _room_matches_needs(r, ["projector", "lab"]) is False


def test_group_size_ok_true_and_false():
    r_small = mk_room(capacity=10)
    r_big = mk_room(capacity=50)
    g = mk_group(size=20)
    assert _group_size_ok(r_big, g) is True
    assert _group_size_ok(r_small, g) is False


def test_find_slot_room_combination_finds_first_valid():
    rooms = (mk_room(id="R1", capacity=30, features=("projector",)), mk_room(id="R2", capacity=10, features=("lab",)))
    slots = (mk_slot(id="MON1", day="monday"), mk_slot(id="MON2", day="monday"))
    group = mk_group(id="G1", size=25)
    # class needs projector so first room qualifies and MON1 is first slot
    c = mk_class(id="CL1", needs="projector", group_id="G1")
    slot_id, room_id = _find_slot_room_combination(c, (group,), slots, rooms, set())
    assert slot_id == "MON1"
    assert room_id == "R1"

    # if R1 taken -> should pick next room/slot or fail
    taken = {("MON1", "R1")}
    slot_id2, room_id2 = _find_slot_room_combination(c, (group,), slots, rooms, taken)
    # R1 at MON1 is taken, but R1 at MON2 is free -> algorithm checks slots in order then rooms
    # so it should pick MON2,R1 because slot MON2 + room R1 is free
    assert slot_id2 is not None and room_id2 is not None


# ---- tests for schedule_batch ----
async def test_schedule_assigns_slot_and_room_when_available():
    rooms = (mk_room(id="R01", capacity=40, features=("projector", "lectoruim")),)
    slots = (mk_slot(id="MON1", day="monday"),)
    group = mk_group(id="G1", size=30)
    classes = (mk_class(id="L1", needs="lectoruim", teacher_id="T1", group_id="G1"),)
    res = await schedule_batch("monday", classes, rooms, slots, (group,))
    updated = res["classes"]
    rpt = res["report"]
    assert len(updated) == 1
    assert updated[0].slot_id == "MON1"
    assert updated[0].room_id == "R01"
    assert updated[0].status == "scheduled"
    assert rpt["assigned_this_run"] == 1
    assert rpt["unscheduled_count"] == 0


async def test_schedule_respects_capacity_and_features():
    # room without required feature and insufficient capacity
    rooms = (mk_room(id="R01", capacity=10, features=("none",)),)
    slots = (mk_slot(id="MON1", day="monday"),)
    group = mk_group(id="G1", size=18)
    classes = (mk_class(id="C1", needs="projector", teacher_id="T1", group_id="G1"),)
    res = await schedule_batch("monday", classes, rooms, slots, (group,))
    updated = res["classes"]
    assert updated[0].slot_id == ""  # not assigned
    assert res["report"]["assigned_this_run"] == 0
    assert res["report"]["unscheduled_count"] == 1


async def test_schedule_preserves_already_scheduled_and_does_not_reassign():
    rooms = (mk_room(id="R1", capacity=50, features=("projector",)),)
    slots = (mk_slot(id="MON1", day="monday"),)
    group = mk_group(id="G1", size=10)
    class1 = mk_class(id="S1", needs="projector", teacher_id="T1", group_id="G1", slot_id="MON1", room_id="R1", status="scheduled")
    classes = (class1,)
    res = await schedule_batch("monday", classes, rooms, slots, (group,))
    # scheduled_count counts classes that have slot+room
    assert res["report"]["scheduled_count"] == 1
    assert res["report"]["assigned_this_run"] == 0  # nothing newly assigned


async def test_schedule_avoids_teacher_conflict():
    # teacher T1 already has a scheduled class at MON1
    rooms = (mk_room(id="R1", capacity=50, features=("projector",)), mk_room(id="R2", capacity=50, features=("projector",)))
    slots = (mk_slot(id="MON1", day="monday"), mk_slot(id="MON2", day="monday"))
    g1 = mk_group(id="G1", size=10)
    g2 = mk_group(id="G2", size=10)
    class1 = mk_class(id="A", needs="projector", teacher_id="T1", group_id="G1", slot_id="MON1", room_id="R1", status="scheduled")
    class2 = mk_class(id="B", needs="projector", teacher_id="T1", group_id="G2")
    classes = (class1, class2)
    res = await schedule_batch("monday", classes, rooms, slots, (g1, g2))
    updated = {c.id: c for c in res["classes"]}
    assert updated["A"].slot_id == "MON1"
    # B must not be assigned to MON1 because teacher conflict; it may be assigned to MON2 or left unassigned
    assert not (updated["B"].slot_id == "MON1" and updated["B"].teacher_id == "T1")


async def test_schedule_avoids_room_double_assignment_and_reports_proper_counts():
    rooms = (mk_room(id="R01", capacity=30, features=("projector",)),)
    slots = (mk_slot(id="MON1", day="monday"),)
    g1 = mk_group(id="G1", size=10)
    g2 = mk_group(id="G2", size=10)
    class1 = mk_class(id="A", needs="projector", teacher_id="T1", group_id="G1")
    class2 = mk_class(id="B", needs="projector", teacher_id="T2", group_id="G2")
    classes = (class1, class2)
    res = await schedule_batch("monday", classes, rooms, slots, (g1, g2))
    # at most one assigned because only one (slot,room) exists
    assert res["report"]["assigned_this_run"] <= 1
    # collisions list should be empty (algorithm avoids double-assign)
    assert res["report"]["collisions"] == []


# ---- tests for generate_period_report ----
async def test_generate_period_report_aggregates_across_days():
    rooms = (
        mk_room(id="R01", capacity=30, features=("projector",)),
        mk_room(id="R02", capacity=30, features=("lab",)),
    )
    slots = (
        mk_slot(id="MON1", day="monday"),
        mk_slot(id="TUE1", day="tuesday"),
    )
    group = mk_group(id="G1", size=20)
    classes = (
        mk_class(id="C1", needs="projector", teacher_id="T1", group_id="G1"),
        mk_class(id="C2", needs="lab", teacher_id="T2", group_id="G1"),
    )
    res = await generate_period_report(["monday", "tuesday"], classes, rooms, slots, (group,))
    assert "days" in res and "aggregated" in res
    assert res["aggregated"]["total_days"] == 2
    # aggregated sums must be integers and non-negative
    assert isinstance(res["aggregated"]["total_assigned_this_run"], int)
    assert res["aggregated"]["total_assigned_this_run"] >= 0
