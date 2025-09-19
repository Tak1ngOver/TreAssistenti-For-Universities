# Модели, с которыми работает программа.
# Авторы: 

from dataclasses import dataclass

@dataclass(frozen=True)
class Building:                     #Корпус
    id: str                         #Идентификатор корпуса
    name: str                       #Наименование здания

@dataclass(frozen=True)
class Room:                         #Аудитория
    id: str                         #Идентификатор аудитории
    building_id: int                #Идентификатор корпуса, в котором находится аудитория
    name: str                       #Наименование (или номер) аудитории
    capacity: int                   #Количество мест
    features: tuple[str, ...]       #Особенности (например: projector, lab, accessibility)

@dataclass(frozen=True)
class Teacher:                      #Преподаватель
    id: str                         #Идентификатор преподавателя
    name: str                       #ФИО преподавателя
    dept: str                       #Кафедра, к которой относится преподаватель

@dataclass(frozen=True)
class Course:                       #Дисциплина
    id: str                         #Идентификатор дисциплины
    code: str                       #Код дисциплины
    title: str                      #Наименование дисциплины
    hours_per_week: int             #Количество часов в неделю
    needs: tuple[str, ...]          #Требует (например: lab, projector)

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