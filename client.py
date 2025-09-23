import flet as ft
import httpx

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

state = {}


def main_page(page: ft.Page):
    page.title = "Расписание"
    page.bgcolor = ft.Colors.WHITE
    page.scroll = ft.ScrollMode.AUTO

    section_name = ft.Text(
        "Overview", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87
    )
    section_content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    sidebar_open = True

    def toggle_sidebar():
        nonlocal sidebar_open
        sidebar_open = not sidebar_open
        sidebar_container.width = 200 if sidebar_open else 50

        for btn, label, icon in zip(sidebar_buttons, MENU, MENU_ICONS):
            btn.content = ft.Row(
                [
                    ft.Icon(icon, size=22),
                    ft.Text(label, size=14) if sidebar_open else ft.Container(width=0),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            )
        page.update()

    toggle_btn = ft.IconButton(
        icon=ft.Icons.MENU,
        icon_color=ft.Colors.BLACK87,
        on_click=lambda e: toggle_sidebar(),
    )

    sidebar_buttons = []
    for label, icon in zip(MENU, MENU_ICONS):
        btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(icon, size=24), ft.Text(label, size=14)],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            bgcolor=ft.Colors.BLUE_400,
            color=ft.Colors.BLACK87,
            width=180,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
            on_click=lambda e, name=label: switch_section(name),
        )
        sidebar_buttons.append(btn)

    sidebar_column = ft.Column(
        [toggle_btn, *sidebar_buttons],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    sidebar_container = ft.Container(
        content=sidebar_column,
        width=200,
        bgcolor=ft.Colors.WHITE,
        padding=10,
        animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
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
        animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
    )


    page.add(
        ft.Row(
            [sidebar_container, main_content_container],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )

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
                    "Это проект программы, помогающей составлять расписание для университетов.\n\nАвторы:\nАлуа Кизатбаева\nДемид Метельников\nДильшат Сембаев", color=ft.Colors.BLACK87
                )
            )
        else:
            section_content.controls.append(
                ft.Text(
                    "Тут пока ещё пусто. :)", color=ft.Colors.BLACK87
                )
            )
        page.update()

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

        table1_rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(z["id"], color=ft.Colors.BLACK87)),
                    ft.DataCell(ft.Text(z["name"], color=ft.Colors.BLACK87)),
                ]
            )
            for z in state["buildings"]
        ]
        table1_title = ft.Text("Корпуса", size=24, weight=ft.FontWeight.BOLD)
        table1 = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Название корпуса"))],
            rows=table1_rows,
            border=ft.border.all(1, ft.Colors.BLACK12),
            heading_row_color="#358FC1",
            heading_text_style=ft.TextStyle(
                weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE
            ),
        )
        table2_title = ft.Text("Аудитории", size=24, weight=ft.FontWeight.BOLD)
        table2_rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(z["id"], color=ft.Colors.BLACK87)),
                    ft.DataCell(ft.Text(z["building_id"], color=ft.Colors.BLACK87)),
                    ft.DataCell(ft.Text(z["name"], color=ft.Colors.BLACK87)),
                    ft.DataCell(ft.Text(z["capacity"], color=ft.Colors.BLACK87)),
                    ft.DataCell(ft.Text(z["features"], color=ft.Colors.BLACK87)),
                ]
            )
            for z in state["rooms"]
        ]
        table2 = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Корпус")), ft.DataColumn(ft.Text("Номер")), ft.DataColumn(ft.Text("Вместимость")), ft.DataColumn(ft.Text("Дополнительные условия"))],
            rows=table2_rows,
            border=ft.border.all(1, ft.Colors.BLACK12),
            heading_row_color="#358FC1",
            heading_text_style=ft.TextStyle(
                weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE
            ),
        )
        table3_title = ft.Text("Преподаватели", size=24, weight=ft.FontWeight.BOLD)
        table3_rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(z["id"], color=ft.Colors.BLACK87)),
                    ft.DataCell(ft.Text(z["name"], color=ft.Colors.BLACK87)),
                    ft.DataCell(ft.Text(z["dept"], color=ft.Colors.BLACK87)),
                ]
            )
            for z in state["teachers"]
        ]
        table3 = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Имя")), ft.DataColumn(ft.Text("Кафедра"))],
            rows=table3_rows,
            border=ft.border.all(1, ft.Colors.BLACK12),
            heading_row_color="#358FC1",
            heading_text_style=ft.TextStyle(
                weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE
            ),
        )
        section_content.controls.append(table1_title); section_content.controls.append(table1); section_content.controls.append(table2_title); section_content.controls.append(table2); section_content.controls.append(table3_title); section_content.controls.append(table3)
        page.update()

    def show_data_section():
        async def load_data(e):
            section_content.controls.clear()
            section_content.controls.append(
                ft.Text("Загрузка...", color=ft.Colors.BLACK87)
            )
            page.update()

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{BACKEND_URL}/load_seed")
                    result = response.json()
                    r = await client.get(f"{BACKEND_URL}/data")
                    data = r.json()
                    state.update(data)

                section_content.controls.clear()
                section_content.controls.append(
                    ft.Text(
                        "Данные успешно загружены!",
                        color=ft.Colors.BLACK87,
                    )
                )
            except Exception as e:
                section_content.controls.clear()
                section_content.controls.append(
                    ft.Text(f"Возникла ошикбка: {e}. Возможно, отсутствует соединение с сервером или данные некорректны.", color=ft.Colors.RED)
                )
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