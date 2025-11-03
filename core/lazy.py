from typing import Iterable, Iterator
from core.domain import Slot, Class, Room

def iter_free_slots_for_room(room_id: str, classes: Iterable[Class], slots: Iterable[Slot]) -> Iterable[Slot]:
    #Ленивая генерация свободных слотов для заданной аудитории.
    #Получаем множество занятых slot_id для данной аудитории
    occupied_slot_ids = {c.slot_id for c in classes if c.room_id == room_id and c.slot_id}

    #Ленивая фильтрация слотов (только те, что не заняты)
    for slot in slots:
        if slot.id not in occupied_slot_ids:
            yield slot

def iter_candidate_assignments(cls: Class, rooms: Iterable[Room], slots: Iterable[Slot]) -> Iterator[tuple[Room, Slot]]:
    #Ленивая генерация возможных пар (аудитория, слот) для данного класса.
    # Ленивый перебор всех комбинаций аудиторий и слотов
    for room in rooms:
        if cls.needs and cls.needs not in room.features:
            continue

        for slot in slots:
            yield (room, slot)