from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import transforms
from dataclasses import asdict
from typing import Dict, Tuple

app = FastAPI(title="Планировщик расписания")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


state: Dict[str, Tuple] = {}


@app.post("/load_seed")
async def load_seed():
    buildings, rooms, teachers, groups, courses, slots, classes, constraints = (
        transforms.load_seed("./data/seed.json")
    )

    state["buildings"] = buildings
    state["rooms"] = rooms
    state["teachers"] = teachers
    state["groups"] = groups
    state["courses"] = courses
    state["slots"] = slots
    state["classes"] = classes
    state["constraints"] = constraints

    return {
        "status": "ok"
    }


@app.get("/data")
async def get_data():
    def serialize_tuple(t):
        return [asdict(x) for x in t]

    return {
        "buildings": serialize_tuple(state["buildings"]),
        "rooms": serialize_tuple(state["rooms"]),
        "teachers": serialize_tuple(state["teachers"]),
        "groups": serialize_tuple(state["groups"]),
        "courses": serialize_tuple(state["courses"]),
        "slots": serialize_tuple(state["slots"]),
        "classes": serialize_tuple(state["classes"]),
        "constraints": serialize_tuple(state["constraints"]),
    }


@app.post("/total_room_capacity")
async def get_capacity():
    result = transforms.total_room_capacity(state["rooms"])
    return {
        "total_capacity": result
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app=app)