import pytest
from core.domain import Class, Group, Room
from core.transforms import add_class, assign_room, assign_slot, map_groups, total_room_capacity

#Тесты функции add_class
def test_add_class_to_empty_list():
    classes = ()
    new_class = Class(
        id="PE1",
        course_id="PE101", 
        needs=["gym"], 
        teacher_id="T01", 
        group_id="G0105", 
        slot_id="MON1", 
        room_id="R02", 
        status="scheduled"
    )
    result = add_class(classes, new_class)
    assert len(result) == 1
    assert result[0] == new_class
    assert result[0].id == "PE1"

def test_add_class_to_not_empty_list():
    existing_class = Class(
        id="PE1",
        course_id="PE101", 
        needs=["gym"], 
        teacher_id="T01", 
        group_id="G0105", 
        slot_id="MON1", 
        room_id="R02", 
        status="planned"
    )
    classes = (existing_class,)

    new_class = Class(
        id="ECON_LEC1",
        course_id="EC101", 
        needs=["lectorium"], 
        teacher_id="T12", 
        group_id="G0105", 
        slot_id="MON2", 
        room_id="LEC01", 
        status="scheduled"
    )
    result = add_class(classes, new_class)
    assert len(result) == 2
    assert existing_class in result
    assert new_class in result
    assert result[1].id == "ECON_LEC1"

#Тесты функции assign_room
def test_assign_room():
    class1 = Class(
        id="PSY_LEC1",
        course_id="PS101", 
        needs=["lectorium", "accessibility"], 
        teacher_id="T04", 
        group_id="G0105", 
        slot_id="TUE1", 
        room_id="", 
        status="planned"
    )
    class2 = Class(
        id="IT_LEC1",
        course_id="IT101", 
        needs=["lectorium"], 
        teacher_id="T05", 
        group_id="G0105", 
        slot_id="TUE2", 
        room_id="LEC02", 
        status="scheduled"
    )
    classes = (class1, class2)
    new_room_id = "LEC01"
    result = assign_room(classes, class1.id, new_room_id)
    assert len(result) == 2
    assert result[1].room_id == new_room_id
    assert result[1].id == class1.id
    assert result[1].course_id == class1.course_id
    assert result[1].needs == class1.needs
    assert result[1].teacher_id == class1.teacher_id
    assert result[1].slot_id == class1.slot_id
    assert result[1].status == class1.status
    assert result[0] == class2

def test_assign_room_to_already_assigned_class():
    class1 = Class(
        id="IT_LEC1",
        course_id="IT101", 
        needs=["lectorium"], 
        teacher_id="T05", 
        group_id="G0105", 
        slot_id="TUE2", 
        room_id="LEC02", 
        status="scheduled"
    )
    classes = (class1,)
    new_room_id = "LEC03"
    result = assign_room(classes, class1.id, new_room_id)
    assert len(result) == 1
    assert result[0].room_id == new_room_id
    assert result[0].id == class1.id

#Тесты функции assign_slot
def test_assign_slot():
    class1 = Class(
        id="THE_LEC1",
        course_id="GD101", 
        needs=["lectorium", "accessibility"], 
        teacher_id="T05", 
        group_id="G0105", 
        slot_id="", 
        room_id="LEC01", 
        status="planned"
    )
    class2 = Class(
        id="PH_LEC1",
        course_id="PH101", 
        needs=["lectorium"], 
        teacher_id="T11", 
        group_id="G0105", 
        slot_id="WED2", 
        room_id="LEC02", 
        status="scheduled"
    )
    classes = (class1, class2)
    new_slot_id = "WED1"
    result = assign_slot(classes, class1.id, new_slot_id)
    assert len(result) == 2
    assert result[1].slot_id == new_slot_id
    assert result[1].id == class1.id
    assert result[1].course_id == class1.course_id
    assert result[1].needs == class1.needs
    assert result[1].teacher_id == class1.teacher_id
    assert result[1].room_id == class1.room_id
    assert result[1].status == class1.status
    assert result[0] == class2

def test_assign_slot_to_already_assigned_class():
    class1 = Class(
        id="PH_LEC1",
        course_id="PH101", 
        needs=["lectorium"], 
        teacher_id="T11", 
        group_id="G0105", 
        slot_id="WED2", 
        room_id="LEC02", 
        status="scheduled"
    )
    classes = (class1,)
    new_slot_id = "WED3"
    result = assign_slot(classes, class1.id, new_slot_id)
    assert len(result) == 1
    assert result[0].slot_id == new_slot_id
    assert result[0].id == class1.id

#Тесты функции map_groups
def test_map_groups_plus_ten():
    group1 = Group(
        id="G01",
        name="Юристы 1",
        size=18,
        track="Юриспруденция"
    )
    group2 = Group(
        id="G0105",
        name="Поток юристов",
        size=68,
        track="Юриспруденция"
    )
    group3 = Group(
        id="G06",
        name="Артисты 1",
        size=14,
        track="Смешанные искусства"
    )
    group4 = Group(
        id="G0608",
        name="Поток артистов",
        size=39,
        track="Смешанные искусства"
    )
    groups = (group1, group2, group3, group4)

    def increase_size(group: Group) -> Group:
        return Group(
            id=group.id,
            name=group.name,
            size=group.size + 10,
            track=group.track
        )
    result = map_groups(groups, increase_size)
    assert len(result) == 4
    assert result[0].size == 28
    assert result[1].size == 78
    assert result[2].size == 24
    assert result[3].size == 49
        
    assert result[0].id == group1.id
    assert result[0].name == group1.name
    assert result[0].track == group1.track

def test_map_groups_if():
    group1 = Group(
        id="G01",
        name="Юристы 1",
        size=18,
        track="Юриспруденция"
    )
    group2 = Group(
        id="G0105",
        name="Поток юристов",
        size=68,
        track="Юриспруденция"
    )
    group3 = Group(
        id="G06",
        name="Артисты 1",
        size=14,
        track="Смешанные искусства"
    )
    group4 = Group(
        id="G0608",
        name="Поток артистов",
        size=39,
        track="Смешанные искусства"
    )
    groups = (group1, group2, group3, group4)

    def change_size(group: Group) -> Group:
        if group.size < 20:
            return Group(
                id=group.id,
                name=group.name,
                size=group.size + 5,
                track=group.track
            )
        else:
            return Group(
                id=group.id,
                name=group.name,
                size=group.size - 5,
                track=group.track
            )
    result = map_groups(groups, change_size)
    assert len(result) == 4
    assert result[0].size == 23
    assert result[1].size == 63
    assert result[2].size == 19
    assert result[3].size == 34
    assert result[0].id == group1.id
    assert result[0].name == group1.name
    assert result[0].track == group1.track

#Тесты функции total_room_capacity
def test_total_room_capacity():
    room1 = Room(
        id="R01",
        building_id="B01",
        name="101",
        capacity=30,
        features=["none"]
    )
    room2 = Room(
        id="R02",
        building_id="B01",
        name="102",
        capacity=80,
        features=["gym"]
    )
    room3 = Room(
        id="R03",
        building_id="B01",
        name="201",
        capacity=18,
        features=["lab"]
    )
    rooms = (room1, room2, room3)
    result = total_room_capacity(rooms)
    assert isinstance(result, int)
    assert result == 128

def test_total_room_capacity_no_rooms():
    rooms = ()
    result = total_room_capacity(rooms)
    assert isinstance(result, int)
    assert result == 0