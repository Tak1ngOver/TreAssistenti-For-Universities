import pytest
from core.domain import *
from core.recursion import *

def test_by_day_returns_true():
    # Есть слот на понедельник
    slots = [
        Slot(id="MON1", day="monday", start="8:00", end="10:00"),
        Slot(id="TUE1", day="tuesday", start="8:00", end="10:00")
    ]

    # Пара, у которой slot_id совпадает с понедельничным
    c = Class(
        id="PE1",
        course_id="PE101",
        needs=("gym",),
        teacher_id="T01",
        group_id="G0105",
        slot_id="MON1",
        room_id="R02",
        status="scheduled"
    )

    func = by_day("monday")
    assert func(c, slots) is True


def test_by_day_returns_false():
    # Есть слоты, но день не совпадает
    slots = [
        Slot(id="MON1", day="monday", start="8:00", end="10:00"),
        Slot(id="TUE1", day="tuesday", start="8:00", end="10:00")
    ]

    # Пара имеет слот на вторник, а фильтр ищет понедельник
    c = Class(
        id="PE1",
        course_id="PE101",
        needs=("gym",),
        teacher_id="T01",
        group_id="G0105",
        slot_id="TUE1",
        room_id="R02",
        status="scheduled"
    )

    func = by_day("monday")
    assert func(c, slots) is False

####################################################################################################################################


def test_by_teacher_returns_true():
    c = Class(
        id="PE1",
        course_id="PE101",
        needs=("gym",),
        teacher_id="T01",
        group_id="G0105",
        slot_id="MON1",
        room_id="R02",
        status="scheduled"
    )

    func = by_teacher("T01")
    result = func(c)
    assert result is True
    assert c.teacher_id == "T01"


def test_by_teacher_returns_false():
    c = Class(
        id="PE1",
        course_id="PE101",
        needs=("gym",),
        teacher_id="T02",
        group_id="G0105",
        slot_id="MON1",
        room_id="R02",
        status="scheduled"
    )

    func = by_teacher("T01")
    result = func(c)
    assert result is False
    assert c.teacher_id == "T02"

################################################################################################################################



def test_by_group_returns_true():
    c = Class(
        id="PE1",
        course_id="PE101",
        needs=("gym",),
        teacher_id="T01",
        group_id="G0105",
        slot_id="MON1",
        room_id="R02",
        status="scheduled"
    )

    func = by_group("G0105")
    result = func(c)
    assert result is True
    assert c.group_id == "G0105"


def test_by_group_returns_false():
    c = Class(
        id="PE1",
        course_id="PE101",
        needs=("gym",),
        teacher_id="T01",
        group_id="G06",
        slot_id="MON1",
        room_id="R02",
        status="scheduled"
    )

    func = by_group("G0105")
    result = func(c)
    assert result is False
    assert c.group_id == "G06"

###################################################################################################################################

def test_by_building_returns_true():
    rooms = (
        Room(id="R01", building_id="B1", name="room 1", capacity=30, features=("projector",)),
        Room(id="R02", building_id="B2", name="room 2", capacity=25, features=("gym",))
    )

    c = Class(
        id="PE1",
        course_id="PE101",
        needs=("gym",),
        teacher_id="T01",
        group_id="G0105",
        slot_id="MON1",
        room_id="R01",
        status="scheduled"
    )

    func = by_building("B1", rooms)
    result = func(c)
    assert result is True
    assert c.room_id == "R01"


def test_by_building_returns_false():
    rooms = (
        Room(id="R01", building_id="B1", name="room 1", capacity=30, features=("projector",)),
        Room(id="R02", building_id="B2", name="room 2", capacity=25, features=("gym",)),
    )

    c = Class(
        id="PE2",
        course_id="PE102",
        needs=("lab",),
        teacher_id="T02",
        group_id="G0205",
        slot_id="TUE2",
        room_id="R02",
        status="scheduled"
    )

    func = by_building("B1", rooms)
    result = func(c)
    assert result is False
    assert c.room_id == "R02"

####################################################################################################################################

def test_nest_by_day_with_two_days():
    classes = (
        Class(
            id="PE1",
            course_id="PE101",
            needs=("gym",),
            teacher_id="T01",
            group_id="G0105",
            slot_id="MON1",
            room_id="R02",
            status="scheduled"
        ),
        Class(
            id="MATH1",
            course_id="MATH101",
            needs=("board",),
            teacher_id="T02",
            group_id="G0106",
            slot_id="TUE1",
            room_id="R03",
            status="scheduled"
        ),
    )

    slots = (
        Slot(id="MON1", day="Monday", start="08:00", end="10:00"),
        Slot(id="TUE1", day="Tuesday", start="08:00", end="10:00"),
    )

    result = nest_by_day(classes, slots)

    assert len(result) == 2
    assert result[0][0] == "Monday"
    assert len(result[0][1]) == 1
    assert result[0][1][0].id == "PE1"

    assert result[1][0] == "Tuesday"
    assert len(result[1][1]) == 1
    assert result[1][1][0].id == "MATH1"


def test_nest_by_day_empty_slots():
    classes = (
        Class(
            id="PE1",
            course_id="PE101",
            needs=("gym",),
            teacher_id="T01",
            group_id="G0105",
            slot_id="MON1",
            room_id="R02",
            status="scheduled"
        ),
    )

    slots = ()

    result = nest_by_day(classes, slots)

    assert result == ()

#####################################################################################################################################

def test_find_conflicts_recursive_with_conflict():
    classes = (
        Class(
            id="PE1",
            course_id="PE101",
            needs=("gym",),
            teacher_id="T01",
            group_id="G0105",
            slot_id="MON1",
            room_id="R02",
            status="scheduled"
        ),
        Class(
            id="PE2",
            course_id="PE102",
            needs=("gym",),
            teacher_id="T02",
            group_id="G0106",
            slot_id="MON1",
            room_id="R02",
            status="scheduled"
        ),
    )

    slots = (
        Slot(id="MON1", day="monday", start="08:00", end="09:00"),
    )

    result = find_conflicts_recursive(classes, slots)

    assert len(result) == 1
    assert result[0][0].id == "PE1"
    assert result[0][1].id == "PE2"
    assert result[0][0].room_id == result[0][1].room_id == "R02"


def test_find_conflicts_recursive_without_conflict():
    classes = (
        Class(
            id="PE1",
            course_id="PE101",
            needs=("gym",),
            teacher_id="T01",
            group_id="G0105",
            slot_id="MON1",
            room_id="R02",
            status="scheduled"
        ),
        Class(
            id="PE2",
            course_id="PE102",
            needs=("gym",),
            teacher_id="T02",
            group_id="G0106",
            slot_id="TUE1",
            room_id="R03",
            status="scheduled"
        ),
    )

    slots = (
        Slot(id="MON1", day="monday", start="08:00", end="09:00"),
        Slot(id="TUE1", day="tuesday", start="08:00", end="09:00"),
    )

    result = find_conflicts_recursive(classes, slots)

    assert result == ()






  