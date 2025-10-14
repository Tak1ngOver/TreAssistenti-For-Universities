from functools import lru_cache
from core.domain import *
import time
import json

@lru_cache(maxsize=None)
def compute_timetable_stats(
    key: str,
    classes_index: tuple["Class", ...],
    slots_index: tuple["Slot", ...]
) -> tuple[tuple[str, int], ...]:
    # Базовый случай
    if not classes_index:
        return (("conflicts", 0), ("windows", 0))

    head = classes_index[0]
    tail = classes_index[1:]

    # Рекурсивный вызов
    tail_stats = compute_timetable_stats(key, tail, slots_index)

    conflicts = 0
    windows = 0

    # Конфликты
    for other in tail:
        if other.slot_id == head.slot_id and other.slot_id != "":
            if (
                other.group_id == head.group_id
                or other.teacher_id == head.teacher_id
            ):
                conflicts += 1

    # День текущего занятия
    slot_day = next((s.day for s in slots_index if s.id == head.slot_id), None)

    # Если есть слот и день
    if slot_day:
        day_slots = [
            int(s.id[-1])
            for s in slots_index
            if s.day == slot_day and any(
                c.group_id == head.group_id and c.slot_id == s.id
                for c in classes_index
            )
        ]
        day_slots.sort()
        for i in range(len(day_slots) - 1):
            diff = day_slots[i + 1] - day_slots[i]
            if diff > 1:
                windows += diff - 1

    total_conflicts = tail_stats[0][1] + conflicts
    total_windows = tail_stats[1][1] + windows

    return (("conflicts", total_conflicts), ("windows", total_windows))

def measure_cache_performance():
    with open("./data/seed.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    classes = tuple(Class(**c) for c in data["classes"])
    slots = tuple(Slot(**s) for s in data["slots"])

    start = time.perf_counter()
    compute_timetable_stats("first_run", classes, slots)
    t1 = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    compute_timetable_stats("first_run", classes, slots)  # повтор с кэшем
    t2 = (time.perf_counter() - start) * 1000

    print(f"Первый вызов: {t1:.3f} ms")
    print(f"Второй (из кэша): {t2:.3f} ms")
    return t1, t2