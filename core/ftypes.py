from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable, Union, Iterable, Dict
from core.domain import *

# Типовые параметры
T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")

# Maybe
class Maybe(Generic[T]):
    def map(self, fn: Callable[[T], U]) -> Maybe[U]:
        raise NotImplementedError

    def bind(self, fn: Callable[[T], Maybe[U]]) -> Maybe[U]:
        raise NotImplementedError

    def get_or_else(self, default: U) -> Union[T, U]:
        raise NotImplementedError


@dataclass(frozen=True)
class Just(Maybe[T]):
    value: T

    def map(self, fn: Callable[[T], U]) -> Maybe[U]:
        return Just(fn(self.value))

    def bind(self, fn: Callable[[T], Maybe[U]]) -> Maybe[U]:
        return fn(self.value)

    def get_or_else(self, default: U) -> Union[T, U]:
        return self.value


class Nothing(Maybe[T]):
    instance = None

    def new(cls):
        if cls.instance is None:
            cls.instance = super().new(cls)
        return cls.instance

    def map(self, fn):
        return self

    def bind(self, fn):
        return self

    def get_or_else(self, default):
        return default


# Either (ошибка / успех)
class Either(Generic[E, T]):
    # Базовый тип Either для обработки ошибок

    def map(self, fn: Callable[[T], U]) -> Either[E, U]:
        raise NotImplementedError

    def bind(self, fn: Callable[[T], Either[E, U]]) -> Either[E, U]:
        raise NotImplementedError

    def get_or_else(self, default: U) -> Union[T, U]:
        raise NotImplementedError


@dataclass(frozen=True)
class Right(Either[E, T]):
    # Успешный результат
    value: T

    def map(self, fn):
        return Right(fn(self.value))

    def bind(self, fn):
        return fn(self.value)

    def get_or_else(self, default):
        return self.value


@dataclass(frozen=True)
class Left(Either[E, T]):
    # Ошибка (левая ветка Either)
    error: E

    def map(self, fn):
        return self

    def bind(self, fn):
        return self

    def get_or_else(self, default):
        return default


# Безопасные операции
def safe_room(rooms: Iterable[Room], room_id: str) -> Maybe[Room]:
    # Безопасный поиск комнаты по ID
    for room in rooms:
        if room.id == room_id:
            return Just(room)
    return Nothing()


# Валидация назначения класса
def validate_assignment(
    classes: Iterable[Class],
    rooms: Iterable[Room],
    slots: Iterable[Slot],
    groups: Iterable[Group],
    cls: Class
) -> Either[Dict[str, str], Class]:
    # Проверяет корректность назначения класса: наличие слота, аудитории и группы, вместимость и соответствие аудитории требованиям, отсутствие коллизий по слотам, преподавателям и группам
    errors: Dict[str, str] = {}

    # Проверка слота
    if not cls.slot_id:
        errors["slot"] = "Слот не назначен"
        return Left(errors)

    # Проверка аудитории
    room_maybe = safe_room(rooms, cls.room_id)
    if isinstance(room_maybe, Just):
        room = room_maybe.value
    else:
        errors["room"] = f"Аудитория {cls.room_id} не найдена"
        return Left(errors)

    # Проверка группы
    group = next((g for g in groups if g.id == cls.group_id), None)
    if group is None:
        errors["group"] = f"Группа {cls.group_id} не найдена"
        return Left(errors)

    # Проверка вместимости
    if room.capacity < group.size:
        errors["capacity"] = (
            f"Вместимость аудитории {room.capacity} меньше размера группы {group.size}"
        )

    # Проверка фич аудитории
    needs = cls.needs or ""
    if needs:
        room_features = tuple(f.lower() for f in room.features)
        need_lower = needs.lower()

        fits = any(
            need_lower in feature or feature in need_lower
            for feature in room_features
        )

        if not fits:
            errors["features"] = (
                f"Аудитория с характеристиками {room.features} "
                f"не удовлетворяет требованию '{cls.needs}'"
            )

    # Проверка коллизий
    for other in classes:
        if other.id == cls.id or other.slot_id != cls.slot_id:
            continue

        if other.room_id == cls.room_id:
            errors.setdefault(
                "collision_room",
                f"Аудитория {cls.room_id} уже используется для занятия {other.id}"
            )

        if other.teacher_id == cls.teacher_id:
            errors.setdefault(
                "collision_teacher",
                f"Преподаватель {cls.teacher_id} уже ведёт занятие {other.id}"
            )

        if other.group_id == cls.group_id:
            errors.setdefault(
                "collision_group",
                f"Группа {cls.group_id} уже имеет занятие {other.id}"
            )

    # Возврат результата
    if errors:
        return Left(errors)
    return Right(cls)