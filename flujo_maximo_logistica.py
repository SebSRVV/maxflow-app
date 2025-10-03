import json
import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class FlujoMaximoEK:
    """
    Ejecuta Edmonds–Karp con red residual y traza de iteraciones.
    Retorna (valor_total, mapa_flujo, iteraciones) donde:
    - mapa_flujo[(u,v)] = flujo final u→v sobre arcos originales.
    - iteraciones = [{"k": iter, "camino": [(u,v),...], "cuello": valor}, ...]
    """
    def __init__(self, n):
        self.n = n
        self.residual = [dict() for _ in range(n)]
        self.original = [dict() for _ in range(n)]

    def agregar_arco(self, u, v, cap):
        """Agrega un arco dirigido u→v con capacidad positiva."""
        if cap <= 0:
            raise ValueError("La capacidad debe ser > 0")
        self.residual[u][v] = self.residual[u].get(v, 0.0) + float(cap)
        self.residual[v].setdefault(u, 0.0)
        self.original[u][v] = self.original[u].get(v, 0.0) + float(cap)

    def _bfs(self, s, t):
        """Devuelve un camino aumentante s→t como lista de arcos [(u,v),...], o None."""
        padre = [-1]*self.n
        padre_arco = [None]*self.n
        q = [s]
        padre[s] = s
        while q:
            u = q.pop(0)
            for v, cap in self.residual[u].items():
                if padre[v] == -1 and cap > 1e-12:
                    padre[v] = u
                    padre_arco[v] = (u, v)
                    if v == t:
                        camino = []
                        x = t
                        while x != s:
                            e = padre_arco[x]
                            camino.append(e)
                            x = padre[x]
                        camino.reverse()
                        return camino
                    q.append(v)
        return None

    def maximo_flujo(self, s, t):
        """Corre Edmonds–Karp entre s y t; retorna valor total, flujo por arco e iteraciones."""
        if s == t:
            return 0.0, {}, []
        iteraciones = []
        k = 0
        while True:
            camino = self._bfs(s, t)
            if not camino:
                break
            k += 1
            cuello = min(self.residual[u][v] for (u, v) in camino)
            for (u, v) in camino:
                self.residual[u][v] -= cuello
                self.residual[v][u] = self.residual[v].get(u, 0.0) + cuello
            iteraciones.append({"k": k, "camino": camino[:], "cuello": cuello})
        mapa_flujo = {}
        for u in range(self.n):
            for v in self.original[u].keys():
                mapa_flujo[(u, v)] = self.residual[v].get(u, 0.0)
        valor_total = sum(self.residual[v].get(s, 0.0) for v in range(self.n))
        return valor_total, mapa_flujo, iteraciones


RADIO_NODO = 20

class ModeloGrafo:
    """
    Modelo del grafo: nodos, arcos y persistencia JSON.
    """
    def __init__(self):
        self.nodos = []
        self.arcos = []
        self.nombre_a_id = {}
        self.siguiente_idx_nombre = 0

    def agregar_nodo(self, x, y, nombre=None):
        """Agrega un nodo en (x,y) con nombre único (auto si None)."""
        if nombre is None:
            nombre = f"N{self.siguiente_idx_nombre}"; self.siguiente_idx_nombre += 1
        if nombre in self.nombre_a_id:
            raise ValueError("Nombre ya existe")
        nid = len(self.nodos)
        self.nodos.append((x, y, nombre))
        self.nombre_a_id[nombre] = nid
        return nid

    def renombrar_nodo(self, nid, nuevo):
        """Renombra el nodo nid a 'nuevo' si está disponible."""
        if nuevo in self.nombre_a_id and self.nombre_a_id[nuevo] != nid:
            raise ValueError("Nombre de nodo ya en uso")
        x, y, _ = self.nodos[nid]
        viejo = self.nodos[nid][2]
        self.nodos[nid] = (x, y, nuevo)
        del self.nombre_a_id[viejo]
        self.nombre_a_id[nuevo] = nid

    def mover_nodo(self, nid, x, y):
        """Mueve el nodo nid a (x,y)."""
        n = self.nodos[nid]; self.nodos[nid] = (x, y, n[2])

    def eliminar_nodo(self, nid):
        """Elimina el nodo y reindexa nodos y arcos restantes."""
        self.arcos = [(u,v,c) for (u,v,c) in self.arcos if u != nid and v != nid]
        nodos_viejos = self.nodos
        self.nodos, self.nombre_a_id = [], {}
        remap = {}
        for i,(x,y,nm) in enumerate(nodos_viejos):
            if i == nid: continue
            remap[i] = len(self.nodos)
            self.nodos.append((x,y,nm))
            self.nombre_a_id[nm] = remap[i]
        self.arcos = [(remap[u], remap[v], c) for (u,v,c) in self.arcos]

    def agregar_arco(self, u, v, cap):
        """Agrega o acumula capacidad de un arco u→v."""
        if u == v:
            raise ValueError("No se permiten lazos")
        for i,(a,b,c) in enumerate(self.arcos):
            if a==u and b==v:
                self.arcos[i]=(a,b,c+float(cap)); return
        self.arcos.append((u,v,float(cap)))

    def actualizar_capacidad(self, u, v, nueva_cap):
        """Actualiza la capacidad de un arco u→v existente."""
        for i,(a,b,c) in enumerate(self.arcos):
            if a==u and b==v:
                self.arcos[i]=(a,b,float(nueva_cap)); return True
        return False

    def eliminar_arco(self, u, v):
        """Elimina el arco u→v si existe."""
        self.arcos = [(a,b,c) for (a,b,c) in self.arcos if not(a==u and b==v)]

    def exportar_json(self, path):
        """Exporta el grafo a un archivo JSON."""
        datos = {
            "nodos":[{"id":i,"nombre":nm,"x":x,"y":y} for i,(x,y,nm) in enumerate(self.nodos)],
            "arcos":[{"u":u,"v":v,"capacidad":c} for (u,v,c) in self.arcos],
        }
        with open(path,"w",encoding="utf-8") as f: json.dump(datos,f,indent=2,ensure_ascii=False)

    def importar_json(self, path):
        """Importa un grafo desde un archivo JSON."""
        with open(path,"r",encoding="utf-8") as f: datos=json.load(f)
        self.nodos, self.nombre_a_id = [], {}
        for nd in datos.get("nodos",[]):
            self.agregar_nodo(nd["x"], nd["y"], nd["nombre"])
        self.arcos = [(int(ed["u"]), int(ed["v"]), float(ed["capacidad"])) for ed in datos.get("arcos",[])]
        self.siguiente_idx_nombre = 0
        for _,_,nombre in self.nodos:
            if nombre.startswith("N"):
                try: self.siguiente_idx_nombre = max(self.siguiente_idx_nombre, int(nombre[1:])+1)
                except: pass


class Aplicacion(tk.Tk):
    """
    Interfaz Tk para construir el grafo y ejecutar Edmonds–Karp.
    Los arcos muestran solo la capacidad como etiqueta. El estilo de línea depende del
    flujo final. Debajo de cada arco se muestra el log completo de iteraciones con el
    formato: "[De Donde viene, X](iteracion)" donde X es la suma acumulada.
    Incluye un botón para ver todas las rutas, su flujo máximo agregado y cuántas
    iteraciones usaron cada ruta; además muestra el total de flujo.
    """
    def __init__(self):
        super().__init__()
        self.title("Flujo Máximo (Edmonds–Karp) — Modo iterativo")
        self.geometry("1280x820")
        self.configure(bg="#F5F7FB")

        self.modelo = ModeloGrafo()
        self.id_origen = None
        self.id_sumidero = None

        self.ultimo_flujo = {}
        self.ultimo_valor = 0.0
        self.iteraciones = []

        self.arco_pendiente_desde = None
        self.nodo_arrastre = None
        self.offset_arrastre = (0,0)

        self._construir_ui()
        self._vincular_eventos()
        self.redibujar()

    def _construir_ui(self):
        """Crea y maqueta los controles principales de la aplicación."""
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except:
            pass
        estilo.configure("TButton", padding=8, font=("Segoe UI", 10))
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 13, "bold"))
        estilo.configure("Resultado.TLabel", font=("Segoe UI", 11, "bold"))
        estilo.configure("Tag.TLabel", foreground="#555")
        estilo.configure("TFrame", background="#F5F7FB")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

        self.lienzo = tk.Canvas(self, bg="#ffffff", highlightthickness=0)
        self.lienzo.grid(row=0, column=0, sticky="nsew")
        self.lienzo.bind("<Configure>", lambda e: self._dibujar_cuadricula())

        lateral = ttk.Frame(self, padding=(12,10))
        lateral.grid(row=0, column=1, sticky="ns")
        lateral.columnconfigure(0, weight=1)

        ttk.Label(lateral, text="Controles", style="Titulo.TLabel").grid(row=0, column=0, sticky="w", pady=(0,8))

        self.modo_var = tk.StringVar(value="agregar_nodo")
        modos = [
            ("➕ Añadir nodo (clic lienzo)", "agregar_nodo"),
            ("✋ Mover nodo (arrastrar)", "mover_nodo"),
            ("➡️ Añadir arco (origen→destino)", "agregar_arco"),
            ("🗑️ Eliminar (nodo/arco)", "eliminar"),
            ("✏️ Renombrar nodo", "renombrar"),
        ]
        for i,(txt,val) in enumerate(modos, start=1):
            ttk.Radiobutton(lateral, text=txt, value=val, variable=self.modo_var).grid(row=i, column=0, sticky="w")

        ttk.Separator(lateral).grid(row=7, column=0, sticky="ew", pady=8)

        cap_fr = ttk.Frame(lateral); cap_fr.grid(row=8, column=0, sticky="ew", pady=(0,6))
        ttk.Label(cap_fr, text="Capacidad por defecto:").grid(row=0, column=0, sticky="w")
        self.entrada_capacidad = ttk.Entry(cap_fr, width=10); self.entrada_capacidad.grid(row=0, column=1, padx=(6,0)); self.entrada_capacidad.insert(0,"10")

        ttk.Separator(lateral).grid(row=9, column=0, sticky="ew", pady=8)

        ttk.Label(lateral, text="Origen / Sumidero", style="Titulo.TLabel").grid(row=10, column=0, sticky="w")
        r1 = ttk.Frame(lateral); r1.grid(row=11, column=0, sticky="ew", pady=2)
        self.combo_origen = ttk.Combobox(r1, state="readonly"); self.combo_origen.grid(row=0, column=0, padx=(0,6))
        ttk.Button(r1, text="🏭 Establecer Origen", command=self.establecer_origen).grid(row=0, column=1)
        r2 = ttk.Frame(lateral); r2.grid(row=12, column=0, sticky="ew", pady=2)
        self.combo_sumidero = ttk.Combobox(r2, state="readonly"); self.combo_sumidero.grid(row=0, column=0, padx=(0,6))
        ttk.Button(r2, text="🏪 Establecer Sumidero", command=self.establecer_sumidero).grid(row=0, column=1)

        ttk.Button(lateral, text="▶ Calcular Flujo Máximo", command=self.calcular_flujo_maximo).grid(row=13, column=0, sticky="ew", pady=(8,4))
        self.lbl_resultado = ttk.Label(lateral, text="Flujo Maximo: —", style="Resultado.TLabel")
        self.lbl_resultado.grid(row=14, column=0, sticky="w")

        ttk.Label(lateral, text="Arcos (u → v, capacidad)", style="Titulo.TLabel").grid(row=15, column=0, sticky="w", pady=(8,2))
        self.tabla = ttk.Treeview(lateral, columns=("u","v","cap"), show="headings", height=12)
        for col,txt,w in [("u","u",90),("v","v",90),("cap","Capacidad",110)]:
            self.tabla.heading(col, text=txt); self.tabla.column(col, width=w, anchor="center" if col!="cap" else "e")
        self.tabla.grid(row=16, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", self._editar_capacidad_dialogo)

        ttk.Separator(lateral).grid(row=17, column=0, sticky="ew", pady=8)

        f = ttk.Frame(lateral); f.grid(row=18, column=0, sticky="ew")
        ttk.Button(f, text="🆕 Nuevo", command=self.nuevo_grafo).grid(row=0, column=0, padx=2)
        ttk.Button(f, text="📂 Abrir JSON", command=self.abrir_json).grid(row=0, column=1, padx=2)
        ttk.Button(f, text="💾 Guardar JSON", command=self.guardar_json).grid(row=0, column=2, padx=2)
        ttk.Button(f, text="📤 Exportar CSV (flujo)", command=self.exportar_csv).grid(row=0, column=3, padx=2)

        ley = ttk.Frame(lateral); ley.grid(row=19, column=0, sticky="ew", pady=(8,0))
        ttk.Label(ley, text="🏭 Origen   🏪 Sumidero   📦 Intermedio", style="Tag.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(ley, text="Naranja: mayor flujo  •  Cian/Gris: menor flujo", style="Tag.TLabel").grid(row=1, column=0, sticky="w")
        self.lbl_ruta_optima = ttk.Label(ley, text="Ruta óptima: —", style="Tag.TLabel")
        self.lbl_ruta_optima.grid(row=2, column=0, sticky="w", pady=(6,2))
        ttk.Button(ley, text="🔎 Ver todas las rutas", command=self.mostrar_rutas).grid(row=3, column=0, sticky="w", pady=(6,0))

    def _vincular_eventos(self):
        """Conecta eventos del lienzo."""
        self.lienzo.bind("<Button-1>", self._click_lienzo)
        self.lienzo.bind("<B1-Motion>", self._arrastrar_lienzo)
        self.lienzo.bind("<ButtonRelease-1>", self._soltar_lienzo)

    def _dibujar_cuadricula(self):
        """Dibuja una cuadrícula sutil en el lienzo."""
        self.lienzo.delete("grid")
        w = self.lienzo.winfo_width(); h = self.lienzo.winfo_height()
        paso = 24
        for x in range(0, w, paso):
            self.lienzo.create_line(x,0,x,h, fill="#f0f2f6", tags="grid")
        for y in range(0, h, paso):
            self.lienzo.create_line(0,y,w,y, fill="#f0f2f6", tags="grid")

    def redibujar(self):
        """Redibuja arcos, nodos, combos y tabla."""
        self.lienzo.delete("all")
        self._dibujar_cuadricula()
        for (u,v,cap) in self.modelo.arcos:
            self._dibujar_arco(u,v,cap)
        for i,(x,y,nombre) in enumerate(self.modelo.nodos):
            self._dibujar_nodo(i,x,y,nombre)
        self._refrescar_combos_nodo()
        self._refrescar_tabla_arcos()

    def _icono_nodo(self, nid):
        """Devuelve el emoji por rol del nodo."""
        if nid == self.id_origen: return "🏭"
        if nid == self.id_sumidero:   return "🏪"
        return "📦"

    def _dibujar_nodo(self, nid, x, y, nombre):
        """Dibuja un nodo con su estilo e icono."""
        self.lienzo.create_oval(x-RADIO_NODO-2, y-RADIO_NODO-2, x+RADIO_NODO+2, y+RADIO_NODO+2,
                                fill="#E9F2FF", outline="", tags=f"nodo_{nid}")
        color = "#0D6EFD"
        if nid == self.id_origen: color = "#198754"
        elif nid == self.id_sumidero: color = "#DC3545"
        self.lienzo.create_oval(x-RADIO_NODO, y-RADIO_NODO, x+RADIO_NODO, y+RADIO_NODO, fill=color, outline="#1b1b1b",
                                width=1.5, tags=f"nodo_{nid}")
        self.lienzo.create_text(x, y-2, text=self._icono_nodo(nid), font=("Segoe UI Emoji", 12), fill="white")
        self.lienzo.create_text(x, y+12, text=nombre, fill="white", font=("Segoe UI", 9, "bold"))

    def _coords_arco(self, u, v):
        """Calcula coordenadas de un arco y su ángulo base."""
        x1,y1,_ = self.modelo.nodos[u]; x2,y2,_ = self.modelo.nodos[v]
        ang = math.atan2(y2-y1, x2-x1)
        sx = x1 + RADIO_NODO*math.cos(ang); sy = y1 + RADIO_NODO*math.sin(ang)
        ex = x2 - RADIO_NODO*math.cos(ang); ey = y2 - RADIO_NODO*math.sin(ang)
        return sx,sy,ex,ey,ang

    def _log_iteraciones_arco(self, u, v):
        """
        Devuelve el log completo del arco u→v.
        Formato: "[De Donde viene, X](k)" donde X es la suma acumulada hasta la k-ésima aparición.
        """
        log = []
        total = 0.0
        nombre_u = self.modelo.nodos[u][2]
        for it in self.iteraciones:
            if (u,v) in it["camino"]:
                total += it["cuello"]
                log.append(f"[{nombre_u}, {total:g}]({it['k']})")
        return log

    def _dibujar_arco(self, u, v, capacidad):
        """Dibuja un arco con etiqueta de capacidad y log de iteraciones."""
        sx,sy,ex,ey,_ = self._coords_arco(u,v)
        flujo = self.ultimo_flujo.get((u,v), 0.0)
        grosor = max(2, min(10, int(2 + math.log2(flujo+1)*4))) if flujo > 1e-12 else 2
        color = "#5f6368"
        if flujo > 1e-12:
            color = "#0A9396" if flujo < max(1.0, 0.4*capacidad) else "#FF8C00"

        self.lienzo.create_line(sx,sy,ex,ey, arrow=tk.LAST, width=grosor, fill=color, smooth=True,
                                arrowshape=(12,14,5), tags=f"arco_{u}_{v}")

        midx, midy = (sx+ex)/2, (sy+ey)/2
        etiqueta = f"{capacidad:g}"
        self.lienzo.create_rectangle(midx-4, midy-18, midx+4+7*len(etiqueta)/2, midy-2, fill="#ffffff", outline="", stipple="gray25")
        self.lienzo.create_text(midx+2, midy-10, text=etiqueta, fill="#111", font=("Segoe UI", 9))

        log = self._log_iteraciones_arco(u,v)
        if log:
            yoff = 10
            for entrada in log:
                self.lienzo.create_text(midx, midy+yoff, text=entrada, fill="#444", font=("Consolas", 9))
                yoff += 14

    def _refrescar_combos_nodo(self):
        """Actualiza combos de Origen/Sumidero con los nombres actuales."""
        nombres = [n[2] for n in self.modelo.nodos]
        self.combo_origen["values"] = nombres
        self.combo_sumidero["values"] = nombres
        if self.id_origen is not None and self.id_origen < len(nombres): self.combo_origen.set(nombres[self.id_origen])
        if self.id_sumidero is not None and self.id_sumidero < len(nombres): self.combo_sumidero.set(nombres[self.id_sumidero])

    def _refrescar_tabla_arcos(self):
        """Rellena la tabla lateral con los arcos y capacidades."""
        for i in self.tabla.get_children(): self.tabla.delete(i)
        for (u,v,c) in self.modelo.arcos:
            self.tabla.insert("", "end", values=(self.modelo.nodos[u][2], self.modelo.nodos[v][2], f"{c:g}"))

    def _buscar_nodo_en(self, x, y):
        """Devuelve el id de un nodo bajo (x,y), o None si no hay."""
        for i,(nx,ny,_) in enumerate(self.modelo.nodos):
            if (nx-x)**2 + (ny-y)**2 <= (RADIO_NODO+2)**2:
                return i
        return None

    def _buscar_arco_en(self, x, y):
        """Devuelve (u,v) del arco más cercano a (x,y), si está lo bastante cerca."""
        mejor=None; mejor_d=8.0
        for (u,v,_) in self.modelo.arcos:
            sx,sy,ex,ey,_ = self._coords_arco(u,v)
            dx,dy = ex-sx, ey-sy
            if abs(dx)<1e-9 and abs(dy)<1e-9: continue
            t = max(0, min(1, ((x-sx)*dx + (y-sy)*dy)/(dx*dx+dy*dy)))
            qx,qy = sx + t*dx, sy + t*dy
            d = math.hypot(x-qx, y-qy)
            if d < mejor_d: mejor_d=d; mejor=(u,v)
        return mejor

    def _click_lienzo(self, e):
        """Gestiona click en el lienzo según el modo activo."""
        modo = self.modo_var.get()
        if modo == "agregar_nodo":
            try:
                self.modelo.agregar_nodo(e.x, e.y, None)
                self.ultimo_flujo.clear(); self.iteraciones.clear()
                self.redibujar()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        elif modo == "agregar_arco":
            nid = self._buscar_nodo_en(e.x, e.y)
            if nid is None: return
            if self.arco_pendiente_desde is None:
                self.arco_pendiente_desde = nid
                self.lbl_resultado.config(text=f"Selecciona destino desde {self.modelo.nodos[nid][2]}")
            else:
                if nid == self.arco_pendiente_desde:
                    self.arco_pendiente_desde = None
                    return
                try:
                    cap = float(self.entrada_capacidad.get())
                    self.modelo.agregar_arco(self.arco_pendiente_desde, nid, cap)
                    self.arco_pendiente_desde = None
                    self.ultimo_flujo.clear(); self.iteraciones.clear()
                    self.redibujar()
                except Exception as ex: messagebox.showerror("Error", str(ex))
        elif modo == "mover_nodo":
            self.nodo_arrastre = self._buscar_nodo_en(e.x, e.y)
            if self.nodo_arrastre is not None:  # ← FIX: 'is' en lugar de 'es'
                x,y,_ = self.modelo.nodos[self.nodo_arrastre]
                self.offset_arrastre = (e.x-x, e.y-y)
        elif modo == "eliminar":
            nid = self._buscar_nodo_en(e.x, e.y)
            if nid is not None:
                if messagebox.askyesno("Eliminar", f"¿Eliminar nodo {self.modelo.nodos[nid][2]} y sus arcos?"):
                    self.modelo.eliminar_nodo(nid)
                    if self.id_origen == nid: self.id_origen=None
                    if self.id_sumidero == nid: self.id_sumidero=None
                    self.ultimo_flujo.clear(); self.iteraciones.clear()
                    self.redibujar()
                return
            ed = self._buscar_arco_en(e.x, e.y)
            if ed:
                u,v = ed
                if messagebox.askyesno("Eliminar arco", f"¿Eliminar {self.modelo.nodos[u][2]} → {self.modelo.nodos[v][2]}?"):
                    self.modelo.eliminar_arco(u,v)
                    self.ultimo_flujo.clear(); self.iteraciones.clear()
                    self.redibujar()
        elif modo == "renombrar":
            nid = self._buscar_nodo_en(e.x, e.y)
            if nid is not None: self._dialogo_renombrar_nodo(nid)

    def _arrastrar_lienzo(self, e):
        """Arrastra un nodo en modo mover_nodo."""
        if self.modo_var.get()=="mover_nodo" and self.nodo_arrastre is not None:
            dx,dy = self.offset_arrastre
            x = max(RADIO_NODO+4, min(self.lienzo.winfo_width()-RADIO_NODO-4, e.x-dx))
            y = max(RADIO_NODO+4, min(self.lienzo.winfo_height()-RADIO_NODO-4, e.y-dy))
            self.modelo.mover_nodo(self.nodo_arrastre, x, y)
            self.redibujar()

    def _soltar_lienzo(self, _e):
        """Finaliza el arrastre de un nodo."""
        self.nodo_arrastre=None

    def _dialogo_renombrar_nodo(self, nid):
        """Muestra un diálogo para renombrar un nodo."""
        win = tk.Toplevel(self); win.title("Renombrar nodo")
        ttk.Label(win, text="Nuevo nombre:").grid(row=0, column=0, padx=8, pady=8)
        e = ttk.Entry(win); e.grid(row=0, column=1, padx=8, pady=8); e.insert(0, self.modelo.nodos[nid][2])
        def ok():
            nuevo = e.get().strip()
            if not nuevo:
                messagebox.showerror("Error", "Nombre vacío"); return
            try:
                self.modelo.renombrar_nodo(nid, nuevo); self.redibujar(); win.destroy()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        ttk.Button(win, text="Guardar", command=ok).grid(row=1, column=0, columnspan=2, pady=8)

    def _editar_capacidad_dialogo(self, event):
        """Abre diálogo de edición de capacidad al hacer doble clic en un arco de la tabla."""
        item = self.tabla.identify_row(event.y)
        if not item: return
        u_nom, v_nom, _ = self.tabla.item(item, "values")
        u = self.modelo.nombre_a_id[u_nom]; v = self.modelo.nombre_a_id[v_nom]
        self._dialogo_capacidad(u, v)

    def _dialogo_capacidad(self, u, v):
        """Diálogo para cambiar la capacidad de un arco u→v."""
        win = tk.Toplevel(self); win.title("Editar capacidad")
        ttk.Label(win, text=f"Arco {self.modelo.nodos[u][2]} → {self.modelo.nodos[v][2]}").grid(row=0, column=0, columnspan=2, padx=8, pady=(8,4))
        ttk.Label(win, text="Capacidad:").grid(row=1, column=0, padx=8, pady=8)
        e = ttk.Entry(win); e.grid(row=1, column=1, padx=8, pady=8)
        cap = next(c for (a,b,c) in self.modelo.arcos if a==u and b==v)
        e.insert(0, f"{cap:g}")
        def ok():
            try:
                nueva = float(e.get())
                if nueva <= 0: raise ValueError("Capacidad > 0")
                self.modelo.actualizar_capacidad(u, v, nueva)
                self.ultimo_flujo.clear(); self.iteraciones.clear()
                self.redibujar(); win.destroy()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        ttk.Button(win, text="Guardar", command=ok).grid(row=2, column=0, columnspan=2, pady=8)

    def establecer_origen(self):
        """Fija el nodo de origen desde el combo."""
        nombre = self.combo_origen.get()
        if not nombre:
            return
        nid = self.modelo.nombre_a_id.get(nombre)
        if nid is None:
            messagebox.showerror("Error", "Nombre de origen no válido.")
            return
        self.id_origen = nid
        self.redibujar()

    def establecer_sumidero(self):
        """Fija el nodo de sumidero desde el combo."""
        nombre = self.combo_sumidero.get()
        if not nombre:
            return
        nid = self.modelo.nombre_a_id.get(nombre)
        if nid is None:
            messagebox.showerror("Error", "Nombre de sumidero no válido.")
            return
        self.id_sumidero = nid
        self.redibujar()

    def _ruta_de_iteracion(self, it):
        """Convierte una iteración a cadena de ruta con nombres."""
        nombres = [self.modelo.nodos[u][2] for (u, _) in it["camino"]]
        nombres.append(self.modelo.nodos[it["camino"][-1][1]][2])
        return " → ".join(nombres)

    def _calcular_ruta_optima(self):
        """Devuelve la ruta aumentante con mayor cuello (flujo máximo) y etiqueta formateada."""
        if not self.iteraciones:
            return "—"
        mejor = max(self.iteraciones, key=lambda it: it["cuello"])
        ruta_txt = self._ruta_de_iteracion(mejor)
        return f"{ruta_txt}  (flujo máximo={mejor['cuello']:g})"

    def mostrar_rutas(self):
        """Muestra ventana con resumen por ruta, detalle por iteración y total de flujo."""
        if not self.iteraciones:
            messagebox.showinfo("Rutas", "Primero calcula el flujo máximo."); return

        win = tk.Toplevel(self); win.title("Rutas encontradas")
        win.geometry("760x560")

        total_flujo = sum(it["cuello"] for it in self.iteraciones)

        resumen = {}
        for it in self.iteraciones:
            ruta = self._ruta_de_iteracion(it)
            d = resumen.setdefault(ruta, {"flujo": 0.0, "count": 0})
            d["flujo"] += it["cuello"]
            d["count"] += 1

        ttk.Label(win, text="Resumen por ruta", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10,4))
        tree_res = ttk.Treeview(win, columns=("ruta","flujo","iters"), show="headings", height=8)
        tree_res.heading("ruta", text="Ruta")
        tree_res.heading("flujo", text="Flujo máximo")
        tree_res.heading("iters", text="Iteraciones")
        tree_res.column("ruta", width=520, anchor="w")
        tree_res.column("flujo", width=110, anchor="e")
        tree_res.column("iters", width=100, anchor="center")
        tree_res.pack(fill="x", padx=10)

        for ruta, info in resumen.items():
            tree_res.insert("", "end", values=(ruta, f"{info['flujo']:g}", info["count"]))

        ttk.Label(win, text="Detalle por iteración", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10,4))
        tree_det = ttk.Treeview(win, columns=("k","ruta","flujo"), show="headings", height=12)
        tree_det.heading("k", text="Iteración")
        tree_det.heading("ruta", text="Ruta")
        tree_det.heading("flujo", text="Flujo máximo")
        tree_det.column("k", width=90, anchor="center")
        tree_det.column("ruta", width=520, anchor="w")
        tree_det.column("flujo", width=110, anchor="e")
        tree_det.pack(fill="both", expand=True, padx=10)

        for it in self.iteraciones:
            tree_det.insert("", "end", values=(it["k"], self._ruta_de_iteracion(it), f"{it['cuello']:g}"))

        ttk.Label(win, text=f"Total de flujo: {total_flujo:g}", font=("Segoe UI", 10, "bold")).pack(anchor="e", padx=10, pady=8)

    def calcular_flujo_maximo(self):
        """Ejecuta Edmonds–Karp, actualiza trazas y refresca la UI."""
        if self.id_origen is None or self.id_sumidero is None:
            messagebox.showwarning("Faltan datos", "Selecciona Origen y Sumidero."); return
        n = len(self.modelo.nodos)
        ek = FlujoMaximoEK(n)
        for (u,v,c) in self.modelo.arcos: ek.agregar_arco(u,v,c)
        try:
            valor, mapa_flujo, iteraciones = ek.maximo_flujo(self.id_origen, self.id_sumidero)
            self.ultimo_flujo = mapa_flujo
            self.ultimo_valor = valor
            self.iteraciones = iteraciones
            self.lbl_resultado.config(text=f"Valor de flujo: {valor:g}")
            self.lbl_ruta_optima.config(text=f"Ruta óptima: {self._calcular_ruta_optima()}")
            self.redibujar()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def nuevo_grafo(self):
        """Reinicia el grafo a vacío y limpia resultados."""
        if not messagebox.askyesno("Nuevo", "¿Vaciar el grafo actual?"): return
        self.modelo = ModeloGrafo(); self.id_origen=None; self.id_sumidero=None
        self.ultimo_flujo.clear(); self.iteraciones.clear(); self.ultimo_valor=0.0
        self.lbl_ruta_optima.config(text="Ruta óptima: —")
        self.redibujar()

    def guardar_json(self):
        """Guarda el grafo en un archivo JSON."""
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")], title="Guardar grafo")
        if not path: return
        try: self.modelo.exportar_json(path); messagebox.showinfo("Guardado","Grafo guardado.")
        except Exception as ex: messagebox.showerror("Error", str(ex))

    def abrir_json(self):
        """Abre un grafo desde un archivo JSON."""
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")], title="Abrir grafo")
        if not path: return
        try:
            self.modelo.importar_json(path)
            self.id_origen=None; self.id_sumidero=None
            self.ultimo_flujo.clear(); self.iteraciones.clear(); self.ultimo_valor=0.0
            self.lbl_ruta_optima.config(text="Ruta óptima: —")
            self.redibujar()
        except Exception as ex: messagebox.showerror("Error", str(ex))

    def exportar_csv(self):
        """Exporta flujos y resumen de iteraciones a CSV."""
        if not self.ultimo_flujo:
            messagebox.showwarning("Sin resultados","Primero calcula el flujo máximo."); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="Exportar flujo")
        if not path: return
        try:
            with open(path,"w",newline="",encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["u","v","capacidad","flujo"])
                nombres = [n[2] for n in self.modelo.nodos]
                cap_map = {(u,v):c for (u,v,c) in self.modelo.arcos}
                for (u,v),flujo in self.ultimo_flujo.items():
                    w.writerow([nombres[u], nombres[v], cap_map.get((u,v),""), f"{flujo:g}"])
                w.writerow([]); w.writerow(["Valor total de flujo", f"{self.ultimo_valor:g}"])
                w.writerow([])
                w.writerow(["Iteraciones (ruta por iteración)"])
                for it in self.iteraciones:
                    ruta_txt = self._ruta_de_iteracion(it)
                    w.writerow([f"({it['k']})", ruta_txt, f"flujo máximo={it['cuello']:g}"])
            messagebox.showinfo("Exportado", "CSV exportado correctamente.")
        except Exception as ex: messagebox.showerror("Error", str(ex))


if __name__ == "__main__":
    app = Aplicacion()
    """
    a = app.modelo.agregar_nodo(180, 180, "N0")
    b = app.modelo.agregar_nodo(180, 340, "N2")
    c = app.modelo.agregar_nodo(360, 260, "N1")
    d = app.modelo.agregar_nodo(560, 200, "N3")
    e = app.modelo.agregar_nodo(560, 340, "N4")
    f = app.modelo.agregar_nodo(760, 270, "N5")
    app.modelo.agregar_arco(a, d, 10)
    app.modelo.agregar_arco(a, b, 10)
    app.modelo.agregar_arco(b, c, 10)
    app.modelo.agregar_arco(c, e, 10)
    app.modelo.agregar_arco(d, f, 10)
    app.modelo.agregar_arco(e, f, 10)
    app.id_origen = a; app.id_sumidero = f
    """
    app.redibujar()
    app.mainloop()
