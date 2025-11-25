# core/async_schedule.py
import asyncio
from dataclasses import asdict
from typing import Tuple, Callable, Dict, Any
from functools import reduce

from core.domain import Building, Room, Teacher, Group, Course, Slot, Class, Constraint

# небольшие хелперы — совместимы со стилем из примеров
def to_tuple(type_, items):
    if items is None:
        return tuple()
    # If already dataclass instances, leave them
    if items and isinstance(items[0], type_):
        return tuple(items)
    return tuple(type_(**it) for it in items)


def _ensure_rooms(rooms):
    if not rooms:
        return tuple()
    if not isinstance(rooms[0], Room):
        return to_tuple(Room, rooms)
    return rooms


def _ensure_slots(slots):
    if not slots:
        return tuple()
    if not isinstance(slots[0], Slot):
        return to_tuple(Slot, slots)
    return slots


def _ensure_classes(classes):
    if not classes:
        return tuple()
    if not isinstance(classes[0], Class):
        return to_tuple(Class, classes)
    return classes


# Простая логика совместимости комнаты и занятия:
def _room_matches_needs(room: Room, needs: Any) -> bool:
    """
    needs может быть строкой или итерируемым (list/tuple).
    Сопоставляем по вхождению слова needs в features или наоборот.
    (в seed.json есть опечатки вроде 'lectoruim' — используем подстрочные вхождения)
    """
    if needs is None or needs == "" or needs == []:
        return True
    slot_needs = []
    if isinstance(needs, (list, tuple)):
        slot_needs = [str(n).lower() for n in needs]
    else:
        slot_needs = [str(needs).lower()]

    room_feats = [str(f).lower() for f in room.features] if room.features else []
    # если room_feats содержит "none", то считаем, что только пустые needs подходят
    for need in slot_needs:
        # точное или частичное совпадение
        ok = any(need in rf or rf in need for rf in room_feats)
        if not ok:
            return False
    return True


def _group_size_ok(room: Room, group: Group) -> bool:
    return room.capacity >= group.size


def _find_slot_room_combination(
    class_obj: Class, groups: Tuple[Group, ...], day_slots: Tuple[Slot, ...], rooms: Tuple[Room, ...], taken_combos: set
):
    """
    Ищет первую подходящую пару (slot_id, room_id) для class_obj на этом дне,
    учитывая уже занятые комбинации (slot_id, room_id).
    Возвращает (slot_id, room_id) или (None, None).
    """
    # получим группу по id
    group = None
    for g in groups:
        if g.id == class_obj.group_id:
            group = g
            break

    for slot in day_slots:
        for room in rooms:
            combo = (slot.id, room.id)
            if combo in taken_combos:
                continue
            if not _room_matches_needs(room, class_obj.needs):
                continue
            if group and not _group_size_ok(room, group):
                continue
            return slot.id, room.id
    return None, None


async def schedule_batch(day: str, classes, rooms, slots, groups) -> dict:
    """
    Асинхронно планирует (на заданный день) все занятия, которые ещё не имеют slot_id.
    Возвращает словарь с ключами:
      - day: str
      - classes: tuple[Class,...] (обновлённый)
      - report: dict (scheduled, unscheduled, collisions, details)
    Параллельность достигается тем, что функция является coroutine и generate_period_report
    вызывает её через asyncio.gather для нескольких дней одновременно.
    """
    # tiny await чтобы показать, что это coroutine (симуляция I/O/CPU-bound)
    await asyncio.sleep(0)

    classes = _ensure_classes(classes)
    rooms = _ensure_rooms(rooms)
    slots = _ensure_slots(slots)
    groups = to_tuple(Group, groups) if groups and not isinstance(groups[0], Group) else groups

    # слоты только для этого дня
    day_slots = tuple(s for s in slots if s.day.lower() == day.lower())

    # набор занятых комбинаций (slot_id, room_id) на этом дне — учтём уже запланированные занятия
    taken_combos = set()
    taken_teacher_slot = set()  # (teacher_id, slot_id) занятые
    for c in classes:
        if c.slot_id and c.room_id:
            # проверяем, что slot принадлежит дню
            slot_objs = tuple(filter(lambda s: s.id == c.slot_id, day_slots))
            if slot_objs:
                taken_combos.add((c.slot_id, c.room_id))
                taken_teacher_slot.add((c.teacher_id, c.slot_id))

    updated = []
    assigned = []
    unassigned = []
    # итерация по занятиям: назначаем только те, у кого пустой slot_id
    for c in classes:
        if c.slot_id:  # уже запланировано — копируем как есть
            updated.append(c)
            continue
        # ищем первую подходящую (slot, room)
        slot_id, room_id = _find_slot_room_combination(c, groups, day_slots, rooms, taken_combos)
        if slot_id and room_id:
            # проверяем конфликт по преподавателю (один преподаватель в один слот)
            if (c.teacher_id, slot_id) in taken_teacher_slot:
                # нельзя назначить в этот слот — считаем, что нет подходящего
                unassigned.append(c)
                updated.append(c)
                continue
            # сформируем обновлённый класс (иммутабельно)
            updated_c = Class(
                id=c.id,
                course_id=c.course_id,
                needs=c.needs,
                teacher_id=c.teacher_id,
                group_id=c.group_id,
                slot_id=slot_id,
                room_id=room_id,
                status="scheduled",
            )
            updated.append(updated_c)
            assigned.append(updated_c)
            taken_combos.add((slot_id, room_id))
            taken_teacher_slot.add((c.teacher_id, slot_id))
        else:
            # не удалось назначить
            unassigned.append(c)
            updated.append(c)

    # Детекция коллизий: те же (slot_id, room_id) или (teacher_id, slot_id) дублируются => коллизии
    collisions = []
    # проверка на дубли (slot, room)
    seen = {}
    for c in updated:
        key = (c.slot_id, c.room_id)
        if c.slot_id and c.room_id:
            if key in seen:
                collisions.append(
                    {
                        "type": "room_conflict",
                        "slot_id": c.slot_id,
                        "room_id": c.room_id,
                        "classes": [seen[key].id, c.id],
                    }
                )
            else:
                seen[key] = c
    # проверка на дубли по преподавателю
    seen_teacher = {}
    for c in updated:
        key = (c.teacher_id, c.slot_id)
        if c.teacher_id and c.slot_id:
            if key in seen_teacher:
                collisions.append(
                    {
                        "type": "teacher_conflict",
                        "slot_id": c.slot_id,
                        "teacher_id": c.teacher_id,
                        "classes": [seen_teacher[key].id, c.id],
                    }
                )
            else:
                seen_teacher[key] = c

    report = {
        "day": day,
        "scheduled_count": len([c for c in updated if c.slot_id]),
        "assigned_this_run": len(assigned),
        "unscheduled_count": len([c for c in updated if not c.slot_id]),
        "collisions": collisions,
        "assigned_ids": [c.id for c in assigned],
        "unassigned_ids": [c.id for c in unassigned],
    }

    return {"day": day, "classes": tuple(updated), "report": report}


async def generate_period_report(days: list[str], classes, rooms, slots, groups) -> dict:
    """
    Параллельно вызывает schedule_batch для списка дней и агрегирует отчёты.
    Возвращает dict:
      - days: list of per-day reports (as returned by schedule_batch)
      - aggregated: totals (scheduled, unscheduled, collisions_count)
    """
    # build tasks
    tasks = []
    for d in days:
        tasks.append(schedule_batch(d, classes, rooms, slots, groups))

    # одновременно выполняем по дням
    results = await asyncio.gather(*tasks)

    aggregated = {
        "total_days": len(results),
        "total_scheduled": sum(r["report"]["scheduled_count"] for r in results),
        "total_assigned_this_run": sum(r["report"]["assigned_this_run"] for r in results),
        "total_unscheduled": sum(r["report"]["unscheduled_count"] for r in results),
        "total_collisions": sum(len(r["report"]["collisions"]) for r in results),
    }

    return {"days": results, "aggregated": aggregated}
