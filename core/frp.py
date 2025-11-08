from typing import NamedTuple, Callable, Dict, Any

class Event(NamedTuple):
    name: str
    payload: dict


class EventBus:
    def __init__(self) -> None:
        self.subscribers: Dict[str, list[Callable[[Event, dict], dict]]] = {}

    def subscribe(self, name: str, handler: Callable[[Event, dict], dict]):
        #Подписка на событие
        if name not in self.subscribers:
            self.subscribers[name] = []
        self.subscribers[name].append(handler)

    def publish(self, name: str, payload: dict, state: dict):
        #Публикация события и возврат нового состояния
        event = Event(name, payload)
        handlers = self.subscribers.get(name, [])
        new_state = state
        for h in handlers:
            new_state = h(event, new_state)
        return new_state

def assign_slot(event: Event, state: dict):
    #Назначение слота для пары
    class_id = event.payload["class_id"]
    slot_id = event.payload["slot_id"]
    updated = []
    for c in state["classes"]:
        if c["id"] == class_id:
            new_c = dict(c)
            new_c["slot_id"] = slot_id
            new_c["status"] = "scheduled"
            updated.append(new_c)
        else:
            updated.append(c)
    return {**state, "classes": updated}


def move_class(event: Event, state: dict):
    #Перемещение пары в другую аудитори
    class_id = event.payload["class_id"]
    room_id = event.payload["new_room"]
    updated = []
    for c in state["classes"]:
        if c["id"] == class_id:
            new_c = dict(c)
            new_c["room_id"] = room_id
            new_c["status"] = "moved"
            updated.append(new_c)
        else:
            updated.append(c)
    return {**state, "classes": updated}


def cancel_class(event: Event, state: dict):
    #Отмена пары
    class_id = event.payload["class_id"]
    updated = []
    for c in state["classes"]:
        if c["id"] == class_id:
            new_c = dict(c)
            new_c["status"] = "cancelled"
            updated.append(new_c)
        else:
            updated.append(c)
    return {**state, "classes": updated}


def add_room(event: Event, state: dict):
    #Добавление новой аудитории
    new_room = event.payload
    rooms = list(state["rooms"])
    rooms.append(new_room)
    return {**state, "rooms": rooms}