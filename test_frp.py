import pytest
import json
from core.frp import *

def seed():
    with open("data/seed.json", encoding="utf-8") as f:
        return json.load(f)

def test_assign_slot():
    data = seed()
    bus = EventBus()
    bus.subscribe("ASSIGN_SLOT", assign_slot)

    state = bus.publish(
        "ASSIGN_SLOT",
        {"class_id": "ECON_LEC1", "slot_id": "TUE1"},
        data,
    )

    c = next(c for c in state["classes"] if c["id"] == "ECON_LEC1")
    assert c["slot_id"] == "TUE1"
    assert c["status"] == "scheduled"


def test_move_class():
    data = seed()
    bus = EventBus()
    bus.subscribe("MOVE_CLASS", move_class)

    state = bus.publish(
        "MOVE_CLASS",
        {"class_id": "ECON_LEC1", "new_room": "R03"},
        data,
    )

    c = next(c for c in state["classes"] if c["id"] == "ECON_LEC1")
    assert c["room_id"] == "R03"
    assert c["status"] == "moved"


def test_cancel_class():
    data = seed()
    bus = EventBus()
    bus.subscribe("CANCEL_CLASS", cancel_class)

    state = bus.publish("CANCEL_CLASS", {"class_id": "ECON_LEC2"}, data)

    c = next(c for c in state["classes"] if c["id"] == "ECON_LEC2")
    assert c["status"] == "cancelled"


def test_add_room():
    data = seed()
    bus = EventBus()
    bus.subscribe("ADD_ROOM", add_room)

    new_room = {
        "id": "R999",
        "building_id": "B02",
        "name": "999",
        "capacity": 10,
        "features": ["lab"],
    }

    state = bus.publish("ADD_ROOM", new_room, data)

    assert any(r["id"] == "R999" for r in state["rooms"])
    assert len(state["rooms"]) == len(data["rooms"]) + 1


def test_multiple_subscribers():
    data = seed()
    bus = EventBus()
    bus.subscribe("ASSIGN_SLOT", assign_slot)
    bus.subscribe("MOVE_CLASS", move_class)

    s1 = bus.publish("ASSIGN_SLOT", {"class_id": "ECON_LEC1", "slot_id": "TUE1"}, data)
    s2 = bus.publish("MOVE_CLASS", {"class_id": "ECON_LEC1", "new_room": "R05"}, s1)

    c = next(c for c in s2["classes"] if c["id"] == "ECON_LEC1")
    assert c["slot_id"] == "TUE1"
    assert c["room_id"] == "R05"
