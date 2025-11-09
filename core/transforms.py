# Чистые трансформации.
# Авторы: Демид Метельников

import json
from typing import Tuple, Callable
from dataclasses import asdict
from functools import reduce
from core.domain import *

def to_tuple(type, items):
    return tuple(type(**it) for it in items)

def serialize_tuple(t):
        return [asdict(x) for x in t]

def load_seed(path: str) -> tuple[
    tuple[Building,...], tuple[Room,...], tuple[Teacher,...],  tuple[Group,...], 
    tuple[Course,...], tuple[Slot,...],  tuple[Class,...], tuple[Constraint,...]
    ]:
    f = open(path, "r+", encoding="UTF-8")
    data = json.load(f)
    buildings = to_tuple(Building, data.get("buildings", []))
    rooms = to_tuple(Room, data.get("rooms", []))
    teachers = to_tuple(Teacher, data.get("teachers", []))
    groups = to_tuple(Group, data.get("groups", []))
    courses = to_tuple(Course, data.get("courses", []))
    slots = to_tuple(Slot, data.get("slots", []))
    classes = to_tuple(Class, data.get("classes", []))
    constraints = to_tuple(Constraint, data.get("constraints", []))
    f.close()
    return buildings, rooms, teachers, groups, courses, slots, classes, constraints

def add_class(classes: tuple[Class,...], c: Class) -> tuple[Class,...]:
    if not isinstance(classes[0], Class):
        classes = to_tuple(Class, classes)
    if not isinstance(c, Class):
        c = Class(**c)
    new_classes = classes + (c,)
    return new_classes

def assign_room(classes: tuple[Class,...], class_id:str, new_room_id:str) -> tuple[Class,...]:
    if classes and not isinstance(classes[0], Class):
        classes = to_tuple(Class, classes)
    check_room = lambda c: True if c.id == class_id else False
    no_room = lambda c: False if c.id == class_id else True
    needed_class = tuple(filter(check_room, classes))
    if(len(needed_class) != 1):
       # print("Ошибка в данных: несколько занятий с указанным ID")
        return classes
    for i in needed_class:
        updated_class = Class(id=i.id, course_id=i.course_id, needs=i.needs, teacher_id= i.teacher_id, group_id = i.group_id, slot_id = i.slot_id, room_id=new_room_id, status=i.status)
    new_classes = tuple(filter(no_room, classes))
    return new_classes + (updated_class,)

def assign_slot(classes: tuple[Class,...], class_id:str, new_slot_id:str) -> tuple[Class,...]:
    if classes and not isinstance(classes[0], Class):
        classes = to_tuple(Class, classes)
    check_room = lambda c: True if c.id == class_id else False
    no_room = lambda c: False if c.id == class_id else True
    needed_class = tuple(filter(check_room, classes))
    if(len(needed_class) != 1):
        #print("Ошибка в данных: несколько занятий с указанным ID")
        return classes
    for i in needed_class:
        updated_class = Class(id=i.id, course_id=i.course_id, needs=i.needs, teacher_id= i.teacher_id, group_id = i.group_id, slot_id = new_slot_id, room_id=i.room_id, status=i.status)
    new_classes = tuple(filter(no_room, classes))
    return new_classes + (updated_class,)

def map_groups(groups: tuple[Group,...], f: Callable[[Group], Group]) -> tuple[Group,...]:
    new_groups = []
    for g in groups:
        mapped_group = f(g)
        new_groups.append(mapped_group)
    return tuple(new_groups)

def total_room_capacity(rooms: tuple[Room,...]) -> int:
    if not rooms:
        return 0
    if not isinstance(rooms[0], Room):
        rooms = to_tuple(Room, rooms)
    capacities = map(lambda r: r.capacity, rooms)
    sum = reduce(lambda a, b: a + b, capacities)
    return int(sum)