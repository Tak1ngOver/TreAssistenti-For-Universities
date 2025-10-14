from core.domain import Class, Slot, Room

#Замыкания-предикаты

#Предикат для фильтрации занятий по дню недели
def by_day(day: str):
    return lambda c, slots: any(s.id == c.slot_id and s.day == day for s in slots)

#Предикат по преподавателю
def by_teacher(tid: str):
    return lambda c: c.teacher_id == tid

#Предикат по группе
def by_group(gid: str):
    return lambda c: c.group_id == gid

#Предикат для Class, проверяющий, находится ли аудитория занятия в указанном корпусе
def by_building(bid: str, rooms: tuple[Room, ...]):
    room_ids = tuple(r.id for r in rooms if r.building_id == bid)
    return lambda c: c.room_id in room_ids

#Группирует занятия по дням недели. Возвращает кортеж (день, занятия за день)
def nest_by_day(classes: tuple[Class, ...], slots: tuple[Slot, ...]) -> tuple[tuple[str, tuple[Class, ...]], ...]:
    if not slots:
        return ()

    first_day = slots[0].day
    day_slots = tuple(s for s in slots if s.day == first_day)
    rest_slots = tuple(s for s in slots if s.day != first_day)

    day_slot_ids = tuple(s.id for s in day_slots)
    day_classes = tuple(c for c in classes if c.slot_id in day_slot_ids)

    return ((first_day, day_classes),) + nest_by_day(classes, rest_slots)

#Рекурсивно ищет конфликты - занятия, у которых одинаковый слот и аудитория. Возвращает пары конфликтующих занятий.
def find_conflicts_recursive(classes: tuple[Class, ...], slots: tuple[Slot, ...]) -> tuple[tuple[Class, Class], ...]:
    if len(classes) <= 1:
        return ()

    first = classes[0]
    rest = classes[1:]

    current_conflicts = tuple(
        (first, current)
        for current in rest
        for slot1 in slots
        if slot1.id == first.slot_id
        for slot2 in slots
        if slot2.id == current.slot_id
        and first.room_id == current.room_id
        and first.room_id != ""
        and first.slot_id != ""
        and slot1.start == slot2.start
        and slot1.end == slot2.end
    )

    return current_conflicts + find_conflicts_recursive(rest, slots)