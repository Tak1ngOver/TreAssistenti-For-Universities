from core.domain import Room, Class, Group, Slot
from core.ftypes import Maybe, Just, Nothing, Either, Right, Left, safe_room, validate_assignment

# Тесты для Maybe / Just / Nothing

def test_just_map():
    value = Just(5)
    result = value.map(lambda x: x + 3)
    assert isinstance(result, Just)
    assert result.value == 8

def test_nothing_map():
    nothing = Nothing()
    result = nothing.map(lambda x: x + 3)
    assert isinstance(result, Nothing)
    assert result.get_or_else(99) == 99

def test_just_bind():
    value = Just(10)
    result = value.bind(lambda x: Just(x * 2))
    assert isinstance(result, Just)
    assert result.value == 20

def test_nothing_bind():
    nothing = Nothing()
    result = nothing.bind(lambda x: Just(x * 2))
    assert isinstance(result, Nothing)

def test_just_get_or_else():
    value = Just("ok")
    assert value.get_or_else("fallback") == "ok"

def test_nothing_get_or_else():
    nothing = Nothing()
    assert nothing.get_or_else("fallback") == "fallback"

# Тесты для Either / Right / Left

def test_right_map():
    r = Right(4)
    result = r.map(lambda x: x + 6)
    assert isinstance(result, Right)
    assert result.value == 10

def test_left_map_does_not_apply_function():
    l = Left({"error": "wrong"})
    result = l.map(lambda x: x + 6)
    assert isinstance(result, Left)
    assert result.error == {"error": "wrong"}

def test_right_bind():
    r = Right(10)
    result = r.bind(lambda x: Right(x * 3))
    assert isinstance(result, Right)
    assert result.value == 30

def test_left_bind_ignored():
    l = Left("err")
    result = l.bind(lambda x: Right(x * 2))
    assert isinstance(result, Left)
    assert result.error == "err"

def test_right_get_or_else():
    r = Right("ok")
    assert r.get_or_else("fallback") == "ok"

def test_left_get_or_else():
    l = Left("error")
    assert l.get_or_else("fallback") == "fallback"

# Тесты для safe_room

def test_safe_room_found():
    room1 = Room(id="R01", building_id="B01", name="101", capacity=30, features=["projector"])
    room2 = Room(id="R02", building_id="B01", name="102", capacity=40, features=["gym"])
    rooms = (room1, room2)
    result = safe_room(rooms, "R02")
    assert isinstance(result, Just)
    assert result.value == room2

def test_safe_room_not_found():
    room1 = Room(id="R01", building_id="B01", name="101", capacity=30, features=["projector"])
    rooms = (room1,)
    result = safe_room(rooms, "R99")
    assert isinstance(result, Nothing)
    assert result.get_or_else("none") == "none"

# Тесты для validate_assignment

def make_base_entities():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["projector", "accessibility"])
    group = Group(id="G01", name="Юристы 1", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    return room, group, slot

def test_validate_assignment_all_correct():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["projector", "accessibility"])
    group = Group(id="G01", name="Юристы 1", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    cls = Class(id="C01", course_id="LGL101", needs="projector", teacher_id="T01",
    group_id="G01", slot_id="MON1", room_id="R01", status="")
    result = validate_assignment((cls,), (room,), (slot,), (group,), cls)
    assert isinstance(result, Right)
    assert result.value == cls

def test_validate_assignment_missing_slot():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["projector", "accessibility"])
    group = Group(id="G01", name="Юристы 1", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    cls = Class(id="C02", course_id="LGL101", needs="projector", teacher_id="T01",
    group_id="G01", slot_id="", room_id="R01", status="")
    result = validate_assignment((), (room,), (slot,), (group,), cls)
    assert isinstance(result, Left)
    assert "slot" in result.error

def test_validate_assignment_room_not_found():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["projector", "accessibility"])
    group = Group(id="G01", name="Юристы 1", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    cls = Class(id="C03", course_id="LGL101", needs="projector", teacher_id="T01",
    group_id="G01", slot_id="MON1", room_id="R99", status="")
    result = validate_assignment((), (room,), (slot,), (group,), cls)
    assert isinstance(result, Left)
    assert "room" in result.error

def test_validate_assignment_group_not_found():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["projector", "accessibility"])
    group = Group(id="G01", name="Юристы 1", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    cls = Class(id="C04", course_id="LGL101", needs="projector", teacher_id="T01",
    group_id="G99", slot_id="MON1", room_id="R01", status="")
    result = validate_assignment((), (room,), (slot,), (group,), cls)
    assert isinstance(result, Left)
    assert "group" in result.error

def test_validate_assignment_capacity_too_small():
    room = Room(id="R01", building_id="B01", name="101", capacity=10, features=["projector"])
    group = Group(id="G01", name="Юристы", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    cls = Class(id="C05", course_id="LGL101", needs="projector", teacher_id="T01",
    group_id="G01", slot_id="MON1", room_id="R01", status="")
    result = validate_assignment((), (room,), (slot,), (group,), cls)
    assert isinstance(result, Left)
    assert "capacity" in result.error

def test_validate_assignment_feature_not_fit():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["lab"])
    group = Group(id="G01", name="Юристы", size=20, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    cls = Class(id="C06", course_id="LGL101", needs="projector", teacher_id="T01",
    group_id="G01", slot_id="MON1", room_id="R01", status="")
    result = validate_assignment((), (room,), (slot,), (group,), cls)
    assert isinstance(result, Left)
    assert "features" in result.error

def test_validate_assignment_collision_room():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["projector", "accessibility"])
    group = Group(id="G01", name="Юристы 1", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    other = Class(id="X1", course_id="EC101", needs="", teacher_id="T02",
    group_id="G02", slot_id="MON1", room_id="R01", status="")
    cls = Class(id="C07", course_id="LGL101", needs="", teacher_id="T01",
    group_id="G01", slot_id="MON1", room_id="R01", status="")
    result = validate_assignment((other,), (room,), (slot,), (group,), cls)
    assert isinstance(result, Left)
    assert "collision_room" in result.error

def test_validate_assignment_collision_teacher():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["projector", "accessibility"])
    group = Group(id="G01", name="Юристы 1", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    other = Class(id="X2", course_id="EC101", needs="", teacher_id="T01",
    group_id="G02", slot_id="MON1", room_id="R02", status="")
    cls = Class(id="C08", course_id="LGL101", needs="", teacher_id="T01",
    group_id="G01", slot_id="MON1", room_id="R01", status="")
    result = validate_assignment((other,), (room,), (slot,), (group,), cls)
    assert isinstance(result, Left)
    assert "collision_teacher" in result.error

def test_validate_assignment_collision_group():
    room = Room(id="R01", building_id="B01", name="101", capacity=40, features=["projector", "accessibility"])
    group = Group(id="G01", name="Юристы 1", size=30, track="Юриспруденция")
    slot = Slot(id="MON1", day="monday", start="8:00", end="10:00")
    other = Class(id="X3", course_id="EC101", needs="", teacher_id="T02",
    group_id="G01", slot_id="MON1", room_id="R02", status="")
    cls = Class(id="C09", course_id="LGL101", needs="", teacher_id="T01",
    group_id="G01", slot_id="MON1", room_id="R01", status="")
    result = validate_assignment((other,), (room,), (slot,), (group,), cls)
    assert isinstance(result, Left)
    assert "collision_group" in result.error
