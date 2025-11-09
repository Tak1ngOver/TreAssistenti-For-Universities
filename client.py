# client.py
import flet as ft
import httpx
from typing import Optional

from core import transforms, memo
from core.domain import *

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
            section_content.controls.clear()
            cls_id = ft.TextField(label="Идентификатор занятия")
            cls_course = ft.TextField(label="Идентификатор дисциплины")
            cls_status = ft.AutoComplete(suggestions = [
                ft.AutoCompleteSuggestion(key="planned запланировано план", value="planned"),
                ft.AutoCompleteSuggestion(key="scheduled по расписанию", value="scheduled"),
                ft.AutoCompleteSuggestion(key="cancelled отменено отмена", value="cancelled"),
                ], 
                on_select=lambda e: print(e.selection),
            )

            cls_teacher = ft.TextField(label="Идентификатор преподавателя")
            cls_group = ft.TextField(label="Идентификатор учебной группы")
            cls_slot = ft.TextField(label="Идентификатор слота")
            cls_room = ft.TextField(label="Идентификатор аудитории")
            back_button = ft.ElevatedButton("Назад", on_click=lambda _: show_overview())
            submit_button = ft.ElevatedButton("Продолжить", on_click=lambda _: tryadd_new_class())

            section_content.controls.append(ft.Text("Введите данные нового занятия"))
            section_content.controls.append(cls_id)
            section_content.controls.append(cls_course)
            section_content.controls.append(cls_teacher)
            section_content.controls.append(cls_group)
            section_content.controls.append(cls_slot)
            section_content.controls.append(cls_room)
            section_content.controls.append(ft.Text("Статус занятия"))
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
                                status = cls_status.suggestions[cls_status.selected_index].value)
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


    # initially render
    update_section()


# entrypoint for flet
def main(page: ft.Page):
    main_page(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
