import pytest
from core.domain import Slot, Room, Class
from core.lazy import iter_free_slots_for_room, iter_candidate_assignments


#iter_free_slots_for_room
def test_free_slots_excludes_occupied():
    #Проверяет, что занятые слоты исключаются из результата
    slots = [
        Slot(id="MON1", day="monday", start="8:00", end="10:00"),
        Slot(id="MON2", day="monday", start="10:00", end="12:00"),
        Slot(id="MON3", day="monday", start="12:00", end="14:00"),
    ]
    classes = [
        Class(id="C1", course_id="IT101", needs="projector", teacher_id="T1",
              group_id="G1", slot_id="MON2", room_id="R01", status="scheduled")
    ]

    free = list(iter_free_slots_for_room("R01", classes, slots))
    free_ids = [s.id for s in free]

    assert free_ids == ["MON1", "MON3"]


def test_free_slots_all_free_when_no_classes():
    #Если занятий нет, должны вернуться все доступные слоты.
    slots = [
        Slot(id="TUE1", day="tuesday", start="8:00", end="10:00"),
        Slot(id="TUE2", day="tuesday", start="10:00", end="12:00"),
    ]
    classes = []

    result = list(iter_free_slots_for_room("R05", classes, slots))
    assert len(result) == 2
    assert all(isinstance(s, Slot) for s in result)


def test_free_slots_ignores_other_rooms():
    #Функция должна учитывать занятость только данной аудитории.
    slots = [
        Slot(id="FRI1", day="friday", start="8:00", end="10:00"),
        Slot(id="FRI2", day="friday", start="10:00", end="12:00"),
    ]
    classes = [
        Class(id="C1", course_id="EC101", needs="projector", teacher_id="T1",
              group_id="G1", slot_id="FRI2", room_id="R10", status="scheduled")
    ]

    #Проверяем другую аудиторию R11, она должна быть полностью свободна
    free = list(iter_free_slots_for_room("R11", classes, slots))
    free_ids = [s.id for s in free]
    assert free_ids == ["FRI1", "FRI2"]


#iter_candidate_assignments

def test_candidate_assignments_filters_by_needs():
    #Комбинации должны включать только аудитории, где есть нужная особенность
    cls = Class(id="C10", course_id="CH101", needs="lab", teacher_id="T03",
                group_id="G07", slot_id="", room_id="", status="planned")

    rooms = [
        Room(id="R03", building_id="B01", name="201", capacity=18, features=("lab",)),
        Room(id="R04", building_id="B01", name="202", capacity=45, features=("projector",)),
    ]
    slots = [
        Slot(id="MON1", day="monday", start="8:00", end="10:00"),
        Slot(id="MON2", day="monday", start="10:00", end="12:00"),
    ]

    pairs = list(iter_candidate_assignments(cls, rooms, slots))
    assert all("lab" in room.features for room, _ in pairs)
    assert len(pairs) == 2


def test_candidate_assignments_yields_all_combinations():
    #Если потребностей нет, функция должна вернуть все комбинации аудиторий и слотов
    cls = Class(id="C2", course_id="EC101", needs="", teacher_id="T02",
                group_id="G02", slot_id="", room_id="", status="planned")

    rooms = [
        Room(id="R01", building_id="B01", name="101", capacity=30, features=("none",)),
        Room(id="R02", building_id="B01", name="102", capacity=80, features=("gym",)),
    ]
    slots = [
        Slot(id="TUE1", day="tuesday", start="8:00", end="10:00"),
        Slot(id="TUE2", day="tuesday", start="10:00", end="12:00"),
    ]

    pairs = list(iter_candidate_assignments(cls, rooms, slots))
    assert len(pairs) == 4
    assert all(isinstance(p[0], Room) and isinstance(p[1], Slot) for p in pairs)


def test_candidate_assignments_lazy_iteration():
    #Проверка ленивости: генератор не должен материализовывать всё сразу
    cls = Class(id="C3", course_id="PE101", needs="gym", teacher_id="T01",
                group_id="G01", slot_id="", room_id="", status="planned")

    rooms = [
        Room(id="R02", building_id="B01", name="102", capacity=80, features=("gym",)),
    ]
    slots = [
        Slot(id=f"S{i}", day="mon", start="8:00", end="10:00") for i in range(10)
    ]

    gen = iter_candidate_assignments(cls, rooms, slots)
    first_pair = next(gen)
    assert isinstance(first_pair[0], Room)
    assert isinstance(first_pair[1], Slot)
    # Проверим, что генератор продолжает работать без ошибок
    next(gen)
