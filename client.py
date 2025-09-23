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

    popup = ft.PopupMenuButton(items=[
            ft.PopupMenuItem(icon= MENU_ICONS[0], text=MENU[0], on_click=lambda _: switch_section(MENU[0])),
            ft.PopupMenuItem(icon= MENU_ICONS[1], text=MENU[1], on_click=lambda _: switch_section(MENU[1])),
            ft.PopupMenuItem(icon= MENU_ICONS[2], text=MENU[2], on_click=lambda _: switch_section(MENU[2])),
            ft.PopupMenuItem(icon= MENU_ICONS[3], text=MENU[3], on_click=lambda _: switch_section(MENU[3])),
            ft.PopupMenuItem(icon= MENU_ICONS[4], text=MENU[4], on_click=lambda _: switch_section(MENU[4])),
            ft.PopupMenuItem(icon= MENU_ICONS[5], text=MENU[5], on_click=lambda _: switch_section(MENU[5])),
            ft.PopupMenuItem(icon= MENU_ICONS[6], text=MENU[6], on_click=lambda _: switch_section(MENU[6])),
            ft.PopupMenuItem(icon= MENU_ICONS[7], text=MENU[7], on_click=lambda _: switch_section(MENU[7]))
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
        padding=20
    )


    page.add(
        ft.Row(
            [popup, main_content_container],
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