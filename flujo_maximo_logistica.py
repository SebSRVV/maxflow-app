import json
import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class FlujoMaximoEK:
    def __init__(self, n):
        self.n = n
        self.residual = [dict() for _ in range(n)]
        self.original = [dict() for _ in range(n)]

    def agregar_arco(self, u, v, cap):
        if cap <= 0:
            raise ValueError("La capacidad debe ser > 0")
        self.residual[u][v] = self.residual[u].get(v, 0.0) + float(cap)
        self.residual[v].setdefault(u, 0.0)
        self.original[u][v] = self.original[u].get(v, 0.0) + float(cap)

    def _bfs(self, s, t):
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
        if s == t:
            return 0.0, {}, []
        iteraciones = []
        while True:
            camino = self._bfs(s, t)
            if not camino:
                break
            cuello = min(self.residual[u][v] for (u, v) in camino)
            for (u, v) in camino:
                self.residual[u][v] -= cuello
                self.residual[v][u] = self.residual[v].get(u, 0.0) + cuello
            iteraciones.append({"camino": camino[:], "cuello": cuello})
        mapa_flujo = {}
        for u in range(self.n):
            for v in self.original[u].keys():
                mapa_flujo[(u, v)] = self.residual[v].get(u, 0.0)
        valor_total = sum(self.residual[v].get(s, 0.0) for v in range(self.n))
        return valor_total, mapa_flujo, iteraciones

    @staticmethod
    def alcanzables_en_residual(residual, s):
        n = len(residual)
        vis = [False]*n
        q = [s]; vis[s] = True
        while q:
            u = q.pop(0)
            for v, cap in residual[u].items():
                if not vis[v] and cap > 1e-12:
                    vis[v] = True; q.append(v)
        return {i for i,ok in enumerate(vis) if ok}


# modelo de grafo
RADIO_NODO = 20

class ModeloGrafo:
    def __init__(self):
        self.nodos = []          # [(x,y,nombre)] coords de mundo
        self.arcos = []          # [(u,v,cap)]
        self.nombre_a_id = {}
        self.siguiente_idx_nombre = 0

    def agregar_nodo(self, x, y, nombre=None):
        if nombre is None:
            nombre = f"N{self.siguiente_idx_nombre}"; self.siguiente_idx_nombre += 1
        if nombre in self.nombre_a_id:
            raise ValueError("Nombre ya existe")
        nid = len(self.nodos)
        self.nodos.append((x, y, nombre))
        self.nombre_a_id[nombre] = nid
        return nid

    def renombrar_nodo(self, nid, nuevo):
        if nuevo in self.nombre_a_id and self.nombre_a_id[nuevo] != nid:
            raise ValueError("Nombre de nodo ya en uso")
        x, y, _ = self.nodos[nid]
        viejo = self.nodos[nid][2]
        self.nodos[nid] = (x, y, nuevo)
        del self.nombre_a_id[viejo]
        self.nombre_a_id[nuevo] = nid

    def mover_nodo(self, nid, x, y):
        n = self.nodos[nid]; self.nodos[nid] = (x, y, n[2])

    def eliminar_nodo(self, nid):
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
        if u == v:
            raise ValueError("No se permiten lazos")
        for i,(a,b,c) in enumerate(self.arcos):
            if a==u and b==v:
                self.arcos[i]=(a,b,c+float(cap)); return
        self.arcos.append((u,v,float(cap)))

    def actualizar_capacidad(self, u, v, nueva_cap):
        for i,(a,b,c) in enumerate(self.arcos):
            if a==u and b==v:
                self.arcos[i]=(a,b,float(nueva_cap)); return True
        return False

    def eliminar_arco(self, u, v):
        self.arcos = [(a,b,c) for (a,b,c) in self.arcos if not(a==u and b==v)]

    def exportar_json(self, path):
        datos = {
            "nodos":[{"id":i,"nombre":nm,"x":x,"y":y} for i,(x,y,nm) in enumerate(self.nodos)],
            "arcos":[{"u":u,"v":v,"capacidad":c} for (u,v,c) in self.arcos],
        }
        with open(path,"w",encoding="utf-8") as f: json.dump(datos,f,indent=2,ensure_ascii=False)

    def importar_json(self, path):
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


# interfaz tkinter
class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MaxFlow App")
        self.geometry("1920x1080")
        self.configure(bg="#F5F7FB")

        self.modelo = ModeloGrafo()
        self.id_inicio = None
        self.id_destino = None

        self.ultimo_flujo = {}
        self.ultimo_valor = 0.0
        self.iteraciones = []
        self.corte_S = set()
        self.corte_linea = None

        self.arco_pendiente_desde = None

        # transformaciones y navegacion
        self.zoom = 1.0
        self.offset = [0.0, 0.0]
        self.paneando = False
        self.pan_origen = (0, 0)
        self.offset_ini = (0.0, 0.0)
        self.nodo_arrastre = None
        self.offset_arrastre_world = (0.0, 0.0)

        # estado para paneo con espacio
        self.space_down = False

        self._construir_ui()
        self._vincular_eventos()
        self.redibujar()

    # util transformacion mundo↔pantalla
    def w2s(self, x, y):
        return x * self.zoom + self.offset[0], y * self.zoom + self.offset[1]

    def s2w(self, sx, sy):
        return (sx - self.offset[0]) / self.zoom, (sy - self.offset[1]) / self.zoom

    def _construir_ui(self):
        estilo = ttk.Style(self)
        try: estilo.theme_use("clam")
        except: pass
        estilo.configure("TButton", padding=8, font=("Segoe UI", 10))
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 13, "bold"))
        estilo.configure("Resultado.TLabel", font=("Segoe UI", 11, "bold"))
        estilo.configure("Rojo.TLabel", foreground="#DC3545", font=("Segoe UI", 10, "bold"))
        estilo.configure("Tag.TLabel", foreground="#555")
        estilo.configure("TFrame", background="#F5F7FB")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

        self.lienzo = tk.Canvas(self, bg="#ffffff", highlightthickness=0)
        self.lienzo.grid(row=0, column=0, sticky="nsew")
        self.lienzo.bind("<Configure>", lambda e: self._dibujar_cuadricula())

        lateral = ttk.Frame(self, padding=(12,10)); lateral.grid(row=0, column=1, sticky="ns")
        lateral.columnconfigure(0, weight=1)

        ttk.Label(lateral, text="Controles", style="Titulo.TLabel").grid(row=0, column=0, sticky="w", pady=(0,8))

        self.modo_var = tk.StringVar(value="agregar_nodo")
        for i,(txt,val) in enumerate([
            ("➕ Añadir nodo (click lienzo)", "agregar_nodo"),
            ("✋ Mover nodo (arrastrar)", "mover_nodo"),
            ("➡️ Añadir arco (inicio→destino)", "agregar_arco"),
            ("🗑️ Eliminar (nodo/arco)", "eliminar"),
            ("✏️ Renombrar nodo", "renombrar"),
        ], start=1):
            ttk.Radiobutton(lateral, text=txt, value=val, variable=self.modo_var).grid(row=i, column=0, sticky="w")

        ttk.Separator(lateral).grid(row=7, column=0, sticky="ew", pady=8)

        cap_fr = ttk.Frame(lateral); cap_fr.grid(row=8, column=0, sticky="ew", pady=(0,6))
        ttk.Label(cap_fr, text="Capacidad por defecto:").grid(row=0, column=0, sticky="w")
        self.entrada_capacidad = ttk.Entry(cap_fr, width=10)
        self.entrada_capacidad.grid(row=0, column=1, padx=(6,0))
        self.entrada_capacidad.insert(0, "10")

        ttk.Separator(lateral).grid(row=9, column=0, sticky="ew", pady=8)

        ttk.Label(lateral, text="Inicio / Destino", style="Titulo.TLabel").grid(row=10, column=0, sticky="w")
        r1 = ttk.Frame(lateral); r1.grid(row=11, column=0, sticky="ew", pady=2)
        self.combo_inicio = ttk.Combobox(r1, state="readonly"); self.combo_inicio.grid(row=0, column=0, padx=(0,6))
        ttk.Button(r1, text="🚩 Establecer Inicio", command=self.establecer_inicio).grid(row=0, column=1)
        r2 = ttk.Frame(lateral); r2.grid(row=12, column=0, sticky="ew", pady=2)
        self.combo_destino = ttk.Combobox(r2, state="readonly"); self.combo_destino.grid(row=0, column=0, padx=(0,6))
        ttk.Button(r2, text="🏁 Establecer Destino", command=self.establecer_destino).grid(row=0, column=1)

        ttk.Button(lateral, text="▶ Calcular Flujo Máximo", command=self.calcular_flujo_maximo).grid(row=13, column=0, sticky="ew", pady=(8,4))
        self.lbl_resultado = ttk.Label(lateral, text="Flujo máximo: —", style="Resultado.TLabel")
        self.lbl_resultado.grid(row=14, column=0, sticky="w", pady=(0,4))

        ttk.Label(lateral, text="Pesos:", style="Tag.TLabel").grid(row=15, column=0, sticky="w")
        self.lbl_pesos = ttk.Label(lateral, text="—", style="Tag.TLabel")
        self.lbl_pesos.grid(row=16, column=0, sticky="w")
        self.lbl_total = ttk.Label(lateral, text="", style="Rojo.TLabel")
        self.lbl_total.grid(row=17, column=0, sticky="w", pady=(0,6))

        ttk.Label(lateral, text="Arcos (u → v, capacidad)", style="Titulo.TLabel").grid(row=18, column=0, sticky="w", pady=(8,2))
        self.tabla = ttk.Treeview(lateral, columns=("u","v","cap"), show="headings", height=12)
        for col,txt,w in [("u","u",90),("v","v",90),("cap","Capacidad",110)]:
            self.tabla.heading(col, text=txt); self.tabla.column(col, width=w, anchor="center" if col!="cap" else "e")
        self.tabla.grid(row=19, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", self._editar_capacidad_dialogo)

        ttk.Separator(lateral).grid(row=20, column=0, sticky="ew", pady=8)

        f = ttk.Frame(lateral); f.grid(row=21, column=0, sticky="ew")
        ttk.Button(f, text="🆕 Nuevo", command=self.nuevo_grafo).grid(row=0, column=0, padx=2)
        ttk.Button(f, text="📂 Abrir JSON", command=self.abrir_json).grid(row=0, column=1, padx=2)
        ttk.Button(f, text="💾 Guardar JSON", command=self.guardar_json).grid(row=0, column=2, padx=2)
        ttk.Button(f, text="📤 Exportar CSV (flujo)", command=self.exportar_csv).grid(row=0, column=3, padx=2)

        ley = ttk.Frame(lateral); ley.grid(row=22, column=0, sticky="ew", pady=(8,0))
        ttk.Label(ley, text="🚩 Inicio   🏁 Destino   📦 Intermedio", style="Tag.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(ley, text="naranja: con flujo  •  gris: sin flujo  •  linea punteada: corte minimo  •  rueda: zoom  •  medio/derecho o espacio+izquierdo: pan", style="Tag.TLabel").grid(row=1, column=0, sticky="w")

        ttk.Button(lateral, text="🔎 Ver todas las rutas (resumen)", command=self.mostrar_rutas).grid(row=23, column=0, sticky="w", pady=(10,0))

    def _vincular_eventos(self):
        # click izquierdo habitual
        self.lienzo.bind("<Button-1>", self._click_lienzo)
        self.lienzo.bind("<B1-Motion>", self._arrastrar_lienzo)
        self.lienzo.bind("<ButtonRelease-1>", self._soltar_lienzo)

        # paneo con boton medio o derecho
        self.lienzo.bind("<Button-2>", self._pan_inicio)
        self.lienzo.bind("<B2-Motion>", self._pan_mover)
        self.lienzo.bind("<ButtonRelease-2>", self._pan_fin)
        self.lienzo.bind("<Button-3>", self._pan_inicio)
        self.lienzo.bind("<B3-Motion>", self._pan_mover)
        self.lienzo.bind("<ButtonRelease-3>", self._pan_fin)

        # zoom rueda
        self.lienzo.bind("<MouseWheel>", self._on_mousewheel)
        self.lienzo.bind("<Button-4>", lambda e: self._zoom_en_cursor(e, +1))
        self.lienzo.bind("<Button-5>", lambda e: self._zoom_en_cursor(e, -1))

        # atajos de teclado
        self.bind("+", lambda e: self._zoom_centrado(+1))
        self.bind("-", lambda e: self._zoom_centrado(-1))
        self.bind("=", lambda e: self._zoom_centrado(+1))

        # paneo con espacio: presionar y soltar
        self.bind("<KeyPress-space>", self._space_press)
        self.bind("<KeyRelease-space>", self._space_release)

    # grafico
    def _dibujar_cuadricula(self):
        self.lienzo.delete("grid")
        w = self.lienzo.winfo_width(); h = self.lienzo.winfo_height()
        paso_world = 24
        paso = max(8, int(paso_world * self.zoom))
        if paso <= 0: paso = 8
        ox = int(self.offset[0]) % paso
        oy = int(self.offset[1]) % paso
        for x in range(ox, w, paso):
            self.lienzo.create_line(x,0,x,h, fill="#f0f2f6", tags="grid")
        for y in range(oy, h, paso):
            self.lienzo.create_line(0,y,w,y, fill="#f0f2f6", tags="grid")

    def redibujar(self):
        self.lienzo.delete("all")
        self._dibujar_cuadricula()

        for (u,v,cap) in self.modelo.arcos:
            self._dibujar_arco(u,v,cap)

        if self.corte_S and len(self.corte_S) < len(self.modelo.nodos):
            p1, p2 = self._linea_corte_mediatriz(self.corte_S)
            if p1 and p2:
                p1s = self.w2s(*p1); p2s = self.w2s(*p2)
                self.lienzo.create_line(p1s[0], p1s[1], p2s[0], p2s[1],
                                        dash=(6,4), width=2, fill="#6C757D")
                mx = (p1s[0]+p2s[0])/2; my = (p1s[1]+p2s[1])/2
                self.lienzo.create_text(mx+8, my-8, text="Corte mínimo",
                                        anchor="w", fill="#6C757D", font=("Segoe UI", 9, "bold"))

        for i,(x,y,nombre) in enumerate(self.modelo.nodos):
            self._dibujar_nodo(i,x,y,nombre)

        self._refrescar_combos_nodo()
        self._refrescar_tabla_arcos()

    def _icono_nodo(self, nid):
        if nid == self.id_inicio: return "🚩"
        if nid == self.id_destino: return "🏁"
        return "📦"

    def _dibujar_nodo(self, nid, x, y, nombre):
        sx, sy = self.w2s(x, y)
        r = max(6, RADIO_NODO * self.zoom)
        self.lienzo.create_oval(sx-r-2, sy-r-2, sx+r+2, sy+r+2,
                                fill="#E9F2FF", outline="", tags=f"nodo_{nid}")
        color = "#0D6EFD"
        if nid == self.id_inicio: color = "#198754"
        elif nid == self.id_destino: color = "#DC3545"
        self.lienzo.create_oval(sx-r, sy-r, sx+r, sy+r, fill=color, outline="#1b1b1b",
                                width=1.5, tags=f"nodo_{nid}")
        self.lienzo.create_text(sx, sy-2, text=self._icono_nodo(nid), font=("Segoe UI Emoji", 12), fill="white")
        self.lienzo.create_text(sx, sy+12, text=nombre, fill="white", font=("Segoe UI", 9, "bold"))

    def _coords_arco(self, u, v):
        x1,y1,_ = self.modelo.nodos[u]; x2,y2,_ = self.modelo.nodos[v]
        ang = math.atan2(y2-y1, x2-x1)
        sx = x1 + RADIO_NODO*math.cos(ang); sy = y1 + RADIO_NODO*math.sin(ang)
        ex = x2 - RADIO_NODO*math.cos(ang); ey = y2 - RADIO_NODO*math.sin(ang)
        return sx,sy,ex,ey,ang

    def _log_acumulado_arco(self, u, v):
        totales = []
        total = 0.0
        for it in self.iteraciones:
            if (u,v) in it["camino"]:
                total += it["cuello"]
                totales.append(total)
        return totales

    def _dibujar_arco(self, u, v, capacidad):
        sx,sy,ex,ey,_ = self._coords_arco(u,v)
        ssx, ssy = self.w2s(sx, sy)
        eex, eey = self.w2s(ex, ey)
        flujo = self.ultimo_flujo.get((u,v), 0.0)

        color = "#FF8C00" if flujo > 1e-12 else "#5f6368"
        base = 2 + (math.log2(flujo+1)*4 if flujo > 1e-12 else 0)
        grosor = max(2, min(10, int(base)))
        arrow = (12*self.zoom, 14*self.zoom, 5*self.zoom)

        self.lienzo.create_line(ssx,ssy,eex,eey, arrow=tk.LAST, width=grosor, fill=color, smooth=True,
                                arrowshape=arrow, tags=f"arco_{u}_{v}")

        midx, midy = (ssx+eex)/2, (ssy+eey)/2
        etiqueta = f"{capacidad:g}"
        self.lienzo.create_rectangle(midx-4, midy-18, midx+4+7*len(etiqueta)/2, midy-2, fill="#ffffff", outline="", stipple="gray25")
        self.lienzo.create_text(midx+2, midy-10, text=etiqueta, fill="#111", font=("Segoe UI", 9))

        palette = ["#6f42c1", "#0d6efd", "#198754", "#fd7e14", "#d63384", "#20c997", "#845ef7", "#12b886"]
        totales = self._log_acumulado_arco(u, v)
        if totales:
            yoff = 10
            nombre_u = self.modelo.nodos[u][2]
            for i, total in enumerate(totales):
                col = palette[i % len(palette)]
                self.lienzo.create_text(midx, midy+yoff, text="[", fill=col, font=("Consolas", 9), anchor="w")
                x1 = midx + 7*1
                self.lienzo.create_text(x1, midy+yoff, text=nombre_u, fill="#444", font=("Consolas", 9), anchor="w")
                x2 = x1 + 7*len(nombre_u)
                self.lienzo.create_text(x2, midy+yoff, text=",", fill=col, font=("Consolas", 9), anchor="w")
                x3 = x2 + 7*2
                num_txt = f"{total:g}"
                self.lienzo.create_text(x3, midy+yoff, text=num_txt, fill="#DC3545", font=("Consolas", 9, "bold"), anchor="w")
                x4 = x3 + 7*len(num_txt)
                self.lienzo.create_text(x4, midy+yoff, text="]", fill=col, font=("Consolas", 9), anchor="w")
                yoff += 14

    def _refrescar_combos_nodo(self):
        nombres = [n[2] for n in self.modelo.nodos]
        if hasattr(self, "combo_inicio"):
            self.combo_inicio["values"] = nombres
            if self.id_inicio is not None and self.id_inicio < len(nombres):
                self.combo_inicio.set(nombres[self.id_inicio])
        if hasattr(self, "combo_destino"):
            self.combo_destino["values"] = nombres
            if self.id_destino is not None and self.id_destino < len(nombres):
                self.combo_destino.set(nombres[self.id_destino])

    def _refrescar_tabla_arcos(self):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        for (u,v,c) in self.modelo.arcos:
            self.tabla.insert("", "end", values=(self.modelo.nodos[u][2], self.modelo.nodos[v][2], f"{c:g}"))

    # corte minimo en mundo
    def _linea_corte_mediatriz(self, Sset):
        if not self.modelo.nodos: return None, None
        Tset = [i for i in range(len(self.modelo.nodos)) if i not in Sset]
        if not Sset or not Tset: return None, None
        sx = sum(self.modelo.nodos[i][0] for i in Sset)/len(Sset)
        sy = sum(self.modelo.nodos[i][1] for i in Sset)/len(Sset)
        tx = sum(self.modelo.nodos[i][0] for i in Tset)/len(Tset)
        ty = sum(self.modelo.nodos[i][1] for i in Tset)/len(Tset)
        if abs(sx-tx) < 1e-6 and abs(sy-ty) < 1e-6:
            w = self.lienzo.winfo_width(); h = self.lienzo.winfo_height()
            xm, _ = self.s2w(sx, 0)
            return (xm, 0), (xm, h)
        vx, vy = tx - sx, ty - sy
        mx, my = (sx+tx)/2, (sy+ty)/2
        dx, dy = -vy, vx
        norm = math.hypot(dx, dy)
        if norm < 1e-9: dx, dy = 1.0, 0.0
        else: dx, dy = dx/norm, dy/norm
        w = self.lienzo.winfo_width(); h = self.lienzo.winfo_height()
        L = max(w, h) / self.zoom * 2.0
        return (mx - dx*L, my - dy*L), (mx + dx*L, my + dy*L)

    # busquedas hit test
    def _buscar_nodo_en(self, sx, sy):
        x, y = self.s2w(sx, sy)
        r2 = (RADIO_NODO + 2)**2
        for i,(nx,ny,_) in enumerate(self.modelo.nodos):
            if (nx-x)**2 + (ny-y)**2 <= r2:
                return i
        return None

    def _buscar_arco_en(self, sx, sy):
        mejor=None; mejor_d=8.0
        for (u,v,_) in self.modelo.arcos:
            wx1,wy1,wx2,wy2,_ = self._coords_arco(u,v)
            x1,y1 = self.w2s(wx1,wy1); x2,y2 = self.w2s(wx2,wy2)
            dx,dy = x2-x1, y2-y1
            if abs(dx)<1e-9 and abs(dy)<1e-9: continue
            t = max(0, min(1, ((sx-x1)*dx + (sy-y1)*dy)/(dx*dx+dy*dy)))
            qx,qy = x1 + t*dx, y1 + t*dy
            d = math.hypot(sx-qx, sy-qy)
            if d < mejor_d: mejor_d=d; mejor=(u,v)
        return mejor

    # interaccion principal con soporte de espacio para pan
    def _click_lienzo(self, e):
        # si se mantiene espacio, iniciar paneo con izquierdo
        if self.space_down:
            self._pan_inicio(e)
            return

        modo = self.modo_var.get()
        if modo == "agregar_nodo":
            try:
                wx, wy = self.s2w(e.x, e.y)
                self.modelo.agregar_nodo(wx, wy, None)
                self._limpiar_resultados(); self.redibujar()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        elif modo == "agregar_arco":
            nid = self._buscar_nodo_en(e.x, e.y)
            if nid is None: return
            if self.arco_pendiente_desde is None:
                self.arco_pendiente_desde = nid
                self.lbl_resultado.config(text=f"Elige destino desde {self.modelo.nodos[nid][2]}")
            else:
                if nid == self.arco_pendiente_desde:
                    self.arco_pendiente_desde = None; return
                try:
                    cap = float(self.entrada_capacidad.get())
                    self.modelo.agregar_arco(self.arco_pendiente_desde, nid, cap)
                    self.arco_pendiente_desde = None
                    self._limpiar_resultados(); self.redibujar()
                except Exception as ex: messagebox.showerror("Error", str(ex))
        elif modo == "mover_nodo":
            self.nodo_arrastre = self._buscar_nodo_en(e.x, e.y)
            if self.nodo_arrastre is not None:
                wx, wy = self.s2w(e.x, e.y)
                nx, ny, _ = self.modelo.nodos[self.nodo_arrastre]
                self.offset_arrastre_world = (wx - nx, wy - ny)
        elif modo == "eliminar":
            nid = self._buscar_nodo_en(e.x, e.y)
            if nid is not None:
                if messagebox.askyesno("Eliminar", f"¿Eliminar nodo {self.modelo.nodos[nid][2]} y sus arcos?"):
                    self.modelo.eliminar_nodo(nid)
                    if self.id_inicio == nid: self.id_inicio=None
                    if self.id_destino == nid: self.id_destino=None
                    self._limpiar_resultados(); self.redibujar()
                return
            ed = self._buscar_arco_en(e.x, e.y)
            if ed:
                u,v = ed
                if messagebox.askyesno("Eliminar arco", f"¿Eliminar {self.modelo.nodos[u][2]} → {self.modelo.nodos[v][2]}?"):
                    self.modelo.eliminar_arco(u,v)
                    self._limpiar_resultados(); self.redibujar()
        elif modo == "renombrar":
            nid = self._buscar_nodo_en(e.x, e.y)
            if nid is not None: self._dialogo_renombrar_nodo(nid)

    def _arrastrar_lienzo(self, e):
        # si espacio presionado, pan con izquierdo durante el arrastre
        if self.space_down and self.paneando:
            self._pan_mover(e)
            return
        if self.modo_var.get()=="mover_nodo" and self.nodo_arrastre is not None:
            wx, wy = self.s2w(e.x, e.y)
            dx, dy = self.offset_arrastre_world
            nx = wx - dx
            ny = wy - dy
            sx, sy = self.w2s(nx, ny)
            r = RADIO_NODO * self.zoom + 4
            sx = max(r, min(self.lienzo.winfo_width()-r, sx))
            sy = max(r, min(self.lienzo.winfo_height()-r, sy))
            nx, ny = self.s2w(sx, sy)
            self.modelo.mover_nodo(self.nodo_arrastre, nx, ny)
            self.redibujar()

    def _soltar_lienzo(self, e):
        # terminar paneo si venia con espacio+izquierdo
        if self.space_down and self.paneando:
            self._pan_fin(e)
            return
        self.nodo_arrastre=None

    # paneo comun (medio/derecho o espacio+izquierdo)
    def _pan_inicio(self, e):
        self.paneando = True
        self.pan_origen = (e.x, e.y)
        self.offset_ini = (self.offset[0], self.offset[1])
        self.lienzo.configure(cursor="fleur")

    def _pan_mover(self, e):
        if not self.paneando: return
        dx = e.x - self.pan_origen[0]
        dy = e.y - self.pan_origen[1]
        self.offset[0] = self.offset_ini[0] + dx
        self.offset[1] = self.offset_ini[1] + dy
        self.redibujar()

    def _pan_fin(self, _e):
        self.paneando = False
        self.lienzo.configure(cursor="")

    # zoom
    def _on_mousewheel(self, e):
        direction = 1 if e.delta > 0 else -1
        self._zoom_en_cursor(e, direction)

    def _zoom_en_cursor(self, e, direction):
        old_zoom = self.zoom
        factor = 1.1 if direction > 0 else (1/1.1)
        new_zoom = max(0.3, min(4.0, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 1e-6:
            return
        wx, wy = self.s2w(e.x, e.y)
        self.zoom = new_zoom
        self.offset[0] = e.x - wx * self.zoom
        self.offset[1] = e.y - wy * self.zoom
        self.redibujar()

    def _zoom_centrado(self, direction):
        cx = self.lienzo.winfo_width()//2
        cy = self.lienzo.winfo_height()//2
        dummy = type("E", (), {"x": cx, "y": cy})
        self._zoom_en_cursor(dummy, direction)

    # teclado espacio para pan
    def _space_press(self, _e):
        self.space_down = True
        self.lienzo.configure(cursor="fleur")

    def _space_release(self, _e):
        self.space_down = False
        if not self.paneando:
            self.lienzo.configure(cursor="")

    # dialogos
    def _dialogo_renombrar_nodo(self, nid):
        win = tk.Toplevel(self); win.title("Renombrar nodo")
        ttk.Label(win, text="Nuevo nombre:").grid(row=0, column=0, padx=8, pady=8)
        e = ttk.Entry(win); e.grid(row=0, column=1, padx=8, pady=8); e.insert(0, self.modelo.nodos[nid][2])
        def ok():
            nuevo = e.get().strip()
            if not nuevo: messagebox.showerror("Error", "Nombre vacío"); return
            try:
                self.modelo.renombrar_nodo(nid, nuevo); self.redibujar(); win.destroy()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        ttk.Button(win, text="Guardar", command=ok).grid(row=1, column=0, columnspan=2, pady=8)

    def _editar_capacidad_dialogo(self, event):
        item = self.tabla.identify_row(event.y)
        if not item: return
        u_nom, v_nom, _ = self.tabla.item(item, "values")
        u = self.modelo.nombre_a_id[u_nom]; v = self.modelo.nombre_a_id[v_nom]
        self._dialogo_capacidad(u, v)

    def _dialogo_capacidad(self, u, v):
        win = tk.Toplevel(self); win.title("Editar capacidad")
        ttk.Label(win, text=f"Arco {self.modelo.nodos[u][2]} → {self.modelo.nodos[v][2]}").grid(row=0, column=0, columnspan=2, padx=8, pady=(8,4))
        ttk.Label(win, text="Capacidad:").grid(row=1, column=0, padx=8, pady=8)
        e = ttk.Entry(win); e.grid(row=1, column=1, padx=8, pady=8)
        cap = next(c for (a,b,c) in self.modelo.arcos if a==u and b==v); e.insert(0, f"{cap:g}")
        def ok():
            try:
                nueva = float(e.get())
                if nueva <= 0: raise ValueError("Capacidad > 0")
                self.modelo.actualizar_capacidad(u, v, nueva)
                self._limpiar_resultados(); self.redibujar(); win.destroy()
            except Exception as ex: messagebox.showerror("Error", str(ex))
        ttk.Button(win, text="Guardar", command=ok).grid(row=2, column=0, columnspan=2, pady=8)

    # acciones
    def establecer_inicio(self):
        nombre = self.combo_inicio.get()
        if not nombre: return
        nid = self.modelo.nombre_a_id.get(nombre)
        if nid is None: messagebox.showerror("Error", "Nombre de inicio no válido."); return
        self.id_inicio = nid; self.redibujar()

    def establecer_destino(self):
        nombre = self.combo_destino.get()
        if not nombre: return
        nid = self.modelo.nombre_a_id.get(nombre)
        if nid is None: messagebox.showerror("Error", "Nombre de destino no válido."); return
        self.id_destino = nid; self.redibujar()

    def _ruta_de_iteracion(self, it):
        nombres = [self.modelo.nodos[u][2] for (u, _) in it["camino"]]
        nombres.append(self.modelo.nodos[it["camino"][-1][1]][2])
        return " → ".join(nombres)

    def _actualizar_desglose_panel(self):
        if not self.iteraciones:
            self.lbl_pesos.config(text="—"); self.lbl_total.config(text=""); return
        partes = " + ".join(f"{it['cuello']:g}" for it in self.iteraciones)
        total = sum(it["cuello"] for it in self.iteraciones)
        self.lbl_pesos.config(text=partes)
        self.lbl_total.config(text=f"Total: {total:g}")

    def mostrar_rutas(self):
        if not self.iteraciones:
            messagebox.showinfo("Rutas", "Primero calcula el flujo máximo."); return
        win = tk.Toplevel(self); win.title("Rutas encontradas"); win.geometry("760x420")
        total_flujo = sum(it["cuello"] for it in self.iteraciones)
        resumen = {}
        for it in self.iteraciones:
            ruta = self._ruta_de_iteracion(it)
            d = resumen.setdefault(ruta, {"flujo": 0.0, "count": 0})
            d["flujo"] += it["cuello"]; d["count"] += 1
        ttk.Label(win, text="Resumen por ruta", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10,4))
        tree_res = ttk.Treeview(win, columns=("ruta","flujo","iters"), show="headings", height=12)
        tree_res.heading("ruta", text="Ruta")
        tree_res.heading("flujo", text="Flujo (pesos)")
        tree_res.heading("iters", text="Veces")
        tree_res.column("ruta", width=520, anchor="w")
        tree_res.column("flujo", width=130, anchor="e")
        self.lienzo.update_idletasks()
        tree_res.column("iters", width=90, anchor="center")
        tree_res.pack(fill="both", expand=True, padx=10)
        for ruta, info in resumen.items():
            tree_res.insert("", "end", values=(ruta, f"{info['flujo']:g}", info["count"]))
        ttk.Label(win, text=f"Total de flujo: {total_flujo:g}", font=("Segoe UI", 10, "bold")).pack(anchor="e", padx=10, pady=8)

    def _limpiar_resultados(self):
        self.ultimo_flujo.clear(); self.iteraciones.clear(); self.ultimo_valor = 0.0
        self.corte_S = set(); self.corte_linea = None
        self.lbl_resultado.config(text="Flujo máximo: —")
        self.lbl_pesos.config(text="—"); self.lbl_total.config(text="")

    def calcular_flujo_maximo(self):
        if self.id_inicio is None or self.id_destino is None:
            messagebox.showwarning("Faltan datos", "Selecciona Inicio y Destino."); return
        n = len(self.modelo.nodos)
        ek = FlujoMaximoEK(n)
        for (u,v,c) in self.modelo.arcos: ek.agregar_arco(u,v,c)
        try:
            valor, mapa_flujo, iteraciones = ek.maximo_flujo(self.id_inicio, self.id_destino)
            self.ultimo_flujo = mapa_flujo
            self.ultimo_valor = valor
            self.iteraciones = iteraciones
            self.lbl_resultado.config(text=f"Flujo máximo: {valor:g}")
            self._actualizar_desglose_panel()
            self.corte_S = FlujoMaximoEK.alcanzables_en_residual(ek.residual, self.id_inicio)
            self.redibujar()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def nuevo_grafo(self):
        if not messagebox.askyesno("Nuevo", "¿Vaciar el grafo actual?"): return
        self.modelo = ModeloGrafo(); self.id_inicio=None; self.id_destino=None
        self._limpiar_resultados(); self.redibujar()

    def guardar_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")], title="Guardar grafo")
        if not path: return
        try: self.modelo.exportar_json(path); messagebox.showinfo("Guardado","Grafo guardado.")
        except Exception as ex: messagebox.showerror("Error", str(ex))

    def abrir_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")], title="Abrir grafo")
        if not path: return
        try:
            self.modelo.importar_json(path)
            self.id_inicio=None; self.id_destino=None
            self._limpiar_resultados(); self.redibujar()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def exportar_csv(self):
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
                w.writerow([]); w.writerow(["Flujo máximo total", f"{self.ultimo_valor:g}"])
                if self.iteraciones:
                    w.writerow([]); w.writerow(["Pesos:"])
                    w.writerow(["+", *[f"{it['cuello']:g}" for it in self.iteraciones]])
                    w.writerow(["Total", f"{sum(it['cuello'] for it in self.iteraciones):g}"])
            messagebox.showinfo("Exportado", "CSV exportado correctamente.")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))


if __name__ == "__main__":
    app = Aplicacion()
    app.redibujar()
    app.mainloop()
