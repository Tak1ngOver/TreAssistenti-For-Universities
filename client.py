# client.py
import asyncio
import json
from typing import Optional, List, Dict, Any

import flet as ft
import httpx

from core import transforms, memo
from core import service as svc
from core.domain import *
from core.async_schedule import *
from core.frp import *
from core.transforms import *

BACKEND_URL = "http://127.0.0.1:8000"

MENU = [
    "Overview",
    "Data",
    "Functional Core",
    "Pipelines",
    "Async/FRP",
    "Reports",
    "Tests",
    "About",
]

MENU_ICONS = [
    ft.Icons.DASHBOARD,
    ft.Icons.STORAGE,
    ft.Icons.SETTINGS,
    ft.Icons.TRENDING_UP,
    ft.Icons.TIMELINE,
    ft.Icons.INSIGHTS,
    ft.Icons.BUG_REPORT,
    ft.Icons.INFO,
]

state = {}  # тут будут ключи: buildings, rooms, teachers, groups, courses, slots, classes, constraints

bus = EventBus()
bus.subscribe("ASSIGN_SLOT", assign_slot)
bus.subscribe("MOVE_CLASS", move_class)
bus.subscribe("CANCEL_CLASS", cancel_class)
bus.subscribe("ADD_ROOM", add_room)

def map_by_id(items, id_field="id", name_field="name"):
    return {it[id_field]: it[name_field] for it in items}


def get_weekday_options():
    return [
        ("monday", "Понедельник"),
        ("tuesday", "Вторник"),
        ("wednesday", "Среда"),
        ("thursday", "Четверг"),
        ("friday", "Пятница")
    ]


def ensure_loaded(page: ft.Page, section_content: ft.Column) -> bool:
    if not state.get("buildings"):
        section_content.controls.append(
            ft.Text(
                "Данные не загружены. Пожалуйста, перейдите на вкладку Data для загрузки данных.",
                color=ft.Colors.BLACK87,
            )
        )
        page.update()
        return False
    return True

def main_page(page: ft.Page):
    page.title = "Планировщик — Расписание"
    page.bgcolor = ft.Colors.WHITE
    page.scroll = ft.ScrollMode.AUTO

    section_name = ft.Text(
        "Overview", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87
    )
    section_content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    popup = ft.PopupMenuButton(
        items=[
            ft.PopupMenuItem(icon=MENU_ICONS[i], text=MENU[i], on_click=lambda e, n=MENU[i]: switch_section(n))
            for i in range(len(MENU))
        ]
    )

    main_content_container = ft.Container(
        content=ft.Column(
            [section_name, section_content],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        ),
        expand=True,
        padding=20,
    )

    page.add(
        ft.Row(
            [popup, main_content_container],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )

    def map_by_id(items, id_field="id", name_field="name"):
        return {it[id_field]: it[name_field] for it in items}

    def switch_section(name: str):
        section_name.value = name
        update_section()

    def update_section():
        section_content.controls.clear()
        if section_name.value == "Overview":
            show_overview()
        elif section_name.value == "Data":
            show_data_section()
        elif section_name.value == "About":
            section_content.controls.append(
                ft.Text(
                    "Это проект программы, помогающей составлять расписание для университетов.",
                    color=ft.Colors.BLACK87,
                )
            )
        elif section_name.value == "Pipelines":
            show_pipelines_section()
        elif section_name.value == "Async/FRP":
            show_async_frp_section()
        elif section_name.value == "Reports":
            show_reports_section()
        else:
            section_content.controls.append(ft.Text("Тут пока ещё пусто. :)", color=ft.Colors.BLACK87))
        page.update()

    # ---------------------- Overview (summary + filters + classes table) ----------------------
    def show_overview():
        section_content.controls.clear()

        if not state.get("buildings"):
            section_content.controls.append(
                ft.Text(
                    "Данные не загружены. Пожалуйста, перейдите на вкладку Data для загрузки данных.",
                    color=ft.Colors.BLACK87,
                )
            )
            page.update()
            return

        # prepare mapping dicts
        courses_by_code = {c["code"]: c for c in state["courses"]}
        teachers_map = map_by_id(state["teachers"])
        groups_map = map_by_id(state["groups"])
        rooms_map = {r["id"]: r for r in state["rooms"]}
        buildings_map = map_by_id(state["buildings"], id_field="id", name_field="name")
        slots_map = {s["id"]: s for s in state["slots"]}

        # initial filter values (None => no filter)
        selected_day: Optional[str] = None
        selected_teacher: Optional[str] = None
        selected_group: Optional[str] = None
        selected_building: Optional[str] = None

        capacity_button = ft.ElevatedButton("Вместительность всех аудиторий", on_click=lambda _: get_capacity())
        capacity_text = ft.Text("")
        
        add_class_button = ft.ElevatedButton("Добавить занятие", on_click=lambda _: add_new_class())
        assign_room_button = ft.ElevatedButton("Изменить аудиторию", on_click=lambda _: assign_room())
        assign_slot_button = ft.ElevatedButton("Изменить слот", on_click=lambda _: assign_slot())

        def assign_room():
            def get_options(mahkey):
                options = []
                for el in state[mahkey]:
                    if mahkey == "rooms" or mahkey == "teachers" or mahkey == "groups":
                        options.append(
                        ft.DropdownOption(key=el["id"], text=el["name"])
                        )
                    elif mahkey == "courses":
                        options.append(
                        ft.DropdownOption(key=el["id"], text=el["title"])
                        )
                    else:
                        options.append(
                        ft.DropdownOption(key=el["id"])
                        )
                return options
            section_content.controls.clear()
            cls_select = ft.Dropdown(
                editable=True,
                enable_filter=True,
                menu_height=250,
                label="Занятие",
                options=get_options("classes")
            )
            room_select = ft.Dropdown(
                editable=True,
                enable_filter=True,
                menu_height=250,
                label="Аудитория",
                options=get_options("rooms")
            )
            back_button = ft.ElevatedButton("Назад", on_click=lambda _: show_overview())
            submit_button = ft.ElevatedButton("Продолжить", on_click=lambda _: tryassign_room())

            section_content.controls.append(ft.Text("Выберите занятие, для которого хотите изменить аудиторию:"))
            section_content.controls.append(cls_select)
            section_content.controls.append(ft.Text("Выберите аудиторию, которую хотите назначить:"))
            section_content.controls.append(room_select)
            section_content.controls.append(submit_button)
            section_content.controls.append(back_button)
            page.update()
            def tryassign_room():
                if not cls_select.value or not room_select.value:
                     missing = ft.Banner(
                                        bgcolor=ft.Colors.AMBER_100,
                                        leading=ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER, size=40),
                                        content=ft.Text(
                                                          value="Пожалуйста, обязательно выберите идентификатор занятия и идентификатор аудитории!",
                                                          color=ft.Colors.BLACK,
                                                        ),
                                        actions=[
                                                ft.TextButton(
                                                            text="Хорошо", on_click=lambda _: page.close(missing)
                                                            )
                                                ],
                                            )
                     page.open(missing) 
                     return             
                new_classes = transforms.assign_room(state["classes"], cls_select.value, room_select.value)
                state["classes"] = list(transforms.serialize_tuple(new_classes))
                show_overview()

        def assign_slot():
            def get_options(mahkey):
                options = []
                for el in state[mahkey]:
                    if mahkey == "rooms" or mahkey == "teachers" or mahkey == "groups":
                        options.append(
                        ft.DropdownOption(key=el["id"], text=el["name"])
                        )
                    elif mahkey == "courses":
                        options.append(
                        ft.DropdownOption(key=el["id"], text=el["title"])
                        )
                    else:
                        options.append(
                        ft.DropdownOption(key=el["id"])
                        )
                return options
            section_content.controls.clear()
            cls_select = ft.Dropdown(
                editable=True,
                enable_filter=True,
                menu_height=250,
                label="Занятие",
                options=get_options("classes")
            )
            slot_select = ft.Dropdown(
                editable=True,
                enable_filter=True,
                menu_height=250,
                label="Слот",
                options=get_options("slots")
            )
            back_button = ft.ElevatedButton("Назад", on_click=lambda _: show_overview())
            submit_button = ft.ElevatedButton("Продолжить", on_click=lambda _: tryassign_slot())

            section_content.controls.append(ft.Text("Выберите занятие, для которого хотите изменить слот:"))
            section_content.controls.append(cls_select)
            section_content.controls.append(ft.Text("Выберите слот, который хотите назначить:"))
            section_content.controls.append(slot_select)
            section_content.controls.append(submit_button)
            section_content.controls.append(back_button)
            page.update()
            def tryassign_slot():
                if not cls_select.value or not slot_select.value:
                     missing = ft.Banner(
                                        bgcolor=ft.Colors.AMBER_100,
                                        leading=ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER, size=40),
                                        content=ft.Text(
                                                          value="Пожалуйста, обязательно выберите идентификатор занятия и идентификатор слота!",
                                                          color=ft.Colors.BLACK,
                                                        ),
                                        actions=[
                                                ft.TextButton(
                                                            text="Хорошо", on_click=lambda _: page.close(missing)
                                                            )
                                                ],
                                            )
                     page.open(missing) 
                     return             
                new_classes = transforms.assign_slot(state["classes"], cls_select.value, slot_select.value)
                state["classes"] = list(transforms.serialize_tuple(new_classes))
                show_overview()

        def add_new_class():
            def get_options(mahkey):
                options = []
                for el in state[mahkey]:
                    if mahkey == "rooms" or mahkey == "teachers" or mahkey == "groups":
                        options.append(
                        ft.DropdownOption(key=el["id"], text=el["name"])
                        )
                    elif mahkey == "courses":
                        options.append(
                        ft.DropdownOption(key=el["id"], text=el["title"])
                        )
                    else:
                        options.append(
                        ft.DropdownOption(key=el["id"])
                        )
                return options           
            section_content.controls.clear()
            cls_id = ft.TextField(label="Идентификатор занятия")
            cls_course = ft.TextField(label="Идентификатор дисциплины")
            cls_status = ft.Dropdown(
                editable=True,
                enable_filter=True,
                label="Статус",
                options=[
                    ft.DropdownOption(key="scheduled"),
                    ft.DropdownOption(key="cancelled"),
                    ft.DropdownOption(key="planned")]
            )

            cls_teacher = ft.Dropdown(
                editable=True,
                enable_filter=True,
                menu_height=250,
                width=250,
                label="Преподаватель",
                options=get_options("teachers")
            )
            cls_group = ft.Dropdown(
                editable=True,
                enable_filter=True,
                menu_height=250,
                label="Группа",
                options=get_options("groups")
            )
            cls_slot = ft.Dropdown(
                editable=True,
                enable_filter=True,
                menu_height=250,
                label="Слот",
                options=get_options("slots")
            )
            cls_room = ft.Dropdown(
                editable=True,
                enable_filter=True,
                menu_height=250,
                width=200,
                label="Аудитория",
                options=get_options("rooms")
            )
            back_button = ft.ElevatedButton("Назад", on_click=lambda _: show_overview())
            submit_button = ft.ElevatedButton("Продолжить", on_click=lambda _: tryadd_new_class())

            section_content.controls.append(ft.Text("Введите данные нового занятия"))
            section_content.controls.append(cls_id)
            section_content.controls.append(cls_course)
            section_content.controls.append(cls_teacher)
            section_content.controls.append(cls_group)
            section_content.controls.append(cls_slot)
            section_content.controls.append(cls_room)
            section_content.controls.append(cls_status)
            section_content.controls.append(submit_button)
            section_content.controls.append(back_button)
            page.update()

            def tryadd_new_class():
                 if not cls_id.value or not cls_course.value:
                     missing_cls = ft.Banner(
                                        bgcolor=ft.Colors.AMBER_100,
                                        leading=ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER, size=40),
                                        content=ft.Text(
                                                          value="Пожалуйста, обязательно введите идентификатор занятия и идентификатор предмета!",
                                                          color=ft.Colors.BLACK,
                                                        ),
                                        actions=[
                                                ft.TextButton(
                                                            text="Хорошо", on_click=lambda _: page.close(missing_cls)
                                                            )
                                                ],
                                            )
                     page.open(missing_cls) 
                     return             
                 new_c = Class(id = cls_id.value, 
                                course_id = cls_course.value,
                                needs = "",
                                teacher_id = cls_teacher.value,
                                group_id = cls_group.value,
                                slot_id = cls_slot.value,
                                room_id = cls_room.value,
                                status = cls_status.value)
                 new_classes = transforms.add_class(state["classes"], new_c)
                 state["classes"] = list(transforms.serialize_tuple(new_classes))
                 show_overview()
            

        # UI controls
        def get_capacity():
            global capacity_text
            total_capacity = transforms.total_room_capacity(tuple(state["rooms"]))
            capacity_text = ft.Text(f"Общая вместимость: {total_capacity}")
            section_content.controls[1] = capacity_text
            page.update() 
                
        def make_days_options():
            days = []
            seen = set()
            for s in state["slots"]:
                if s["day"] not in seen:
                    days.append(s["day"])
                    seen.add(s["day"])
            return ["(все)"] + days

        day_dropdown = ft.Dropdown(
            label="День",
            width=200,
            options=[ft.dropdown.Option(opt) for opt in make_days_options()],
            value="(все)",
        )

        teacher_dropdown = ft.Dropdown(
            label="Преподаватель",
            width=300,
            options=[ft.dropdown.Option("(все)")] + [ft.dropdown.Option(t["id"], text=t["name"]) for t in state["teachers"]],
            value="(все)",
        )

        group_dropdown = ft.Dropdown(
            label="Группа",
            width=250,
            options=[ft.dropdown.Option("(все)")] + [ft.dropdown.Option(g["id"], text=g["name"]) for g in state["groups"]],
            value="(все)",
        )

        building_dropdown = ft.Dropdown(
            label="Корпус",
            width=250,
            options=[ft.dropdown.Option("(все)")] + [ft.dropdown.Option(b["id"], text=b["name"]) for b in state["buildings"]],
            value="(все)",
        )

        clear_button = ft.ElevatedButton("Сбросить фильтры", on_click=lambda _: on_clear())

        # table for classes
        classes_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Дисциплина")),
                ft.DataColumn(ft.Text("Группа")),
                ft.DataColumn(ft.Text("Преподаватель")),
                ft.DataColumn(ft.Text("День / Время")),
                ft.DataColumn(ft.Text("Аудитория")),
                ft.DataColumn(ft.Text("Корпус")),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.BLACK12),
            heading_row_color="#358FC1",
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            expand=True,
        )

        def build_classes_rows(filtered_classes):
            rows = []
            for cl in filtered_classes:
                course = courses_by_code.get(cl["course_id"], {"title": cl["course_id"]})
                slot = slots_map.get(cl["slot_id"], None)
                slot_text = f"{slot['day']} {slot['start']}-{slot['end']}" if slot else ""
                room = rooms_map.get(cl["room_id"], None)
                building_name = buildings_map.get(room["building_id"], "") if room else ""
                teacher_name = teachers_map.get(cl["teacher_id"], "")
                group_name = groups_map.get(cl["group_id"], "")
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(cl["id"], color=ft.Colors.BLACK87)),
                            ft.DataCell(ft.Text(course.get("title", cl["course_id"]), color=ft.Colors.BLACK87)),
                            ft.DataCell(ft.Text(group_name, color=ft.Colors.BLACK87)),
                            ft.DataCell(ft.Text(teacher_name, color=ft.Colors.BLACK87)),
                            ft.DataCell(ft.Text(slot_text, color=ft.Colors.BLACK87)),
                            ft.DataCell(ft.Text(room["name"] if room else "", color=ft.Colors.BLACK87)),
                            ft.DataCell(ft.Text(building_name, color=ft.Colors.BLACK87)),
                        ]
                    )
                )
            return rows

        # filtering logic
        def apply_filters():
            nonlocal classes_table
            filtered = state["classes"]

            # day filter
            if day_dropdown.value and day_dropdown.value != "(все)":
                target_day = day_dropdown.value
                # find slot ids for that day
                slot_ids = {s["id"] for s in state["slots"] if s["day"] == target_day}
                filtered = [c for c in filtered if c["slot_id"] in slot_ids]

            # teacher filter
            if teacher_dropdown.value and teacher_dropdown.value != "(все)":
                tid = teacher_dropdown.value
                filtered = [c for c in filtered if c["teacher_id"] == tid]

            # group filter
            if group_dropdown.value and group_dropdown.value != "(все)":
                gid = group_dropdown.value
                filtered = [c for c in filtered if c["group_id"] == gid]

            # building filter -> need rooms in building
            if building_dropdown.value and building_dropdown.value != "(все)":
                bid = building_dropdown.value
                room_ids = {r["id"] for r in state["rooms"] if r["building_id"] == bid}
                filtered = [c for c in filtered if c["room_id"] in room_ids]

            # rebuild table rows
            classes_table.rows = build_classes_rows(filtered)
            page.update()

        def on_clear():
            day_dropdown.value = "(все)"
            teacher_dropdown.value = "(все)"
            group_dropdown.value = "(все)"
            building_dropdown.value = "(все)"
            apply_filters()

        # attach handlers
        def dropdown_changed(e):
            apply_filters()

        day_dropdown.on_change = dropdown_changed
        teacher_dropdown.on_change = dropdown_changed
        group_dropdown.on_change = dropdown_changed
        building_dropdown.on_change = dropdown_changed

        # initial fill
        apply_filters()

        # assemble UI
        filters_row = ft.Row(
            [
                day_dropdown,
                teacher_dropdown,
                group_dropdown,
                building_dropdown,
                clear_button,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )
        section_content.controls.append(capacity_button)
        section_content.controls.append(capacity_text)
        section_content.controls.append(add_class_button)
        section_content.controls.append(assign_room_button)
        section_content.controls.append(assign_slot_button)
        section_content.controls.append(ft.Text("Фильтры по предикатам", size=18, weight=ft.FontWeight.BOLD))
        section_content.controls.append(filters_row)
        section_content.controls.append(ft.Divider())
        section_content.controls.append(classes_table)
        page.update()

    # ---------------------- Data tab ----------------------
    def show_data_section():
        async def load_data(e):
            section_content.controls.clear()
            section_content.controls.append(ft.Text("Загрузка...", color=ft.Colors.BLACK87))
            page.update()
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(f"{BACKEND_URL}/load_seed", timeout=10.0)
                    r = await client.get(f"{BACKEND_URL}/data", timeout=10.0)
                    data = r.json()
                    # update global state
                    state.update(data)
                section_content.controls.clear()
                section_content.controls.append(ft.Text("Данные успешно загружены!", color=ft.Colors.GREEN))
                section_content.controls.append(ft.ElevatedButton("Перейти на Overview", on_click=lambda e: switch_section("Overview")))
            except Exception as ex:
                section_content.controls.clear()
                section_content.controls.append(ft.Text(f"Ошибка при загрузке данных: {ex}", color=ft.Colors.RED))
            page.update()

        section_content.controls.clear()
        section_content.controls.append(
            ft.ElevatedButton(
                "Загрузить данные",
                bgcolor=ft.Colors.GREY_200,
                color=ft.Colors.BLACK87,
                width=180,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                on_click=load_data,
            )
        )
        page.update()

    def show_pipelines_section():
        section_content.controls.clear()
        if not state.get("buildings"):
            section_content.controls.append(
                ft.Text(
                    "Данные не загружены. Пожалуйста, перейдите на вкладку Data для загрузки данных.",
                    color=ft.Colors.BLACK87,
                )
            )
            page.update()
            return
        section_content.controls.append(
            ft.ElevatedButton(
                "Вычислить коллизии и окна в расписании",
                on_click=lambda _: compute_conflicts(),
            ))
        section_content.controls.append(
            ft.ElevatedButton(
                "Сравнение скорости работы с хешем и без",
                on_click=lambda _: compute_time_hash(),
            ))
        page.update()
        def compute_conflicts():
            result = memo.compute_timetable_stats("допустим", transforms.to_tuple(Class, state["classes"]), transforms.to_tuple(Slot, state["slots"]))
            colisions = result[0][1]
            windows = result[1][1]
            if isinstance(section_content.controls[-1], ft.Text):
                section_content.controls.pop()
            section_content.controls.append(ft.Text(f"Количество коллизий: {colisions}\nКоличество окон: {windows}"))
            page.update()
        def compute_time_hash():
            r1, r2 = memo.measure_cache_performance()
            if isinstance(section_content.controls[-1], ft.Text):
                section_content.controls.pop()
            section_content.controls.append(ft.Text(f"Время первого прохода: {r1}\nВремя второго прохода (с кешем): {r2}"))
            page.update()

    # Async/FRP
    def show_async_frp_section():
        section_content.controls.clear()
        section_content.controls.append(ft.Text("FRP: Мини-шина событий", size=18, weight=ft.FontWeight.BOLD))

        def create_dropdown(label, items, width=300, text_func=None):
            options = [
                ft.dropdown.Option(item["id"], text=text_func(item) if text_func else item["id"])
                for item in items
            ]
            return ft.Dropdown(label=label, width=width, options=options)

        def publish_event_safe(event_name, payload):
            new_state = bus.publish(event_name, payload, dict(state))
            state.update(new_state)
            room_table.rows = build_room_table_rows()
            page.update()

        # ASSIGN_SLOT
        section_content.controls.append(ft.Text("Назначить слот занятию (ASSIGN_SLOT)"))
        assign_class_dropdown = create_dropdown("Выберите занятие", state["classes"])
        assign_slot_dropdown = create_dropdown(
            "Выберите слот", state["slots"], text_func=lambda s: f"{s['day']} {s['start']}-{s['end']}"
        )
        assign_slot_button = ft.ElevatedButton(
            "Назначить слот",
            on_click=lambda e: publish_event_safe(
                "ASSIGN_SLOT",
                {"class_id": assign_class_dropdown.value, "slot_id": assign_slot_dropdown.value},
            ),
        )
        section_content.controls.extend([assign_class_dropdown, assign_slot_dropdown, assign_slot_button, ft.Divider()])

        # MOVE_CLASS
        section_content.controls.append(ft.Text("Переместить занятие в другую аудиторию (MOVE_CLASS)"))
        move_class_dropdown = create_dropdown("Выберите занятие", state["classes"])
        move_room_dropdown = create_dropdown(
            "Выберите аудиторию",
            state["rooms"],
            text_func=lambda r: f"{r['name']} ({next(b['name'] for b in state['buildings'] if b['id']==r['building_id'])})"
        )
        move_class_button = ft.ElevatedButton(
            "Переместить занятие",
            on_click=lambda e: publish_event_safe(
                "MOVE_CLASS",
                {"class_id": move_class_dropdown.value, "new_room": move_room_dropdown.value},
            ),
        )
        section_content.controls.extend([move_class_dropdown, move_room_dropdown, move_class_button, ft.Divider()])

        # CANCEL_CLASS
        section_content.controls.append(ft.Text("Отменить занятие (CANCEL_CLASS)"))
        cancel_class_dropdown = create_dropdown("Выберите занятие", state["classes"])
        cancel_class_button = ft.ElevatedButton(
            "Отменить занятие",
            on_click=lambda e: publish_event_safe("CANCEL_CLASS", {"class_id": cancel_class_dropdown.value}),
        )
        section_content.controls.extend([cancel_class_dropdown, cancel_class_button, ft.Divider()])

        # ADD_ROOM
        section_content.controls.append(ft.Text("Добавить аудиторию (ADD_ROOM)"))
        room_id_field = ft.TextField(label="ID аудитории", width=200)
        room_name_field = ft.TextField(label="Название аудитории", width=300)
        room_building_dropdown = create_dropdown("Корпус", state["buildings"], text_func=lambda b: b["name"])
        room_capacity_field = ft.TextField(label="Вместимость", width=120)

        def add_room_action():
            capacity = int(room_capacity_field.value)
            payload = {
                "id": room_id_field.value,
                "name": room_name_field.value,
                "building_id": room_building_dropdown.value,
                "capacity": capacity,
                "features": [],
            }
            publish_event_safe("ADD_ROOM", payload)

        add_room_button = ft.ElevatedButton("Добавить аудиторию", on_click=lambda e: add_room_action())
        section_content.controls.extend([room_id_field, room_name_field, room_building_dropdown, room_capacity_field, add_room_button, ft.Divider()])

        # Таблица аудиторий
        section_content.controls.append(ft.Text("Занятость аудиторий", size=16, weight=ft.FontWeight.BOLD))
        room_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Аудитория")),
                ft.DataColumn(ft.Text("Корпус")),
                ft.DataColumn(ft.Text("Вместимость")),
                ft.DataColumn(ft.Text("Статус")),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.BLACK12),
            expand=True,
        )
        section_content.controls.append(room_table)

        def build_room_table_rows():
            rows = []
            for room in state["rooms"]:
                building_name = next((b["name"] for b in state["buildings"] if b["id"] == room["building_id"]), "")
                scheduled_classes = [
                    f"{c['id']} ({c.get('status','')})"
                    for c in state["classes"]
                    if c.get("room_id") == room["id"] and c.get("status") in ("scheduled", "moved")
                ]
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(room["name"])),
                            ft.DataCell(ft.Text(building_name)),
                            ft.DataCell(ft.Text(str(room.get("capacity", 0)))),
                            ft.DataCell(ft.Text(", ".join(scheduled_classes) if scheduled_classes else "Свободно")),
                        ]
                    )
                )
            return rows

        room_table.rows = build_room_table_rows()
        page.update()

    def show_reports_section():
        section_content.controls.clear()

        if not ensure_loaded(page, section_content):
            return

        section_content.controls.append(ft.Text("Генерация отчёта за период", size=18, weight=ft.FontWeight.BOLD))

        # period preset (week / month / custom)
        period_dropdown = ft.Dropdown(
            label="Период",
            width=220,
            options=[
                ft.dropdown.Option("week", text="Неделя"),
                ft.dropdown.Option("month", text="Месяц"),
                ft.dropdown.Option("custom", text="Выбор дней"),
            ],
            value="week",
        )

        # checkboxes for days (custom selection)
        day_checkboxes = {}
        for key, label in get_weekday_options():
            day_checkboxes[key] = ft.Checkbox(label=label, value=(key in ("monday", "tuesday", "wednesday", "thursday", "friday")))

        days_row = ft.Row([day_checkboxes[k] for k, _ in get_weekday_options()], wrap=True)
        
        # Period buttons
        generate_button = ft.ElevatedButton("Сформировать отчёт за период", on_click=None)
        status_text = ft.Text("", color=ft.Colors.BLACK87)
        out_area = ft.Column()

        def build_days_list() -> List[str]:
            kind = period_dropdown.value
            if kind == "week":
                return ["monday", "tuesday", "wednesday", "thursday", "friday"]
            if kind == "month":
                # for month we will run 4 weekly passes using the weekdays below
                return ["monday", "tuesday", "wednesday", "thursday", "friday"]
            # custom
            return [k for k, cb in day_checkboxes.items() if cb.value]

        async def run_period_report(e):
            generate_button.disabled = True
            status_text.value = "Генерация..."
            out_area.controls.clear()
            page.update()

            kind = period_dropdown.value

            # determine selected days
            if kind == "custom":
                selected_days = [k for k, cb in day_checkboxes.items() if cb.value]
            else:
                selected_days = build_days_list()

            if not selected_days:
                status_text.value = "Ни один день не выбран."
                generate_button.disabled = False
                page.update()
                return

            try:
                weeks_results = []
                if kind == "month":
                    # вызовем generate_period_report 4 раза — по одной итерации на каждую неделю месяца
                    # это позволит получить отчёты и обновленные занятия для каждой из 4 недель
                    for week_index in range(4):
                        status_text.value = f"Генерация: неделя {week_index+1}..."
                        page.update()
                        week_result = await generate_period_report(selected_days, state.get("classes", ()), state.get("rooms", ()), state.get("slots", ()), state.get("groups", ()))
                        weeks_results.append(week_result)
                else:
                    # week or custom — одна итерация
                    single = await generate_period_report(selected_days, state.get("classes", ()), state.get("rooms", ()), state.get("slots", ()), state.get("groups", ()))
                    weeks_results.append(single)
            except Exception as ex:
                status_text.value = f"Ошибка при генерации: {ex}"
                generate_button.disabled = False
                page.update()
                return

            # Update global schedule: collect updated classes from all weeks
            updated_by_id: Dict[str, Any] = {}
            for week_res in weeks_results:
                for day_res in week_res.get("days", []):
                    for c in day_res.get("classes", ()):  # classes returned per day
                        if hasattr(c, "__dict__") and not isinstance(c, dict):
                            updated_by_id[getattr(c, "id")] = c.__dict__
                        else:
                            updated_by_id[c["id"]] = c

            # Merge updated classes with any existing classes that were not returned
            existing = {c["id"]: c for c in state.get("classes", [])}
            merged = dict(existing)
            merged.update(updated_by_id)

            # Save back to state as list of dicts
            state["classes"] = list(merged.values())

            # Render results
            out_area.controls.clear()

            # For each week, render per-day reports
            for wi, week_res in enumerate(weeks_results):
                out_area.controls.append(ft.Text(f"Отчёт за неделю {wi+1}", weight=ft.FontWeight.BOLD))
                for day_res in week_res.get("days", []):
                    rep = day_res.get("report", {})
                    out_area.controls.append(ft.Text(f"  День: {day_res.get('day')}", weight=ft.FontWeight.BOLD))
                    out_area.controls.append(ft.Text(f"    Запланировано (slot_id present): {rep.get('scheduled_count')}"))
                    out_area.controls.append(ft.Text(f"    Назначено в этом запуске: {rep.get('assigned_this_run')}"))
                    out_area.controls.append(ft.Text(f"    Не назначено: {rep.get('unscheduled_count')}"))
                    out_area.controls.append(ft.Text(f"    Коллизий: {len(rep.get('collisions', []))}"))
                    if rep.get('collisions'):
                        for coll in rep.get('collisions', []):
                            if coll.get('type') == 'room_conflict':
                                out_area.controls.append(ft.Text(f"      Конфликт аудитории {coll.get('room_id')}: {coll.get('classes')}"))
                            else:
                                out_area.controls.append(ft.Text(f"      Конфликт преподавателя {coll.get('teacher_id')}: {coll.get('classes')}"))
                    if rep.get('assigned_ids'):
                        out_area.controls.append(ft.Text(f"    Назначенные занятия (ids): {', '.join(rep.get('assigned_ids'))}"))
                    if rep.get('unassigned_ids'):
                        out_area.controls.append(ft.Text(f"    Неназначенные занятия (ids): {', '.join(rep.get('unassigned_ids'))}"))
                    out_area.controls.append(ft.Divider())

            # Aggregated across all weeks
            total_agg = {
                'total_days': 0,
                'total_scheduled': 0,
                'total_assigned_this_run': 0,
                'total_unscheduled': 0,
                'total_collisions': 0,
            }
            for week_res in weeks_results:
                agg = week_res.get('aggregated', {})
                total_agg['total_days'] += agg.get('total_days', 0)
                total_agg['total_scheduled'] += agg.get('total_scheduled', 0)
                total_agg['total_assigned_this_run'] += agg.get('total_assigned_this_run', 0)
                total_agg['total_unscheduled'] += agg.get('total_unscheduled', 0)
                total_agg['total_collisions'] += agg.get('total_collisions', 0)

            out_area.controls.append(ft.Text("Итоговый сводный отчёт:", weight=ft.FontWeight.BOLD))
            out_area.controls.append(ft.Text(f"  Всего недель: {len(weeks_results)}"))
            out_area.controls.append(ft.Text(f"  Всего дней: {total_agg.get('total_days')}"))
            out_area.controls.append(ft.Text(f"  Всего запланировано: {total_agg.get('total_scheduled')}"))
            out_area.controls.append(ft.Text(f"  Всего назначено: {total_agg.get('total_assigned_this_run')}"))
            out_area.controls.append(ft.Text(f"  Всего не назначено: {total_agg.get('total_unscheduled')}"))
            out_area.controls.append(ft.Text(f"  Всего коллизий: {total_agg.get('total_collisions')}"))
            out_area.controls.append(ft.Divider())

            status_text.value = "Готово."
            generate_button.disabled = False
            page.update()

        # attach async handler (Flet supports async handlers)
        generate_button.on_click = run_period_report

        # assemble UI
        controls = [
            ft.Row([period_dropdown]),
            ft.Text("Если выбран 'Выбор дней', отметьте дни вручную:"),
            days_row,
            ft.Row([generate_button, status_text]),
            ft.Divider(),
            out_area,
        ]
        for c in controls:
            section_content.controls.append(c)
        page.update()

    # initially render
    update_section()

# entrypoint for flet
def main(page: ft.Page):
    main_page(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
