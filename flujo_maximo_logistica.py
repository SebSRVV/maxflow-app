import json
import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class FlujoMaximoEK:
    def __init__(self, num_nodos):
        self.num_nodos = num_nodos
        self.residual = [dict() for _ in range(num_nodos)]   # red residual
        self.original = [dict() for _ in range(num_nodos)]  # capacidades originales (solo u->v)

    def agregar_arco(self, u, v, capacidad):
        if capacidad <= 0:
            raise ValueError("Capacidad > 0")
        capacidad = float(capacidad)
        self.residual[u][v] = self.residual[u].get(v, 0.0) + capacidad
        self.residual[v].setdefault(u, 0.0)
        self.original[u][v] = self.original[u].get(v, 0.0) + capacidad

    def _busqueda_ancho(self, origen, sumidero):
        padre = [-1]*self.num_nodos
        arco_padre = [None]*self.num_nodos
        cola = [origen]
        padre[origen] = origen
        while cola:
            u = cola.pop(0)
            for v, capacidad in self.residual[u].items():
                if padre[v] == -1 and capacidad > 1e-12:
                    padre[v] = u
                    arco_padre[v] = (u, v)
                    if v == sumidero:
                        # reconstruir camino como lista de arcos
                        camino = []
                        x = sumidero
                        while x != origen:
                            e = arco_padre[x]
                            camino.append(e)
                            x = padre[x]
                        camino.reverse()
                        return camino
                    cola.append(v)
        return None

    def flujo_maximo(self, origen, sumidero):
        if origen == sumidero:
            return 0.0, {}, []
        iteraciones = []
        k = 0
        while True:
            camino = self._busqueda_ancho(origen, sumidero)
            if not camino:
                break
            k += 1
            # cuello de botella
            cuello_botella = min(self.residual[u][v] for (u, v) in camino)
            # aumentar flujo en residual
            for (u, v) in camino:
                self.residual[u][v] -= cuello_botella
                self.residual[v][u] = self.residual[v].get(u, 0.0) + cuello_botella
            # snapshot mínimo (solo arcos del camino)
            iteraciones.append({
                "k": k,
                "camino": camino[:],
                "cuello_botella": cuello_botella,
            })
        # valor y flujo por arco original
        valor_maximo = 0.0
        mapa_flujo = {}
        for u in range(self.num_nodos):
            for v, c0 in self.original[u].items():
                flujo = self.residual[v].get(u, 0.0)  # capacidad reversa final = flujo enviado
                mapa_flujo[(u, v)] = flujo
        # El valor total se suma sobre arcos salientes de 'origen' (o entrantes a 'sumidero')
        valor_maximo = sum(self.residual[v].get(origen, 0.0) for v in range(self.num_nodos))
        return valor_maximo, mapa_flujo, iteraciones


# ==============================
#  Modelo del grafo (GUI)
# ==============================
RADIO_NODO = 20

class ModeloGrafo:
    def __init__(self):
        self.nodos = []      # [(x,y,nombre)]
        self.arcos = []      # [(u,v,capacidad)]
        self.nombre_a_id = {}
        self.siguiente_indice_nombre = 0

    def agregar_nodo(self, x, y, nombre=None):
        if nombre is None:
            nombre = f"N{self.siguiente_indice_nombre}"; self.siguiente_indice_nombre += 1
        if nombre in self.nombre_a_id:
            raise ValueError("Nombre ya existe")
        id_nodo = len(self.nodos)
        self.nodos.append((x, y, nombre))
        self.nombre_a_id[nombre] = id_nodo
        return id_nodo

    def renombrar_nodo(self, id_nodo, nuevo_nombre):
        if nuevo_nombre in self.nombre_a_id and self.nombre_a_id[nuevo_nombre] != id_nodo:
            raise ValueError("Nombre de nodo ya en uso")
        x, y, _ = self.nodos[id_nodo]
        nombre_antiguo = self.nodos[id_nodo][2]
        self.nodos[id_nodo] = (x, y, nuevo_nombre)
        del self.nombre_a_id[nombre_antiguo]
        self.nombre_a_id[nuevo_nombre] = id_nodo

    def mover_nodo(self, id_nodo, x, y):
        n = self.nodos[id_nodo]; self.nodos[id_nodo] = (x, y, n[2])

    def eliminar_nodo(self, id_nodo):
        self.arcos = [(u,v,c) for (u,v,c) in self.arcos if u != id_nodo and v != id_nodo]
        nodos_antiguos = self.nodos
        self.nodos, self.nombre_a_id = [], {}
        re_mapeo = {}
        for i,(x,y,nm) in enumerate(nodos_antiguos):
            if i == id_nodo: continue
            re_mapeo[i] = len(self.nodos)
            self.nodos.append((x,y,nm))
            self.nombre_a_id[nm] = re_mapeo[i]
        self.arcos = [(re_mapeo[u], re_mapeo[v], c) for (u,v,c) in self.arcos]

    def agregar_arco(self, u, v, capacidad):
        if u == v: raise ValueError("No se permiten lazos")
        capacidad = float(capacidad)
        for i,(a,b,c) in enumerate(self.arcos):
            if a==u and b==v:
                self.arcos[i]=(a,b,c+capacidad); return
        self.arcos.append((u,v,capacidad))

    def actualizar_capacidad(self, u, v, nueva_capacidad):
        nueva_capacidad = float(nueva_capacidad)
        for i,(a,b,c) in enumerate(self.arcos):
            if a==u and b==v:
                self.arcos[i]=(a,b,nueva_capacidad); return True
        return False

    def eliminar_arco(self, u, v):
        self.arcos = [(a,b,c) for (a,b,c) in self.arcos if not(a==u and b==v)]

    def exportar_json(self, ruta):
        datos = {
            "nodos":[{"id":i,"name":nm,"x":x,"y":y} for i,(x,y,nm) in enumerate(self.nodos)],
            "arcos":[{"u":u,"v":v,"capacity":c} for (u,v,c) in self.arcos],
        }
        with open(ruta,"w",encoding="utf-8") as f: json.dump(datos,f,indent=2,ensure_ascii=False)

    def importar_json(self, ruta):
        with open(ruta,"r",encoding="utf-8") as f: datos=json.load(f)
        self.nodos, self.nombre_a_id = [], {}
        for nd in datos.get("nodos",[]):
            self.agregar_nodo(nd["x"], nd["y"], nd["name"])
        self.arcos = [(int(ed["u"]), int(ed["v"]), float(ed["capacity"])) for ed in datos.get("arcos",[])]
        self.siguiente_indice_nombre = 0
        for _,_,nombre in self.nodos:
            if nombre.startswith("N"):
                try: self.siguiente_indice_nombre = max(self.siguiente_indice_nombre, int(nombre[1:])+1)
                except: pass


# ==============================
#  Interfaz
# ==============================
class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Flujo Máximo (Edmonds–Karp) — Modo iterativo")
        self.geometry("1240x780")
        self.configure(bg="#F5F7FB")

        self.modelo = ModeloGrafo()
        self.id_origen = None
        self.id_sumidero = None

        self.ultimo_flujo = {}
        self.ultimo_valor = 0.0
        self.iteraciones = []     # lista de iteraciones
        self.mostrar_todas_notas_iter = False

        self.arco_pendiente_desde = None
        self.nodo_arrastrando = None
        self.desplazamiento_arrastre = (0,0)

        self._construir_ui()
        self._enlazar_eventos()
        self.redibujar()

    # ---------- UI ----------
    def _construir_ui(self):
        # estilos
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except:
            pass
        estilo.configure("TButton", padding=6)
        estilo.configure("Title.TLabel", font=("Segoe UI", 12, "bold"))
        estilo.configure("Result.TLabel", font=("Segoe UI", 11))
        estilo.configure("Tag.TLabel", foreground="#555")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

        # lienzo
        self.lienzo = tk.Canvas(self, bg="#ffffff", highlightthickness=0)
        self.lienzo.grid(row=0, column=0, sticky="nsew")
        # cuadrícula suave
        self.lienzo.bind("<Configure>", lambda e: self._dibujar_rejilla())

        # panel lateral
        panel_lateral = ttk.Frame(self, padding=(12,10))
        panel_lateral.grid(row=0, column=1, sticky="ns")
        panel_lateral.columnconfigure(0, weight=1)

        ttk.Label(panel_lateral, text="Controles", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0,8))

        self.var_modo = tk.StringVar(value="add_node")
        modos = [
            ("➕ Añadir nodo (clic lienzo)", "add_node"),
            ("✋ Mover nodo (arrastrar)", "move_node"),
            ("➡️ Añadir arco (origen→destino)", "add_edge"),
            ("🗑️ Eliminar (nodo/arco)", "delete"),
            ("✏️ Renombrar nodo", "rename"),
        ]
        for i,(txt,val) in enumerate(modos, start=1):
            ttk.Radiobutton(panel_lateral, text=txt, value=val, variable=self.var_modo).grid(row=i, column=0, sticky="w")

        ttk.Separator(panel_lateral).grid(row=7, column=0, sticky="ew", pady=8)

        # capacidad al crear arco
        fr_cap = ttk.Frame(panel_lateral); fr_cap.grid(row=8, column=0, sticky="ew", pady=(0,6))
        ttk.Label(fr_cap, text="Capacidad por defecto:").grid(row=0, column=0, sticky="w")
        self.entrada_capacidad = ttk.Entry(fr_cap, width=10); self.entrada_capacidad.grid(row=0, column=1, padx=(6,0)); self.entrada_capacidad.insert(0,"10")

        ttk.Separator(panel_lateral).grid(row=9, column=0, sticky="ew", pady=8)

        # origen/sumidero
        ttk.Label(panel_lateral, text="Origen / Sumidero", style="Title.TLabel").grid(row=10, column=0, sticky="w")
        r1 = ttk.Frame(panel_lateral); r1.grid(row=11, column=0, sticky="ew", pady=2)
        self.combo_origen = ttk.Combobox(r1, state="readonly"); self.combo_origen.grid(row=0, column=0, padx=(0,6))
        ttk.Button(r1, text="🏭 Establecer Origen", command=self.establecer_origen).grid(row=0, column=1)

        r2 = ttk.Frame(panel_lateral); r2.grid(row=12, column=0, sticky="ew", pady=2)
        self.combo_sumidero = ttk.Combobox(r2, state="readonly"); self.combo_sumidero.grid(row=0, column=0, padx=(0,6))
        ttk.Button(r2, text="🏪 Establecer Sumidero", command=self.establecer_sumidero).grid(row=0, column=1)

        # ejecutar
        ttk.Button(panel_lateral, text="▶ Calcular Flujo Máximo", command=self.calcular_flujo_maximo).grid(row=13, column=0, sticky="ew", pady=(8,4))
        self.etiqueta_resultado = ttk.Label(panel_lateral, text="Valor de flujo: —", style="Result.TLabel")
        self.etiqueta_resultado.grid(row=14, column=0, sticky="w")

        # iteraciones
        caja_iter = ttk.LabelFrame(panel_lateral, text="Iteraciones")
        caja_iter.grid(row=15, column=0, sticky="ew", pady=(10,4))
        self.escala_iteracion = ttk.Scale(caja_iter, from_=0, to=0, orient="horizontal", command=self._al_cambio_iteracion)
        self.escala_iteracion.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.etiqueta_iteracion = ttk.Label(caja_iter, text="Iteración: — / —"); self.etiqueta_iteracion.grid(row=1, column=0, sticky="w", padx=8, pady=(0,8))
        self.var_mostrar_todo = tk.BooleanVar(value=False)
        ttk.Checkbutton(caja_iter, text="Mostrar notas de todas las iteraciones", variable=self.var_mostrar_todo, command=self.redibujar) \
            .grid(row=2, column=0, sticky="w", padx=8, pady=(0,8))

        # tabla de arcos
        ttk.Label(panel_lateral, text="Arcos (u → v, cap)", style="Title.TLabel").grid(row=16, column=0, sticky="w", pady=(8,2))
        self.tabla = ttk.Treeview(panel_lateral, columns=("u","v","cap"), show="headings", height=10)
        for col,txt,w in [("u","u",90),("v","v",90),("cap","Capacidad",110)]:
            self.tabla.heading(col, text=txt); self.tabla.column(col, width=w, anchor="center" if col!="cap" else "e")
        self.tabla.grid(row=17, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", self._al_editar_tabla)

        ttk.Separator(panel_lateral).grid(row=18, column=0, sticky="ew", pady=8)

        # archivo
        f = ttk.Frame(panel_lateral); f.grid(row=19, column=0, sticky="ew")
        ttk.Button(f, text="🆕 Nuevo", command=self.nuevo_grafo).grid(row=0, column=0, padx=2)
        ttk.Button(f, text="📂 Abrir JSON", command=self.cargar_json).grid(row=0, column=1, padx=2)
        ttk.Button(f, text="💾 Guardar JSON", command=self.guardar_json).grid(row=0, column=2, padx=2)
        ttk.Button(f, text="📤 Exportar CSV (flujo)", command=self.guardar_csv).grid(row=0, column=3, padx=2)

        # leyenda
        leg = ttk.Frame(panel_lateral); leg.grid(row=20, column=0, sticky="ew", pady=(8,0))
        ttk.Label(leg, text="🏭 Origen   🏪 Sumidero   📦 Intermedio", style="Tag.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(leg, text="Naranja: saturado  •  Cian: en uso  •  Gris: libre", style="Tag.TLabel").grid(row=1, column=0, sticky="w")

    def _enlazar_eventos(self):
        self.lienzo.bind("<Button-1>", self.al_clic_lienzo)
        self.lienzo.bind("<B1-Motion>", self.al_arrastrar_lienzo)
        self.lienzo.bind("<ButtonRelease-1>", self.al_soltar_lienzo)

    # ---------- Dibujo ----------
    def _dibujar_rejilla(self):
        self.lienzo.delete("grid")
        ancho = self.lienzo.winfo_width(); alto = self.lienzo.winfo_height()
        paso = 24
        for x in range(0, ancho, paso):
            self.lienzo.create_line(x,0,x,alto, fill="#f0f2f6", tags="grid")
        for y in range(0, alto, paso):
            self.lienzo.create_line(0,y,ancho,y, fill="#f0f2f6", tags="grid")

    def redibujar(self):
        self.lienzo.delete("all")
        self._dibujar_rejilla()
        # arcos
        for (u,v,capacidad) in self.modelo.arcos:
            self._dibujar_arco(u,v,capacidad)
        # nodos
        for i,(x,y,nombre) in enumerate(self.modelo.nodos):
            self._dibujar_nodo(i,x,y,nombre)
        self._actualizar_combos_nodo()
        self._actualizar_tabla_arcos()
        self._actualizar_encabezado_iteracion()

    def _icono_nodo(self, id_nodo):
        if id_nodo == self.id_origen: return "🏭"
        if id_nodo == self.id_sumidero:   return "🏪"
        return "📦"

    def _dibujar_nodo(self, id_nodo, x, y, nombre):
        # halo
        self.lienzo.create_oval(x-RADIO_NODO-2, y-RADIO_NODO-2, x+RADIO_NODO+2, y+RADIO_NODO+2,
                                fill="#E9F2FF", outline="", tags=f"nodo_{id_nodo}")
        color = "#0D6EFD"  # azul
        if id_nodo == self.id_origen: color = "#198754"  # verde
        elif id_nodo == self.id_sumidero: color = "#DC3545"  # rojo
        self.lienzo.create_oval(x-RADIO_NODO, y-RADIO_NODO, x+RADIO_NODO, y+RADIO_NODO, fill=color, outline="#1b1b1b",
                                width=1.5, tags=f"nodo_{id_nodo}")
        self.lienzo.create_text(x, y-2, text=self._icono_nodo(id_nodo), font=("Segoe UI Emoji", 12), fill="white")
        self.lienzo.create_text(x, y+12, text=nombre, fill="white", font=("Segoe UI", 9, "bold"))

    def _coordenadas_arco(self, u, v):
        x1,y1,_ = self.modelo.nodos[u]; x2,y2,_ = self.modelo.nodos[v]
        angulo = math.atan2(y2-y1, x2-x1)
        sx = x1 + RADIO_NODO*math.cos(angulo); sy = y1 + RADIO_NODO*math.sin(angulo)
        ex = x2 - RADIO_NODO*math.cos(angulo); ey = y2 - RADIO_NODO*math.sin(angulo)
        return sx,sy,ex,ey,angulo

    def _notas_iter_arco(self, u, v):
        """Devuelve lista de (k, texto) para el arco u->v en las iteraciones."""
        notas = []
        for it in self.iteraciones:
            if (u,v) in it["camino"]:
                k = it["k"]; delta = it["cuello_botella"]
                notas.append((k, f"[{self.modelo.nodos[u][2]}, +{delta:g}]({k})"))
        return notas

    def _dibujar_arco(self, u, v, capacidad):
        sx,sy,ex,ey,angulo = self._coordenadas_arco(u,v)
        # estilo según flujo
        ancho = 2; color="#5f6368"
        valor_flujo = self.ultimo_flujo.get((u,v), 0.0)
        if valor_flujo > 1e-12:
            porcentaje = min(1.0, valor_flujo/capacidad if capacidad>1e-12 else 0.0)
            ancho = 2 + int(6*porcentaje)
            color = "#0A9396" if porcentaje < 0.999 else "#FF8C00"

        # línea
        self.lienzo.create_line(sx,sy,ex,ey, arrow=tk.LAST, width=ancho, fill=color, smooth=True,
                                arrowshape=(12,14,5), tags=f"arco_{u}_{v}")

        # etiqueta cap/flujo
        midx, midy = (sx+ex)/2, (sy+ey)/2
        base = f"{self.modelo.nodos[u][2]} → {self.modelo.nodos[v][2]} | cap={capacidad:g}"
        if valor_flujo>1e-12: base += f" | flujo={valor_flujo:g}"
        self.lienzo.create_rectangle(midx-4, midy-18, midx+4+7*len(base)/2, midy-2, fill="#ffffff", outline="", stipple="gray25")
        self.lienzo.create_text(midx+2, midy-10, text=base, fill="#111", font=("Segoe UI", 9))

        # notas por iteración
        notas = self._notas_iter_arco(u,v)
        if not notas:
            return
        if not self.var_mostrar_todo.get():
            # solo la iteración activa
            k = int(round(self.escala_iteracion.get())) if self.iteraciones else 0
            notas = [n for n in notas if n[0]==k]
        if notas:
            desp_y = 10
            for (k,txt) in notas:
                self.lienzo.create_text(midx, midy+desp_y, text=txt, fill="#444", font=("Consolas", 9))
                desp_y += 14

    def _actualizar_combos_nodo(self):
        nombres = [n[2] for n in self.modelo.nodos]
        self.combo_origen["values"] = nombres
        self.combo_sumidero["values"] = nombres
        if self.id_origen is not None and self.id_origen < len(nombres): self.combo_origen.set(nombres[self.id_origen])
        if self.id_sumidero is not None and self.id_sumidero < len(nombres): self.combo_sumidero.set(nombres[self.id_sumidero])

    def _actualizar_tabla_arcos(self):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        for (u,v,c) in self.modelo.arcos:
            self.tabla.insert("", "end", values=(self.modelo.nodos[u][2], self.modelo.nodos[v][2], f"{c:g}"))

    # ---------- interacción lienzo ----------
    def encontrar_nodo_en(self, x, y):
        for i,(nx,ny,_) in enumerate(self.modelo.nodos):
            if (nx-x)**2 + (ny-y)**2 <= (RADIO_NODO+2)**2:
                return i
        return None

    def encontrar_arco_en(self, x, y):
        mejor=None; mejor_dist=8.0
        for (u,v,_) in self.modelo.arcos:
            sx,sy,ex,ey,_ = self._coordenadas_arco(u,v)
            dx,dy = ex-sx, ey-sy
            if abs(dx)<1e-9 and abs(dy)<1e-9: continue
            t = max(0, min(1, ((x-sx)*dx + (y-sy)*dy)/(dx*dx+dy*dy)))
            qx,qy = sx + t*dx, sy + t*dy
            d = math.hypot(x-qx, y-qy)
            if d < mejor_dist: mejor_dist=d; mejor=(u,v)
        return mejor

    def al_clic_lienzo(self, e):
        modo = self.var_modo.get()
        if modo == "add_node":
            try:
                self.modelo.agregar_nodo(e.x, e.y, None)
                self.ultimo_flujo.clear(); self.iteraciones.clear()
                self.redibujar()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        elif modo == "add_edge":
            id_nodo = self.encontrar_nodo_en(e.x, e.y)
            if id_nodo is None: return
            if self.arco_pendiente_desde is None:
                self.arco_pendiente_desde = id_nodo
                self.etiqueta_resultado.config(text=f"Selecciona destino desde {self.modelo.nodos[id_nodo][2]}")
            else:
                if id_nodo == self.arco_pendiente_desde:
                    self.arco_pendiente_desde = None
                    return
                try:
                    capacidad = float(self.entrada_capacidad.get())
                    self.modelo.agregar_arco(self.arco_pendiente_desde, id_nodo, capacidad)
                    self.arco_pendiente_desde = None
                    self.ultimo_flujo.clear(); self.iteraciones.clear()
                    self.redibujar()
                except Exception as ex: messagebox.showerror("Error", str(ex))
        elif modo == "move_node":
            self.nodo_arrastrando = self.encontrar_nodo_en(e.x, e.y)
            if self.nodo_arrastrando is not None:
                x,y,_ = self.modelo.nodos[self.nodo_arrastrando]
                self.desplazamiento_arrastre = (e.x-x, e.y-y)
        elif modo == "delete":
            id_nodo = self.encontrar_nodo_en(e.x, e.y)
            if id_nodo is not None:
                if messagebox.askyesno("Eliminar", f"¿Eliminar nodo {self.modelo.nodos[id_nodo][2]} y sus arcos?"):
                    self.modelo.eliminar_nodo(id_nodo)
                    if self.id_origen == id_nodo: self.id_origen=None
                    if self.id_sumidero == id_nodo: self.id_sumidero=None
                    self.ultimo_flujo.clear(); self.iteraciones.clear()
                    self.redibujar()
                return
            arco = self.encontrar_arco_en(e.x, e.y)
            if arco:
                u,v = arco
                if messagebox.askyesno("Eliminar arco", f"¿Eliminar {self.modelo.nodos[u][2]} → {self.modelo.nodos[v][2]}?"):
                    self.modelo.eliminar_arco(u,v)
                    self.ultimo_flujo.clear(); self.iteraciones.clear()
                    self.redibujar()
        elif modo == "rename":
            id_nodo = self.encontrar_nodo_en(e.x, e.y)
            if id_nodo is not None: self._dialogo_renombrar_nodo(id_nodo)

    def al_arrastrar_lienzo(self, e):
        if self.var_modo.get()=="move_node" and self.nodo_arrastrando is not None:
            dx,dy = self.desplazamiento_arrastre
            x = max(RADIO_NODO+4, min(self.lienzo.winfo_width()-RADIO_NODO-4, e.x-dx))
            y = max(RADIO_NODO+4, min(self.lienzo.winfo_height()-RADIO_NODO-4, e.y-dy))
            self.modelo.mover_nodo(self.nodo_arrastrando, x, y)
            self.redibujar()

    def al_soltar_lienzo(self, e):
        self.nodo_arrastrando=None

    # ---------- diálogos ediciones ----------
    def _dialogo_renombrar_nodo(self, id_nodo):
        ventana = tk.Toplevel(self); ventana.title("Renombrar nodo")
        ttk.Label(ventana, text="Nuevo nombre:").grid(row=0, column=0, padx=8, pady=8)
        entrada = ttk.Entry(ventana); entrada.grid(row=0, column=1, padx=8, pady=8); entrada.insert(0, self.modelo.nodos[id_nodo][2])
        def ok():
            nuevo_nombre = entrada.get().strip()
            if not nuevo_nombre:
                messagebox.showerror("Error", "Nombre vacío"); return
            try:
                self.modelo.renombrar_nodo(id_nodo, nuevo_nombre); self.redibujar(); ventana.destroy()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        ttk.Button(ventana, text="Guardar", command=ok).grid(row=1, column=0, columnspan=2, pady=8)

    def _al_editar_tabla(self, event):
        item = self.tabla.identify_row(event.y)
        if not item: return
        u_nombre, v_nombre, _ = self.tabla.item(item, "values")
        u = self.modelo.nombre_a_id[u_nombre]; v = self.modelo.nombre_a_id[v_nombre]
        self._dialogo_editar_capacidad(u, v)

    def _dialogo_editar_capacidad(self, u, v):
        ventana = tk.Toplevel(self); ventana.title("Editar capacidad")
        ttk.Label(ventana, text=f"Arco {self.modelo.nodos[u][2]} → {self.modelo.nodos[v][2]}").grid(row=0, column=0, columnspan=2, padx=8, pady=(8,4))
        ttk.Label(ventana, text="Capacidad:").grid(row=1, column=0, padx=8, pady=8)
        entrada = ttk.Entry(ventana); entrada.grid(row=1, column=1, padx=8, pady=8)
        cap = next(c for (a,b,c) in self.modelo.arcos if a==u and b==v)
        entrada.insert(0, f"{cap:g}")
        def ok():
            try:
                nueva_capacidad = float(entrada.get())
                if nueva_capacidad <= 0: raise ValueError("Capacidad > 0")
                self.modelo.actualizar_capacidad(u, v, nueva_capacidad)
                self.ultimo_flujo.clear(); self.iteraciones.clear()
                self.redibujar(); ventana.destroy()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        ttk.Button(ventana, text="Guardar", command=ok).grid(row=2, column=0, columnspan=2, pady=8)

    # ---------- acciones ----------
    def establecer_origen(self):
        nombre = self.combo_origen.get()
        if not nombre: return
        self.id_origen = self.modelo.nombre_a_id[nombre]; self.redibujar()

    def establecer_sumidero(self):
        nombre = self.combo_sumidero.get()
        if not nombre: return
        self.id_sumidero = self.modelo.nombre_a_id[nombre]; self.redibujar()

    def _al_cambio_iteracion(self, _=None):
        self.redibujar()

    def _actualizar_encabezado_iteracion(self):
        total = len(self.iteraciones)
        actual = int(round(self.escala_iteracion.get())) if total>0 else 0
        self.etiqueta_iteracion.config(text=f"Iteración: {actual if actual>0 else '—'} / {total if total>0 else '—'}")

    def calcular_flujo_maximo(self):
        if self.id_origen is None or self.id_sumidero is None:
            messagebox.showwarning("Faltan datos", "Selecciona Origen y Sumidero."); return
        num_nodos = len(self.modelo.nodos)
        flujo_ek = FlujoMaximoEK(num_nodos)
        for (u,v,c) in self.modelo.arcos: flujo_ek.agregar_arco(u,v,c)
        try:
            valor, mapa_flujo, iteraciones = flujo_ek.flujo_maximo(self.id_origen, self.id_sumidero)
            self.ultimo_flujo = mapa_flujo
            self.ultimo_valor = valor
            self.iteraciones = iteraciones
            self.etiqueta_resultado.config(text=f"Valor de flujo: {valor:g}")
            # configurar slider de iteraciones
            if iteraciones:
                self.escala_iteracion.configure(from_=1, to=len(iteraciones))
                self.escala_iteracion.set(len(iteraciones))
            else:
                self.escala_iteracion.configure(from_=0, to=0)
                self.escala_iteracion.set(0)
            self.redibujar()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def nuevo_grafo(self):
        if not messagebox.askyesno("Nuevo", "¿Vaciar el grafo actual?"): return
        self.modelo = ModeloGrafo(); self.id_origen=None; self.id_sumidero=None
        self.ultimo_flujo.clear(); self.iteraciones.clear(); self.ultimo_valor=0.0
        self.redibujar()

    def guardar_json(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")], title="Guardar grafo")
        if not ruta: return
        try: self.modelo.exportar_json(ruta); messagebox.showinfo("Guardado","Grafo guardado.")
        except Exception as ex: messagebox.showerror("Error", str(ex))

    def cargar_json(self):
        ruta = filedialog.askopenfilename(filetypes=[("JSON","*.json")], title="Abrir grafo")
        if not ruta: return
        try:
            self.modelo.importar_json(ruta)
            self.id_origen=None; self.id_sumidero=None
            self.ultimo_flujo.clear(); self.iteraciones.clear(); self.ultimo_valor=0.0
            self.redibujar()
        except Exception as ex: messagebox.showerror("Error", str(ex))

    def guardar_csv(self):
        if not self.ultimo_flujo:
            messagebox.showwarning("Sin resultados","Primero calcula el flujo máximo."); return
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="Exportar flujo")
        if not ruta: return
        try:
            with open(ruta,"w",newline="",encoding="utf-8") as f:
                escritor = csv.writer(f); escritor.writerow(["u","v","capacidad","flujo"])
                nombres = [n[2] for n in self.modelo.nodos]
                mapa_cap = {(u,v):c for (u,v,c) in self.modelo.arcos}
                for (u,v),flujo in self.ultimo_flujo.items():
                    escritor.writerow([nombres[u], nombres[v], mapa_cap.get((u,v),""), f"{flujo:g}"])
                escritor.writerow([]); escritor.writerow(["Valor total de flujo", f"{self.ultimo_valor:g}"])
                escritor.writerow([])
                escritor.writerow(["Iteraciones"])
                for it in self.iteraciones:
                    camino_txt = " → ".join(self.modelo.nodos[u][2] for (u,_) in it["camino"])+f" → {self.modelo.nodos[self.iteraciones[0]['camino'][-1][1]][2]}"
                    escritor.writerow([f"({it['k']})", camino_txt, f"+{it['cuello_botella']:g}"])
            messagebox.showinfo("Exportado", "CSV exportado correctamente.")
        except Exception as ex: messagebox.showerror("Error", str(ex))


if __name__ == "__main__":
    app = Aplicacion()
    app.redibujar()
    app.mainloop()
