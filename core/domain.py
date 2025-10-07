# Модели, с которыми работает программа.
# Авторы: Дильшат Сембаев.

from dataclasses import dataclass

@dataclass(frozen=True)
class Building:                     #Корпус
    id: str                         #Идентификатор корпуса
    name: str                       #Наименование здания

@dataclass(frozen=True)
class Room:                         #Аудитория
    id: str                         #Идентификатор аудитории
    building_id: str                #Идентификатор корпуса, в котором находится аудитория
    name: str                       #Наименование (или номер) аудитории
    capacity: int                   #Количество мест
    features: tuple[str, ...]       #Особенности (например: projector, lab, accessibility)

@dataclass(frozen=True)
class Teacher:                      #Преподаватель
    id: str                         #Идентификатор преподавателя
    name: str                       #ФИО преподавателя
    dept: str                       #Кафедра, к которой относится преподаватель

@dataclass(frozen=True)
class Group:                        #Группа
    id: str                         #Идентификатор группы
    name: str                       #Наименование группы
    size: int                       #Количество студентов в группе
    track: str                      #Учебное направление

@dataclass(frozen=True)
class Course:                       #Дисциплина
    code: str                       #Код дисциплины
    title: str                      #Наименование дисциплины
    dept: str                       #Кафедра, к которой относится дисциплина
    hours_per_week: int             #Количество часо в в неделю

@dataclass(frozen=True)
class Slot:                         #Слот (место в расписании)
    id: str                         #Идентификатор слота
    day: str                        #День недели
    start: str                      #Начало пары
    end: str                        #Конец пары

@dataclass(frozen=True)
class Class:                        #Пара
    id: str                         #Идентификатор пары
    course_id: str                  #Идентификатор дисциплины
    needs: tuple[str, ...]          #Требует (например: lab, projector)
    teacher_id: str                 #Идентификатор преподавателя
    group_id: str                   #Идентификатор учебной группы
    slot_id: str                    #Идентификатор слота
    room_id: str                    #Идентификатор аудитории
    status: str                     #Статус занятия (например: planned/scheduled/moved/cancelled)

@dataclass(frozen=True)
class Constraint:                   #Ограничение
    id: str                         #Идентификатор ограничения
    kind: str                       #Тип ограничения (например: max windows per day, preferred buildings и т.п.) 
    payload: dict                   #Дополнительные сведения (например: "teacher_id": "T01")