# client.py
import flet as ft
import httpx
from typing import Optional

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

    # ---------------------- helpers for mapping ids -> names ----------------------
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

        # UI controls
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

        clear_button = ft.ElevatedButton("Сбросить фильтры", on_click=lambda e: on_clear())

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

    # initially render
    update_section()


# entrypoint for flet
def main(page: ft.Page):
    main_page(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
