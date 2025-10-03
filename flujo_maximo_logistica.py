import json
import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# MaxFlow App
class ElMaxiFlujo:
    def __init__(self, n_nodos):
        self.n_nodos = n_nodos
        self.la_red = [dict() for _ in range(n_nodos)]

    # funcion para agregar un arco con capacidad
    def pon_arco(self, u, v, cap):
        if cap < 0:
            raise ValueError("La capacidad no puede ser negativa, obvio")
        # ver si ya existe el nodo
        self.la_red[u][v] = self.la_red[u].get(v, 0.0) + float(cap)

    # busqueda del grafo en anchura (BFS) para encontrar camino aumentante
    def _busqueda(self, s, t, el_papa):
        fue_visitado = [False] * self.n_nodos
        la_cola = [s]
        fue_visitado[s] = True
        el_papa[:] = [(-1, None)] * self.n_nodos
        while la_cola:
            u = la_cola.pop(0) # Siempre el primero
            for v, cap_res in self.la_red[u].items():
                if not fue_visitado[v] and cap_res > 1e-12: # revisar si todavia hay espacio
                    fue_visitado[v] = True
                    el_papa[v] = (u, cap_res)
                    if v == t:
                        return True
                    la_cola.append(v)
        return False

    # calculo del flujo maximo con Edmonds-Karp (Ford-Fulkerson con BFS)
    def calcula_el_maximo(self, s, t):
        if s == t:
            return 0.0, {}
        # chequeo basico de indices
        if not (0 <= s < self.n_nodos and 0 <= t < self.n_nodos):
            raise ValueError("Indices de origen/sumidero fuera de rango, ¡fijate bien!")

        # asegurar que todos los arcos tengan su reverso en la_red (con capacidad residual 0)
        for u in range(self.n_nodos):
            for v in list(self.la_red[u].keys()):
                self.la_red[v].setdefault(u, 0.0)

        el_papa = [(-1, None)] * self.n_nodos
        max_flujo = 0.0

        # guardamos la red inicial (la_red) para calcular el flujo final por arco.
        la_red_inicial = [dict(d) for d in self.la_red]

        while self._busqueda(s, t, el_papa):
            # encontrar el cuello de botella
            cap_camino = float('inf')
            v = t
            while v != s:
                u, cap_actual = el_papa[v]
                cap_camino = min(cap_camino, cap_actual)
                v = u
            # mandar mas flujo por ese camino
            v = t
            while v != s:
                u, _ = el_papa[v]
                # quitar capacidad adelante porque ya la usamos
                self.la_red[u][v] -= cap_camino
                # poner capacidad reversa para devolver si hace falta
                self.la_red[v][u] += cap_camino
                v = u
            max_flujo += cap_camino # acumular al maximo flujo

        # calcular el flujo neto por cada arco original
        mapa_flujo = {}
        for u in range(self.n_nodos):
            for v, cap0 in la_red_inicial[u].items():
                if cap0 > 1e-12:
                    flujo_enviado = self.la_red[v][u]
                    if flujo_enviado > 1e-12:
                        mapa_flujo[(u, v)] = flujo_enviado
                    else:
                        mapa_flujo[(u, v)] = 0.0

        return max_flujo, mapa_flujo


# Mi grafico
class ElModeloDelGrafo:
    def __init__(self):
        self.los_nodos = []
        self.los_arcos = []
        self.nombre_a_id = {}
        self.sig_nombre_idx = 0

    def pon_nodo(self, x, y, nombre=None):
        if nombre is None:
            nombre = f"N{self.sig_nombre_idx}"
            self.sig_nombre_idx += 1
        if nombre in self.nombre_a_id:
            raise ValueError("Ya existe un nodo con ese nombre, ¡cambialo!")
        nid = len(self.los_nodos)
        self.los_nodos.append((x, y, nombre))
        self.nombre_a_id[nombre] = nid
        return nid

    def cambia_nombre_nodo(self, nid, nuevo_nombre):
        if nuevo_nombre in self.nombre_a_id and self.nombre_a_id[nuevo_nombre] != nid:
            raise ValueError("Nombre de nodo ya en uso, ¡se mas creativo!")
        x, y, _ = self.los_nodos[nid]
        viejo_nombre = self.los_nodos[nid][2]
        self.los_nodos[nid] = (x, y, nuevo_nombre)
        del self.nombre_a_id[viejo_nombre]
        self.nombre_a_id[nuevo_nombre] = nid

    def mueve_nodo(self, nid, x, y):
        n = self.los_nodos[nid]
        self.los_nodos[nid] = (x, y, n[2])

    def quita_nodo(self, nid):
        # Quitar arcos asociados
        self.los_arcos = [(u, v, c) for (u, v, c) in self.los_arcos if u != nid and v != nid]
        # Reindexar: toca reajustar los indices de todos
        los_nodos_viejos = self.los_nodos
        self.los_nodos = []
        self.nombre_a_id = {}
        el_mapa = {}
        for i, (x, y, nombre) in enumerate(los_nodos_viejos):
            if i == nid:
                continue
            nuevo_id = len(self.los_nodos)
            self.los_nodos.append((x, y, nombre))
            self.nombre_a_id[nombre] = nuevo_id
            el_mapa[i] = nuevo_id
        # Reajustar arcos
        los_arcos_nuevos = []
        for (u, v, c) in self.los_arcos:
            los_arcos_nuevos.append((el_mapa[u], el_mapa[v], c))
        self.los_arcos = los_arcos_nuevos

    def pon_arco(self, u, v, capacidad):
        if u == v:
            raise ValueError("No se permiten lazos (u = v), ¡separa los nodos!")
        # si ya existe
        for i, (a, b, c) in enumerate(self.los_arcos):
            if a == u and b == v:
                self.los_arcos[i] = (a, b, c + float(capacidad))
                return
        self.los_arcos.append((u, v, float(capacidad)))

    def actualiza_capacidad(self, u, v, nueva_cap):
        for i, (a, b, c) in enumerate(self.los_arcos):
            if a == u and b == v:
                self.los_arcos[i] = (a, b, float(nueva_cap))
                return True
        return False

    def quita_arco(self, u, v):
        self.los_arcos = [(a, b, c) for (a, b, c) in self.los_arcos if not (a == u and b == v)]

    def exporta_json(self, ruta):
        datos = {
            "nodos": [{"id": i, "nombre": n[2], "x": n[0], "y": n[1]} for i, n in enumerate(self.los_nodos)],
            "arcos": [{"u": u, "v": v, "capacidad": c} for (u, v, c) in self.los_arcos],
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

    def importa_json(self, ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        self.los_nodos = []
        self.nombre_a_id = {}
        for nd in datos.get("nodos", []):
            x, y, nombre = nd["x"], nd["y"], nd["nombre"]
            self.pon_nodo(x, y, nombre)
        self.los_arcos = []
        for ed in datos.get("arcos", []):
            self.los_arcos.append((int(ed["u"]), int(ed["v"]), float(ed["capacidad"])))

        self.sig_nombre_idx = 0
        for n in self.los_nodos:
            if n[2].startswith("N"):
                try:
                    idx = int(n[2][1:])
                    self.sig_nombre_idx = max(self.sig_nombre_idx, idx + 1)
                except:
                    pass


# Interfaz grafica con Tkinter
RADIO_NODO = 18

class LaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MaxFlow - Tu App de Logistica (Edmonds–Karp)")
        # resolucion de la ventana
        self.geometry("1440x920")

        self.el_modelo = ElModeloDelGrafo()
        self.id_origen = None
        self.id_sumidero = None

        self._crea_interfaz()
        self._enlaza_eventos()

        self.arco_pendiente_desde = None

        self.ultimo_flujo = {}
        self.ultimo_valor = 0.0

    def _crea_interfaz(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

        self.lienzo = tk.Canvas(self, bg="#FFFFFF")
        self.lienzo.grid(row=0, column=0, sticky="nsew")

        derecho = ttk.Frame(self, padding=10)
        derecho.grid(row=0, column=1, sticky="ns")
        derecho.columnconfigure(0, weight=1)

        ttk.Label(derecho, text="Controles", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, pady=(0, 8), sticky="w")

        self.modo_var = tk.StringVar(value="add_node")
        modos = [
            ("Anadir nodo (clic lienzo)", "add_node"),
            ("Mover nodo (arrastrar)", "move_node"),
            ("Anadir arco (click origen→destino)", "add_edge"),
            ("Eliminar (nodo/arco)", "delete"),
            ("Renombrar nodo", "rename"),
        ]
        for i, (label, val) in enumerate(modos, start=1):
            ttk.Radiobutton(derecho, text=label, value=val, variable=self.modo_var).grid(row=i, column=0, sticky="w")

        ttk.Separator(derecho).grid(row=7, column=0, pady=8, sticky="ew")

        cap_fr = ttk.Frame(derecho)
        cap_fr.grid(row=8, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(cap_fr, text="Capacidad:").grid(row=0, column=0, sticky="w")
        self.entrada_cap = ttk.Entry(cap_fr, width=10)
        self.entrada_cap.grid(row=0, column=1, padx=(6,0))
        self.entrada_cap.insert(0, "10")

        ttk.Separator(derecho).grid(row=9, column=0, pady=8, sticky="ew")

        ttk.Label(derecho, text="Origen / Sumidero", font=("Segoe UI", 10, "bold")).grid(row=10, column=0, sticky="w")
        src_fr = ttk.Frame(derecho); src_fr.grid(row=11, column=0, sticky="ew", pady=(2,2))
        self.combo_origen = ttk.Combobox(src_fr, state="readonly", values=[])
        self.combo_origen.grid(row=0, column=0, padx=(0,6))
        self.btn_pon_origen = ttk.Button(src_fr, text="Establecer Origen", command=self.pon_origen)
        self.btn_pon_origen.grid(row=0, column=1)

        snk_fr = ttk.Frame(derecho); snk_fr.grid(row=12, column=0, sticky="ew", pady=(2,6))
        self.combo_sumidero = ttk.Combobox(snk_fr, state="readonly", values=[])
        self.combo_sumidero.grid(row=0, column=0, padx=(0,6))
        self.btn_pon_sumidero = ttk.Button(snk_fr, text="Establecer Sumidero", command=self.pon_sumidero)
        self.btn_pon_sumidero.grid(row=0, column=1)

        self.btn_correr = ttk.Button(derecho, text="Calcular Flujo Maximo", command=self.calcula_flujo_maximo)
        self.btn_correr.grid(row=13, column=0, pady=(8,2), sticky="ew")

        self.etiqueta_resultado = ttk.Label(derecho, text="Valor de flujo: —", font=("Segoe UI", 11))
        self.etiqueta_resultado.grid(row=14, column=0, pady=(4,2), sticky="w")

        ttk.Label(derecho, text="Arcos (u → v, cap)", font=("Segoe UI", 10, "bold")).grid(row=15, column=0, sticky="w", pady=(8,2))
        self.tabla = ttk.Treeview(derecho, columns=("u","v","cap"), show="headings", height=10)
        self.tabla.heading("u", text="u")
        self.tabla.heading("v", text="v")
        self.tabla.heading("cap", text="Capacidad")
        self.tabla.column("u", width=90, anchor="center")
        self.tabla.column("v", width=90, anchor="center")
        self.tabla.column("cap", width=100, anchor="e")
        self.tabla.grid(row=16, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", self._en_editar_tabla)

        ttk.Separator(derecho).grid(row=17, column=0, pady=8, sticky="ew")
        btns = ttk.Frame(derecho); btns.grid(row=18, column=0, sticky="ew")
        ttk.Button(btns, text="Nuevo", command=self.nuevo_grafo).grid(row=0, column=0, padx=2)
        ttk.Button(btns, text="Abrir JSON", command=self.carga_json).grid(row=0, column=1, padx=2)
        ttk.Button(btns, text="Guardar JSON", command=self.guarda_json).grid(row=0, column=2, padx=2)
        ttk.Button(btns, text="Exportar CSV (flujo)", command=self.guarda_csv).grid(row=0, column=3, padx=2)

        ttk.Separator(derecho).grid(row=19, column=0, pady=8, sticky="ew")
        ayuda_txt = ("Tips rapidos:\n"
                     "• Modo 'Anadir nodo': clic en el lienzo.\n"
                     "• Modo 'Anadir arco': clic en nodo origen y luego nodo destino.\n"
                     "• Mover: arrastrar un nodo.\n"
                     "• Eliminar: clic en nodo o arco.\n"
                     "• Doble clic en la tabla para editar capacidad.\n"
                     "• Establece Origen y Sumidero antes de calcular, ¡no te olvides!.\n"
                     "• Arcos saturados se pintan mas gruesos y de otro color.")
        ttk.Label(derecho, text=ayuda_txt, wraplength=260, justify="left").grid(row=20, column=0, sticky="w")

    def _enlaza_eventos(self):
        self.lienzo.bind("<Button-1>", self.en_clic_lienzo)
        self.lienzo.bind("<B1-Motion>", self.en_arrastrar_lienzo)
        self.lienzo.bind("<ButtonRelease-1>", self.en_soltar_lienzo)

    def redibuja(self):
        self.lienzo.delete("all")
        for (u, v, cap) in self.el_modelo.los_arcos:
            self._dibuja_arco(u, v, cap)
        for i, (x, y, nombre) in enumerate(self.el_modelo.los_nodos):
            self._dibuja_nodo(i, x, y, nombre)
        self._actualiza_combos_nodo()
        self._actualiza_tabla_arco()

    def _dibuja_nodo(self, nid, x, y, nombre):
        color = "#0D6EFD"
        if nid == self.id_origen:
            color = "#198754"
        elif nid == self.id_sumidero:
            color = "#DC3545"
        self.lienzo.create_oval(x - RADIO_NODO, y - RADIO_NODO, x + RADIO_NODO, y + RADIO_NODO, fill=color, outline="#222", width=1.5, tags=f"node_{nid}")
        self.lienzo.create_text(x, y, text=nombre, fill="white", font=("Segoe UI", 10, "bold"), tags=f"node_{nid}")

    def _coord_arco(self, u, v):
        x1, y1, _ = self.el_modelo.los_nodos[u]
        x2, y2, _ = self.el_modelo.los_nodos[v]
        ang = math.atan2(y2 - y1, x2 - x1)
        sx = x1 + RADIO_NODO * math.cos(ang)
        sy = y1 + RADIO_NODO * math.sin(ang)
        ex = x2 - RADIO_NODO * math.cos(ang)
        ey = y2 - RADIO_NODO * math.sin(ang)
        return sx, sy, ex, ey

    def _dibuja_arco(self, u, v, cap):
        sx, sy, ex, ey = self._coord_arco(u, v)
        ancho_usar = 2
        color = "#444"
        valor_flujo = None
        if (u, v) in self.ultimo_flujo:
            valor_flujo = self.ultimo_flujo[(u, v)]
            if valor_flujo > 1e-12:
                porcentaje = min(1.0, valor_flujo / cap if cap > 1e-12 else 0.0)
                ancho_usar = 2 + int(6 * porcentaje)
                color = "#0A9396" if porcentaje < 0.999 else "#FF8C00"
        self.lienzo.create_line(sx, sy, ex, ey, arrow=tk.LAST, width=ancho_usar, fill=color, tags=f"edge_{u}_{v}")
        midx = (sx + ex) / 2
        midy = (sy + ey) / 2
        nombre_u = self.el_modelo.los_nodos[u][2]
        nombre_v = self.el_modelo.los_nodos[v][2]
        label = f"{nombre_u} → {nombre_v} | cap={cap:g}"
        if valor_flujo is not None:
            label += f" | flujo={valor_flujo:g}"
        self.lienzo.create_text(midx, midy - 8, text=label, fill="#111", font=("Segoe UI", 9), tags=f"edge_{u}_{v}")

    def _actualiza_combos_nodo(self):
        nombres = [n[2] for n in self.el_modelo.los_nodos]
        self.combo_origen["values"] = nombres
        self.combo_sumidero["values"] = nombres
        if self.id_origen is not None and self.id_origen < len(nombres):
            self.combo_origen.set(nombres[self.id_origen])
        if self.id_sumidero is not None and self.id_sumidero < len(nombres):
            self.combo_sumidero.set(nombres[self.id_sumidero])

    def _actualiza_tabla_arco(self):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        for (u, v, c) in self.el_modelo.los_arcos:
            self.tabla.insert("", "end", values=(self.el_modelo.los_nodos[u][2], self.el_modelo.los_nodos[v][2], f"{c:g}"))

    def encuentra_nodo_en(self, x, y):
        for i, (nx, ny, _) in enumerate(self.el_modelo.los_nodos):
            if (nx - x)**2 + (ny - y)**2 <= RADIO_NODO**2:
                return i
        return None

    def encuentra_arco_en(self, x, y):
        el_mejor = None
        mejor_distancia = 8.0
        for (u, v, cap) in self.el_modelo.los_arcos:
            sx, sy, ex, ey = self._coord_arco(u, v)
            px, py = x, y
            dx, dy = ex - sx, ey - sy
            if dx == 0 and dy == 0:
                continue
            t = max(0, min(1, ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)))
            qx, qy = sx + t * dx, sy + t * dy
            d = math.hypot(px - qx, py - qy)
            if d < mejor_distancia:
                mejor_distancia = d
                el_mejor = (u, v)
        return el_mejor

    def en_clic_lienzo(self, event):
        modo = self.modo_var.get()
        if modo == "add_node":
            nombre = None
            try:
                self.el_modelo.pon_nodo(event.x, event.y, nombre)
                self.ultimo_flujo.clear()
                self.redibuja()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        elif modo == "add_edge":
            nid = self.encuentra_nodo_en(event.x, event.y)
            if nid is None:
                return
            if self.arco_pendiente_desde is None:
                self.arco_pendiente_desde = nid
                self._pista(f"Selecciona destino para el arco desde {self.el_modelo.los_nodos[nid][2]}")
            else:
                if nid == self.arco_pendiente_desde:
                    self._pista("No se permiten lazos")
                    self.arco_pendiente_desde = None
                    return
                try:
                    cap = float(self.entrada_cap.get())
                    if cap <= 0:
                        raise ValueError("La capacidad debe ser positiva, ¡dale valor!")
                    self.el_modelo.pon_arco(self.arco_pendiente_desde, nid, cap)
                    self.arco_pendiente_desde = None
                    self.ultimo_flujo.clear()
                    self.redibuja()
                except ValueError as e:
                    messagebox.showerror("Capacidad invalida", str(e))
                    self.arco_pendiente_desde = None
        elif modo == "move_node":
            self.nodo_arrastrar = self.encuentra_nodo_en(event.x, event.y)
            self.desplazamiento = (0,0)
            if self.nodo_arrastrar is not None:
                x, y, _ = self.el_modelo.los_nodos[self.nodo_arrastrar]
                self.desplazamiento = (event.x - x, event.y - y)
        elif modo == "delete":
            nid = self.encuentra_nodo_en(event.x, event.y)
            if nid is not None:
                if messagebox.askyesno("Eliminar nodo", f"¿Eliminar nodo {self.el_modelo.los_nodos[nid][2]} y sus arcos?"):
                    self.el_modelo.quita_nodo(nid)
                    if self.id_origen == nid: self.id_origen = None
                    if self.id_sumidero == nid: self.id_sumidero = None
                    self.ultimo_flujo.clear()
                    self.redibuja()
                return
            ed = self.encuentra_arco_en(event.x, event.y)
            if ed:
                u, v = ed
                if messagebox.askyesno("Eliminar arco", f"¿Eliminar arco {self.el_modelo.los_nodos[u][2]} → {self.el_modelo.los_nodos[v][2]}?"):
                    self.el_modelo.quita_arco(u, v)
                    self.ultimo_flujo.clear()
                    self.redibuja()
        elif modo == "rename":
            nid = self.encuentra_nodo_en(event.x, event.y)
            if nid is not None:
                self._dialogo_renombrar_nodo(nid)

    def en_arrastrar_lienzo(self, event):
        if self.modo_var.get() == "move_node" and hasattr(self, "nodo_arrastrar") and self.nodo_arrastrar is not None:
            dx, dy = self.desplazamiento
            x = max(RADIO_NODO + 4, min(self.lienzo.winfo_width() - RADIO_NODO - 4, event.x - dx))
            y = max(RADIO_NODO + 4, min(self.lienzo.winfo_height() - RADIO_NODO - 4, event.y - dy))
            self.el_modelo.mueve_nodo(self.nodo_arrastrar, x, y)
            self.redibuja()

    def en_soltar_lienzo(self, event):
        if hasattr(self, "nodo_arrastrar"):
            self.nodo_arrastrar = None

    def _en_editar_tabla(self, event):
        item = self.tabla.identify_row(event.y)
        if not item:
            return
        vals = self.tabla.item(item, "values")
        u_nombre, v_nombre, cap = vals
        u = self.el_modelo.nombre_a_id[u_nombre]
        v = self.el_modelo.nombre_a_id[v_nombre]
        self._dialogo_editar_capacidad(u, v)

    def _dialogo_renombrar_nodo(self, nid):
        ventana = tk.Toplevel(self)
        ventana.title("Renombrar nodo")
        ttk.Label(ventana, text="Nuevo nombre:").grid(row=0, column=0, padx=8, pady=8)
        e = ttk.Entry(ventana)
        e.grid(row=0, column=1, padx=8, pady=8)
        e.insert(0, self.el_modelo.los_nodos[nid][2])
        def ok():
            nuevo_nombre = e.get().strip()
            if not nuevo_nombre:
                messagebox.showerror("Error", "El nombre no puede ser vacio, ¡ponle algo!")
                return
            try:
                self.el_modelo.cambia_nombre_nodo(nid, nuevo_nombre)
                self.redibuja()
                ventana.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        ttk.Button(ventana, text="Aceptar", command=ok).grid(row=1, column=0, columnspan=2, pady=8)

    def _dialogo_editar_capacidad(self, u, v):
        ventana = tk.Toplevel(self)
        ventana.title("Editar capacidad")
        u_nombre = self.el_modelo.los_nodos[u][2]
        v_nombre = self.el_modelo.los_nodos[v][2]
        ttk.Label(ventana, text=f"Arco {u_nombre} → {v_nombre}").grid(row=0, column=0, columnspan=2, padx=8, pady=(8,2))
        ttk.Label(ventana, text="Capacidad:").grid(row=1, column=0, padx=8, pady=8)
        e = ttk.Entry(ventana)
        e.grid(row=1, column=1, padx=8, pady=8)
        cap = 0.0
        for (a, b, c) in self.el_modelo.los_arcos:
            if a == u and b == v:
                cap = c; break
        e.insert(0, f"{cap:g}")
        def ok():
            try:
                nueva_cap = float(e.get())
                if nueva_cap <= 0:
                    raise ValueError("La capacidad debe ser positiva, ¡es logica!")
                self.el_modelo.actualiza_capacidad(u, v, nueva_cap)
                self.ultimo_flujo.clear()
                self.redibuja()
                ventana.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        ttk.Button(ventana, text="Guardar", command=ok).grid(row=2, column=0, columnspan=2, pady=8)

    def pon_origen(self):
        nombre = self.combo_origen.get()
        if not nombre: return
        self.id_origen = self.el_modelo.nombre_a_id.get(nombre)
        self.redibuja()

    def pon_sumidero(self):
        nombre = self.combo_sumidero.get()
        if not nombre: return
        self.id_sumidero = self.el_modelo.nombre_a_id.get(nombre)
        self.redibuja()

    def calcula_flujo_maximo(self):
        if self.id_origen is None or self.id_sumidero is None:
            messagebox.showwarning("Faltan datos", "Debes seleccionar Origen y Sumidero, ¡es lo basico!.")
            return
        n_nodos = len(self.el_modelo.los_nodos)
        if n_nodos == 0:
            return
        mf = ElMaxiFlujo(n_nodos)
        for (u, v, c) in self.el_modelo.los_arcos:
            mf.pon_arco(u, v, c)
        try:
            valor, mapa_flujo = mf.calcula_el_maximo(self.id_origen, self.id_sumidero)
            self.ultimo_flujo = mapa_flujo
            self.ultimo_valor = valor
            self.etiqueta_resultado.config(text=f"Valor de flujo: {valor:g}")
            self.redibuja()
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))

    def nuevo_grafo(self):
        if not messagebox.askyesno("Nuevo", "¿Deseas limpiar el grafo actual? Se va a borrar todo."):
            return
        self.el_modelo = ElModeloDelGrafo()
        self.id_origen = None
        self.id_sumidero = None
        self.ultimo_flujo.clear()
        self.ultimo_valor = 0.0
        self.redibuja()

    def guarda_json(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON","*.json")],
                                            title="Guardar grafo")
        if not ruta: return
        try:
            self.el_modelo.exporta_json(ruta)
            messagebox.showinfo("Guardado", "Grafo guardado correctamente. ¡Listo!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def carga_json(self):
        ruta = filedialog.askopenfilename(filetypes=[("JSON","*.json")], title="Abrir grafo")
        if not ruta: return
        try:
            self.el_modelo.importa_json(ruta)
            self.id_origen = None
            self.id_sumidero = None
            self.ultimo_flujo.clear()
            self.ultimo_valor = 0.0
            self.redibuja()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def guarda_csv(self):
        if not self.ultimo_flujo:
            messagebox.showwarning("Sin resultados", "Primero calcula el flujo maximo, ¡no seas vago!.")
            return
        ruta = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV","*.csv")],
                                            title="Exportar flujo")
        if not ruta: return
        try:
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                escritor = csv.writer(f)
                escritor.writerow(["u","v","capacidad","flujo"])
                nombres = [n[2] for n in self.el_modelo.los_nodos]
                mapa_cap = {(u,v):c for (u,v,c) in self.el_modelo.los_arcos}
                for (u,v), flujo in self.ultimo_flujo.items():
                    escritor.writerow([nombres[u], nombres[v], mapa_cap.get((u,v), ""), f"{flujo:g}"])
                escritor.writerow([])
                escritor.writerow(["Valor total de flujo", f"{self.ultimo_valor:g}"])
            messagebox.showinfo("Exportado", "CSV exportado correctamente. ¡Trabajo hecho!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _pista(self, texto):
        self.etiqueta_resultado.config(text=texto)


if __name__ == "__main__":
    app = LaApp()
    app.redibuja()
    app.mainloop()