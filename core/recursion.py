from domain import Class, Slot, Room

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