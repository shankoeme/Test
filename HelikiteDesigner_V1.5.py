import math
import numpy as np
import flet as ft
import flet.canvas as cv

# ==================================================
# Pure Python 3D Ellipsoid Wireframe Generator
# ==================================================
def generate_ellipsoid_points(L, W, H, u_div, v_div):
    a, b, c = L / 2, W / 2, H / 2
    u_div, v_div = int(u_div), int(v_div)
    
    nodes = []
    lines = []

    for j in range(v_div + 1):
        theta = np.pi * j / v_div
        for i in range(u_div):
            phi = 2 * np.pi * i / u_div
            x = a * np.sin(theta) * np.cos(phi)
            y = b * np.sin(theta) * np.sin(phi)
            z = c * np.cos(theta)
            nodes.append([x, y, z])

    for j in range(v_div):
        for i in range(u_div):
            p1 = j * u_div + i
            p2 = j * u_div + (i + 1) % u_div
            p3 = (j + 1) * u_div + i
            lines.append((p1, p2))
            lines.append((p1, p3))

    return np.array(nodes), lines

def theoretical_surface_area(a, b, c):
    p = 1.6075
    return 4 * math.pi * (((a*b)**p + (a*c)**p + (b*c)**p) / 3) ** (1/p)

# ==================================================
# Fast & Smooth Flet 3D Canvas App
# ==================================================
def main(page: ft.Page):
    page.title = "Helikite 3D Designer (Mobile)"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 15

    # Camera & Transform States
    rot_x = [0.4]
    rot_y = [0.6]
    zoom_scale = [25.0]

    cached_nodes = [None]
    cached_lines = [None]

    # UI Inputs
    vol_input = ft.TextField(label="Target Volume (m³)", value="50.0", keyboard_type=ft.KeyboardType.NUMBER)
    l_input = ft.TextField(label="Length (m)", value="4.6", keyboard_type=ft.KeyboardType.NUMBER)
    w_input = ft.TextField(label="Width (m)", value="4.6", keyboard_type=ft.KeyboardType.NUMBER)
    h_input = ft.TextField(label="Height (m)", value="2.88", keyboard_type=ft.KeyboardType.NUMBER)
    lh_input = ft.TextField(label="L/H Ratio", value="1.6", keyboard_type=ft.KeyboardType.NUMBER)
    wh_input = ft.TextField(label="W/H Ratio", value="1.6", keyboard_type=ft.KeyboardType.NUMBER)

    fabric_density = ft.TextField(label="Fabric Density (kg/m²)", value="0.1", keyboard_type=ft.KeyboardType.NUMBER)
    he_lift = ft.TextField(label="Helium Lift (kg/m³)", value="1.046", keyboard_type=ft.KeyboardType.NUMBER)

    u_div = ft.TextField(label="U Division", value="16", keyboard_type=ft.KeyboardType.NUMBER)
    v_div = ft.TextField(label="V Division", value="8", keyboard_type=ft.KeyboardType.NUMBER)

    mode_switch = ft.Switch(label="Target Volume Mode Switch", value=False)
    output_text = ft.Text(value="Results will appear here...", font_family="monospace", size=13)

    canvas = cv.Canvas(width=350, height=300)

    zoom_slider = ft.Slider(min=10.0, max=60.0, value=25.0, label="Zoom: {value}", expand=True)

    def draw_cached_3d():
        if cached_nodes[0] is None:
            return

        canvas.shapes.clear()
        
        angle_x, angle_y, scale = rot_x[0], rot_y[0], zoom_scale[0]
        
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(angle_x), -np.sin(angle_x)],
            [0, np.sin(angle_x), np.cos(angle_x)]
        ])
        Ry = np.array([
            [np.cos(angle_y), 0, np.sin(angle_y)],
            [0, 1, 0],
            [-np.sin(angle_y), 0, np.cos(angle_y)]
        ])

        rotated = cached_nodes[0] @ Rx.T @ Ry.T
        
        cx, cy = 175, 150

        proj_x = cx + rotated[:, 0] * scale
        proj_y = cy - rotated[:, 2] * scale

        for p1, p2 in cached_lines[0]:
            canvas.shapes.append(
                cv.Line(
                    proj_x[p1], proj_y[p1], proj_x[p2], proj_y[p2],
                    paint=ft.Paint(color="cyan", stroke_width=1)
                )
            )
        canvas.update()

    def update_geometry_and_calc(e=None):
        try:
            L = float(l_input.value)
            W = float(w_input.value)
            H = float(h_input.value)

            if mode_switch.value:
                V = float(vol_input.value)
                FR = float(lh_input.value)
                TR = float(wh_input.value)
                H = (6 * V / (math.pi * FR * TR)) ** (1/3)
                L = FR * H
                W = TR * H
                l_input.value = f"{L:.3f}"
                w_input.value = f"{W:.3f}"
                h_input.value = f"{H:.3f}"
                page.update()

            nodes, lines = generate_ellipsoid_points(L, W, H, u_div.value, v_div.value)
            cached_nodes[0] = nodes
            cached_lines[0] = lines

            draw_cached_3d()

            vol = (math.pi / 6) * L * W * H
            theory_area = theoretical_surface_area(L/2, W/2, H/2)
            gross_lift = vol * float(he_lift.value)
            envelope_weight = theory_area * float(fabric_density.value)

            output_text.value = f"""--- HELIKITE SPECS ---
L: {L:.2f}m | W: {W:.2f}m | H: {H:.2f}m
Volume       : {vol:.2f} m³
Surface Area : {theory_area:.2f} m²
Gross Lift   : {gross_lift:.2f} kg
Net Payload  : {(gross_lift - envelope_weight):.2f} kg"""
        except Exception as err:
            output_text.value = f"Error: {err}"
        page.update()

    def on_pan_update(e: ft.DragUpdateEvent):
        rot_y[0] += e.delta_x * 0.008
        rot_x[0] += e.delta_y * 0.008
        draw_cached_3d()

    def on_zoom_change(e):
        zoom_scale[0] = zoom_slider.value
        draw_cached_3d()

    def reset_camera(e):
        rot_x[0] = 0.4
        rot_y[0] = 0.6
        zoom_scale[0] = 25.0
        zoom_slider.value = 25.0
        draw_cached_3d()

    zoom_slider.on_change = on_zoom_change

    gesture_container = ft.GestureDetector(
        content=ft.Container(
            content=canvas,
            bgcolor="#1e272e",
            border_radius=10,
            alignment=ft.alignment.center
        ),
        on_pan_update=on_pan_update
    )

    calc_btn = ft.ElevatedButton("Update Geometry & Calculate", on_click=update_geometry_and_calc, icon=ft.Icons.REFRESH)
    reset_cam_btn = ft.IconButton(icon=ft.Icons.CENTER_FOCUS_STRONG, tooltip="Reset Camera View", on_click=reset_camera)

    page.add(
        ft.Text("Helikite 3D Mobile Designer", size=20, weight=ft.FontWeight.BOLD),
        mode_switch,
        ft.Row([l_input, w_input, h_input]),
        ft.Row([vol_input, lh_input, wh_input]),
        ft.Row([fabric_density, he_lift]),
        ft.Row([u_div, v_div]),
        calc_btn,
        ft.Divider(),
        ft.Row([
            ft.Text("3D View Controls", size=14, weight=ft.FontWeight.BOLD),
            reset_cam_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        gesture_container,
        ft.Row([
            ft.Icon(ft.Icons.ZOOM_OUT, size=18),
            zoom_slider,
            ft.Icon(ft.Icons.ZOOM_IN, size=18)
        ]),
        ft.Container(content=output_text, bgcolor="black12", padding=10, border_radius=8)
    )

    update_geometry_and_calc()

# Flet Version အားလုံးတွင် အဆင်ပြေစေမည့် Universal Runner
if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "run_app"):
        ft.run_app(main)
    else:
        ft.app(target=main)