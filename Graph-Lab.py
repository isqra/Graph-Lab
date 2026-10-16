import tkinter as tk
from tkinter import ttk, messagebox
import math

root = tk.Tk()
root.title("Построение графа")
root.geometry("850x650")

R = 20
vertices = {}
edges = [] # Неориентированные рёбра
arcs = [] # Ориентированные дуги
edge_labels = {}
highlighted_connection = None

selected = None
dragging = None
mode = "add"

graph_type = "Неориентированный"

# ---------------- ИНТЕРФЕЙС ----------------

top = tk.Frame(root)
top.pack(fill="x", padx=10, pady=5)

tk.Label(top, text="Тип графа:").pack(side="left")

graph_type_var = tk.StringVar(value=graph_type)

type_menu = tk.OptionMenu(
    top,
    graph_type_var,
    "Неориентированный",
    "Ориентированный",
    command=lambda value: change_graph_type(value)
)

type_menu.pack(side="left", padx=5)

canvas = tk.Canvas(root, bg="white")
canvas.pack(fill="both", expand=True)

info = tk.Label(
    root,
    justify="left",
    anchor="w",
    font=("Arial", 10)
)
info.pack(fill="x", padx=10, pady=5)

status = tk.Label(root, text="Режим: Добавить вершины")
status.pack(fill="x", padx=10, pady=3)

# ---------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------

def is_directed():
    return graph_type_var.get() == "Ориентированный"

def current_connections():
    """ Возвращает связи текущего типа графа."""
    return arcs if is_directed() else edges

def get_adjacency_matrix():
    nodes = sorted(vertices)
    index = {v: i for i, v in enumerate(nodes)}
    matrix = [[0] * len(nodes) for _ in nodes]

    for a, b in current_connections():
        i, j = index[a], index[b]
        matrix[i][j] = 1

        if not is_directed():
            matrix[j][i] = 1

    return nodes, matrix

def get_incidence_matrix():
    nodes = sorted(vertices)
    connections = current_connections()
    labels = [edge_labels.get(c, "") for c in connections]
    matrix = []

    for v in nodes:
        row = []

        for a, b in connections:
            if is_directed():
                if v == a:
                    row.append(1)
                elif v == b:
                    row.append(-1)
                else:
                    row.append(0)
            else:
                row.append(1 if v == a or v == b else 0)

        matrix.append(row)
    return nodes, labels, matrix

def show_adjacency_matrix():
    window = tk.Toplevel(root)
    window.title("Матрица смежности")
    window.geometry("555x444")

    table_frame = tk.Frame(window)
    table_frame.pack(fill="both", expand=True)

    def refresh():
        for widget in table_frame.winfo_children():
            widget.destroy()
        nodes, matrix = get_adjacency_matrix()

        table = ttk.Treeview(
            table_frame,
            columns=[str(v) for v in nodes],
            show="headings",
        )

        for v in nodes:
            table.heading(str(v), text=str(v))
            table.column(str(v), width=45, anchor="center")
        table.pack(fill="both", expand=True)
        for i, v in enumerate(nodes):
            table.insert("", "end", iid=str(v), values=matrix[i])

        def select_cell(event):
            global highlighted_connection

            row_id = table.identify_row(event.y)
            col_id = table.identify_column(event.x)

            if not row_id or not col_id:
                return

            k = int(col_id[1:]) - 1
            if k < 0 or k >= len(nodes):
                return
            a = int(row_id)
            b = nodes[k]
            i = nodes.index(a)

            if a == b or matrix[i][k] == 0:
                highlighted_connection = None
            elif is_directed():
                highlighted_connection = (a, b)
            else:
                highlighted_connection = tuple(sorted((a, b)))

            redraw()

        table.bind("<ButtonRelease-1>", select_cell)

    refresh()

def show_incidence_matrix():
    window = tk.Toplevel(root)
    window.title("Матрица инцидентности")
    window.geometry("555x444")

    nodes, labels, matrix = get_incidence_matrix()

    columns = ["Вершина"] + labels

    table = ttk.Treeview(
        window,
        columns=columns,
        show="headings"
    )

    for col in columns:
        table.heading(col, text=col)
        table.column(col, width=65, anchor="center")

    for i, v in enumerate(nodes):
        table.insert(
            "",
            "end",
            values=[v] + matrix[i]
        )

    table.pack(fill="both", expand=True)

def vertex_at(x, y):
    for v, (vx, vy) in vertices.items():
        if (x-vx)**2 + (y-vy)**2 <= R**2:
            return v
    return None

def change_graph_type(new_type):
    """Меняет тип графа, не удаляя вершины."""
    global graph_type, selected, dragging, highlighted_connection

    if new_type == graph_type:
        return

    if edges or arcs:
        answer = messagebox.askyesno(
            "Смена типа графа",
            "При смене типа графа все существующие связи "
            "будут удалены. \n\nПродолжить?"
        )
        if not answer:
            graph_type_var.set(graph_type)
            return
    edges.clear()
    arcs.clear()
    edge_labels.clear()
    highlighted_connection = None

    graph_type = new_type
    selected = None
    dragging = None

    set_mode("add")

def redraw():
    canvas.delete("all")

    directed = is_directed()

    for conn in current_connections():
        a, b = conn
        x1, y1 = vertices[a]
        x2, y2 = vertices[b]

        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        if length == 0:
            continue

        ux = dx / length
        uy = dy / length

        start_x = x1 + ux * R
        start_y = y1 + uy * R

        is_highlighted = (conn == highlighted_connection)
        color = "red" if is_highlighted else "black"
        width = 4 if is_highlighted else 2

        if directed:
            end_x = x2 - ux * (R + 5)
            end_y = y2 - uy * (R + 5)
            canvas.create_line(
                start_x, start_y, end_x, end_y,
                width=width,
                fill=color,
                arrow=tk.LAST,
                arrowshape=(12, 15, 5)
            )
        else:
            end_x = x2 - ux * R
            end_y = y2 - uy * R
            canvas.create_line(
                start_x, start_y, end_x, end_y,
                width=width,
                fill=color
            )

        # Подпись ребра/дуги у середины линии
        label = edge_labels.get(conn)
        if label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            canvas.create_text(
                mid_x, mid_y - 10,
                text=label,
                fill="darkgreen",
                font=("Arial", 9, "bold")
            )

    for v, (x, y) in vertices.items():
        color = "orange" if v == selected else "lightblue"
        canvas.create_oval(
            x - R, y - R,
            x + R, y + R,
            fill=color,
            outline="black",
            width=2
        )
        canvas.create_text(
            x, y,
            text=str(v),
            font=("Arial", 10)
        )

def update():
    if is_directed():
        in_degrees = {v: 0 for v in vertices}
        out_degrees = {v: 0 for v in vertices}

        for a, b in arcs:
            out_degrees[a] += 1
            in_degrees[b] += 1

        total_in = sum(in_degrees.values())
        total_out = sum(out_degrees.values())

        info.config(text=
            f"Тип: Ориентированный граф\n"
            f"Вершин: {len(vertices)}/100 | "
            f"Рёбер: {len(edges)}/500 | "
            f"Дуг: {len(arcs)}/500\n"
            f"Полустепени захода: {in_degrees}\n"
            f"Полустепени исхода: {out_degrees}\n"
            f"Сумма полустепеней захода: {total_in}\n"
            f"Сумма полустепеней исхода: {total_out}\n"
            f"Количество дуг: {len(arcs)}\n"
            f"Проверка: "
            f"{'ВЕРНА' if total_in == total_out == len(arcs) else 'ОШИБКА'}"
        )

    else:
        degrees = {v: 0 for v in vertices}

        for a, b in edges:
            degrees[a] += 1
            degrees[b] += 1

        total = sum(degrees.values())

        info.config(text=(
            f"Тип: Неориентированный граф\n"
            f"Вершин: {len(vertices)}/100 | "
            f"Рёбер: {len(edges)}/500 | "
            f"Дуг: {len(arcs)}/500\n"
            f"Степени вершин: {degrees}\n"
            f"Сумма степеней: {total}\n"
            f"2 × количество рёбер: {2 * len(edges)}\n"
            f"Лемма о рукопожатиях: "
            f"{'ВЕРНА' if total == 2 * len(edges) else 'ОШИБКА'}"
        ))


def set_mode(new_mode):
    global mode, selected, dragging

    mode = new_mode
    selected = None
    dragging = None

    if mode == "add":
        name = "Добавление вершин"
    elif mode == "edge":
        name = (
            "Добавление дуг"
            if is_directed()
            else "Добавление рёбер"
        )
    elif mode == "move":
        name = "Перемещение вершин"
    elif mode == "delete_edge":
        name = (
            "Удаление дуг"
            if is_directed()
            else "Удаление рёбер"
        )
    else:
        name = "Удаление вершин"

    status.config(text="Режим: " + name)

    redraw()
    update()

def next_free_vertex_id():
    n = 1
    while n in vertices:
        n += 1
    return n


def next_free_edge_label():
    used = set(edge_labels.values())
    n = 1
    while f"e{n}" in used:
        n += 1
    return f"e{n}"

def click(event):
    global selected, dragging, highlighted_connection

    v = vertex_at(event.x, event.y)

    # Добавление вершин
    if mode == "add":
        if v is not None:
            return

        if len(vertices) >= 100:
            messagebox.showwarning(
                "Ошибка", "Максимум 100 вершин!"
            )
            return

        x, y = event.x, event.y

        for vx, vy in vertices.values():
            if (x-vx)**2 + (y-vy)**2 < (2*R+5)**2:
                messagebox.showinfo(
                    "Граф", "Вершины слишком близко!"
                )
                return

        vertices[next_free_vertex_id()] = (x, y)

        redraw()
        update()
        return

    if v is None:
        selected = None
        redraw()
        return

    # Добавление рёбер или дуг
    if mode == "edge":
        if selected is None:
            selected = v

        elif selected == v:
            selected = None

        else:
            if is_directed():
                connection = (selected, v)
            else:
                connection = tuple(sorted((selected, v)))

            connections = current_connections()

            if connection in connections:
                messagebox.showinfo(
                    "Граф", "Такая связь уже существует!"
                )
            elif len(connections) >= 500:
                messagebox.showwarning(
                    "Ошибка", "Максимум 500 связей!"
                )
            else:
                connections.append(connection)
                edge_labels[connection] = next_free_edge_label()

            selected = None

        redraw()
        update()
        return

    # Удаление рёбер или дуг
    if mode == "delete_edge":
        if selected is None:
            selected = v

        elif selected == v:
            selected = None

        else:
            if is_directed():
                connection = (selected, v)
            else:
                connection = tuple(sorted((selected, v)))

            connections = current_connections()

            if connection in connections:
                connections.remove(connection)
                edge_labels.pop(connection, None)
                if highlighted_connection == connection:
                    highlighted_connection = None
            else:
                messagebox.showinfo(
                    "Граф", "Такая связь не существует!"
                )

            selected = None

        redraw()
        update()
        return

    # Удаление вершины и связанных с ней рёбер/дуг
    if mode == "delete_vertex":
        del vertices[v]

        edges[:] = [e for e in edges if v not in e]
        arcs[:] = [a for a in arcs if v not in a]

        for conn in list(edge_labels):
            if v in conn:
                del edge_labels[conn]
        if highlighted_connection is not None and v in highlighted_connection:
            highlighted_connection = None


        selected = None
        redraw()
        update()
        return

    # Перемещение вершины
    if mode == "move":
        dragging = v
        selected = v
        redraw()



def move_vertex(event):
    global dragging

    if mode != "move" or dragging is None:
        return

    x, y = event.x, event.y

    for v, (vx, vy) in vertices.items():
        if v == dragging:
            continue

        distance_squared = (x - vx) ** 2 + (y - vy) ** 2

        if distance_squared < (2 * R + 5) ** 2:
            return

    vertices[dragging] = (x, y)
    redraw()

def release(event):
    global dragging
    dragging = None
    update()


buttons = tk.Frame(root)
buttons.pack(fill="x", pady=5)

for text, value in [
    ("Добавить вершины", "add"),
    ("Соединить рёбра", "edge"),
    ("Перемещать вершины", "move"),
    ("Удалить ребро", "delete_edge"),
    ("Удалить вершину", "delete_vertex")
]:
    tk.Button(
        buttons,
        text=text,
        command=lambda m=value: set_mode(m)
    ).pack(side="left", padx=3)

matrix_buttons = tk.Frame(root)
matrix_buttons.pack(fill="x", pady=5)

tk.Button(
    matrix_buttons,
    text="Матрица смежности",
    command=show_adjacency_matrix
).pack(side="left", padx=5)

tk.Button(
    matrix_buttons,
    text="Матрица инцидентности",
    command=show_incidence_matrix
).pack(side="left", padx=5)

canvas.bind("<Button-1>", click)
canvas.bind("<B1-Motion>", move_vertex)
canvas.bind("<ButtonRelease-1>", release)

redraw()
update()
root.mainloop()