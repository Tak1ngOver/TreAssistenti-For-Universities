from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union, Optional
 
T = TypeVar("T")   # значение успешного вычисления
E = TypeVar("E")   # тип ошибки / левой ветви
U = TypeVar("U")   # тип результата после map/bind
 
class Maybe(Generic[T]):
    #Контейнер для значения, которое может отсутствовать
    def map(self, func: Callable[[T], U]) -> "Maybe[U]":
        #Применяет функцию к значению, если оно существует
        raise NotImplementedError
 
    def bind(self, func: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        #Связывает контейнер с новой вычисляемой функцией (монда)
        raise NotImplementedError
 
    def get_or_else(self, default: U) -> Union[T, U]:
        #Возвращает значение, если оно есть, иначе значение по умолчанию
        raise NotImplementedError
 
 
@dataclass(frozen=True)
class Just(Maybe[T]):
    value: T
 
    def map(self, func: Callable[[T], U]) -> "Maybe[U]":
        return Just(func(self.value))
 
    def bind(self, func: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        return func(self.value)
 
    def get_or_else(self, default: U) -> T:
        return self.value
 
 
@dataclass(frozen=True)
class Nothing(Maybe[T]):
    def map(self, func: Callable[[T], U]) -> "Maybe[U]":
        return self
 
    def bind(self, func: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        return self
 
    def get_or_else(self, default: U) -> U:
        return default
 
class Either(Generic[E, T]):
    #Контейнер для значения, которое может быть успешным (Right) или ошибкой (Left)
 
    def map(self, func: Callable[[T], U]) -> "Either[E, U]":
        raise NotImplementedError
 
    def bind(self, func: Callable[[T], "Either[E, U]"]) -> "Either[E, U]":
        raise NotImplementedError
 
    def get_or_else(self, default: U) -> Union[T, U]:
        raise NotImplementedError
 
 
@dataclass(frozen=True)
class Right(Either[E, T]):
    value: T
 
    def map(self, func: Callable[[T], U]) -> "Either[E, U]":
        return Right(func(self.value))
 
    def bind(self, func: Callable[[T], "Either[E, U]"]) -> "Either[E, U]":
        return func(self.value)
 
    def get_or_else(self, default: U) -> T:
        return self.value
 
 
@dataclass(frozen=True)
class Left(Either[E, T]):
    error: E
 
    def map(self, func: Callable[[T], U]) -> "Either[E, U]":
 
    def bind(self, func: Callable[[T], "Either[E, U]"]) -> "Either[E, U]":
        return self  # остаёмся в ошибке
 
    def get_or_else(self, default: U) -> U:
        return default
   
def safe_room(rooms: tuple, room_id: str) -> Maybe:
    #Безопасно возвращает аудиторию по её ID. Возвращает Just(Room) если найдена, иначе Nothing.
    found = next((r for r in rooms if r.id == room_id), None)
    return Just(found) if found is not None else Nothing()
 
 
def validate_assignment(classes: tuple, rooms: tuple, slots: tuple, groups: tuple, cls) -> Either[dict, object]: 
    errors = {}
 
    # Найти аудиторию и слот
    
    room = next((r for r in rooms if r.id == cls.room_id), None)
    slot = next((s for s in slots if s.id == cls.slot_id), None)
    group = next((g for g in groups if g.id == cls.group_id), None)
 
    # Проверка существования
    if room is None:
        errors["room"] = f"Аудитория {cls.room_id} не найдена."
    if slot is None:
        errors["slot"] = f"Слот {cls.slot_id} не найден."
    if group is None:
        errors["group"] = f"Группа {cls.group_id} не найдена."
 
    # Проверка вместимости
    if hasattr(group, "size") and hasattr(room, "capacity"):
        if room.capacity < group.size:
            errors["capacity"] = f"Аудитория {room.name} ({room.capacity} мест) меньше группы ({group.size})."
    
    class_needs = cls.needs.split()
    # Проверка фичей аудитории
    if hasattr(room, "features"):
        if class_needs:
            for need in class_needs:
                if need not in room.features:
                 errors["features"] = f"Аудитория {room.name} не поддерживает требуемую фичу ({cls.needs})."
                 break
 
    # Проверка пересечений: аудитория / преподаватель / группа
    for other in classes:
        if other.id == cls.id:
            continue
        if other.slot_id == cls.slot_id:
            if other.room_id == cls.room_id:
                errors.setdefault("collision_room", []).append(f"Аудитория {cls.room_id} занята.")
            if other.teacher_id == cls.teacher_id:
                errors.setdefault("collision_teacher", []).append(f"Преподаватель {cls.teacher_id} уже занят.")
            if other.group_id == cls.group_id:
                errors.setdefault("collision_group", []).append(f"Группа {cls.group_id} уже занята.")
 
    return Left(errors) if errors else Right(cls)