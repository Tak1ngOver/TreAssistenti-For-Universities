from domain import Class, Slot, Room

#Замыкания-предикаты

#Предикат для фильтрации занятий по дню недели
def by_day(day: str):
    return lambda c, slots: any(s.id == c.slot_id and s.day == day for s in slots)