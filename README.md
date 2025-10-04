# MaxFlow

Aplicacion de escritorio (Tkinter) para **construir grafos** y **calcular el flujo maximo** con el algoritmo **Ford-Fulkerson**, con visualizacion interactiva, zoom, paneo y herramientas de edicion (nodos, arcos, capacidades), exportacion/importacion y reporte de iteraciones.

---

## Resumen de las funcionalidades de la app

- Dibuja nodos y arcos dirigidos con capacidades.
- Selecciona origen y destino, y calcula el **flujo maximo** (Edmonds–Karp es una implementación del método de Ford-Fulkerson).
- Muestra el **flujo por arco**, el **corte minimo** (zona punteada) y el **desglose por iteraciones** (veces).
- Interaccion moderna: **zoom con rueda**, **paneo** con boton medio/derecho o **espacio + arrastrar**, **(+, -)**.
- Persistencia: **guarda/abre** grafos en **JSON** y exporta resultados a **CSV**.
- Distribuible: se puede crear un **.exe** independiente (no requiere Python en la PC destino).

---

## Tabla de contenidos

- [Funciones principales](#funciones-principales)
- [Controles y atajos](#controles-y-atajos)
- [Formato de archivos](#formato-de-archivos)
- [Arquitectura del codigo](#arquitectura-del-codigo)
    - [FlujoMaximoEK](#1-flujomaximoek-algoritmo-edmondskarp)
    - [ModeloGrafo](#2-modelografo-modelo-de-datos)
    - [Aplicacion (Tk)](#3-aplicacion-tk-interfaz-y-render)
    - [Sistema de transformaciones](#4-sistema-de-transformaciones-zoom--pan)

---

## Funciones principales

- **Edicion de grafo**:
    - anadir, mover, renombrar y eliminar nodos
    - anadir, editar y eliminar arcos con capacidades

- **Calculo de flujo maximo**:
    - algoritmo Edmonds–Karp (BFS sobre grafo residual)
    - bitacora de iteraciones: camino aumentante y cuello

- **Visualizacion**:
    - grosor/color de arcos segun flujo
    - linea punteada aproximando el **corte minimo**
    - etiquetas de capacidades y anotaciones por iteracion

- **Persistencia**:
    - exportar/importar grafo a **JSON**
    - exportar resultados a **CSV** (capacidad, flujo, total, sumatorias)

- **UX**:
    - zoom centrado en el cursor
    - paneo del lienzo (mouse o barra espaciadora)
    - atajos de teclado y cuadro lateral de controles

---

## Controles y atajos

**Modos (panel derecho):**
- ➕ **Anadir nodo**: clic en el lienzo
- ✋ **Mover nodo**: arrastrar un nodo
- ➡️ **Anadir arco**: clic en origen y luego en destino
- 🗑️ **Eliminar**: clic sobre nodo o arco
- ✏️ **Renombrar nodo**: clic sobre nodo

**Inicio/Destino:** seleccionar en los combobox y presionar los botones respectivos.

**Calcular:** boton **▶ Calcular Flujo Maximo**.

**Navegacion del lienzo:**
- **Rueda** del mouse: **zoom** (centrado en el cursor)
- **Boton medio** o **boton derecho**: **paneo** (arrastrar)
- **Barra espaciadora + clic izquierdo**: **paneo** (mientras la mantengas)
- **+ / -**: zoom centrado en el canvas
- El cursor cambia a **fleur** cuando esta en modo paneo

---

## Formato de archivos

### JSON (grafo)
```json
{
  "nodos": [
    { "id": 0, "nombre": "N0", "x": 180.0, "y": 220.0 }
  ],
  "arcos": [
    { "u": 0, "v": 1, "capacidad": 10.0 }
  ]
}
```

## Arquitectura del código

La aplicación está organizada en tres componentes principales más un sistema de transformaciones para zoom y pan:

### 1) `FlujoMaximoEK`: algoritmo Edmonds–Karp
- Implementa el cálculo de flujo máximo mediante BFS sobre la red residual.  
- **Estructuras principales:**
  - `residual`: lista de diccionarios con capacidades residuales.
  - `original`: grafo inicial para reconstruir flujos al final.  
- **Métodos clave:**
  - `agregar_arco(u,v,cap)`: agrega un arco al grafo.
  - `_bfs(s,t)`: busca un camino aumentante.
  - `maximo_flujo(s,t)`: ejecuta el ciclo Edmonds–Karp, devuelve valor total, mapa de flujos y lista de iteraciones.
  - `alcanzables_en_residual(residual, s)`: obtiene el conjunto alcanzable desde `s` (útil para corte mínimo).

### 2) `ModeloGrafo`: modelo de datos
- Representa el grafo como listas de nodos y arcos.  
- **Estructuras:**
  - `nodos`: lista `(x, y, nombre)` en coordenadas de mundo.
  - `arcos`: lista `(u, v, capacidad)`.
  - `nombre_a_id`: diccionario para búsqueda rápida de nodos.  
- **Funciones principales:**
  - Añadir, mover, renombrar y eliminar nodos.
  - Añadir, actualizar y eliminar arcos.
  - Importar/exportar grafo en formato JSON.

### 3) `Aplicacion (Tk)`: interfaz gráfica
- Ventana principal con **Canvas** para dibujar grafo y panel lateral de controles.  
- **Responsabilidades:**
  - Gestión de modos de interacción (agregar/mover/eliminar/renombrar).
  - Dibujar nodos, arcos, capacidades, flujos y corte mínimo.
  - Mostrar resultados de iteraciones y resúmenes de rutas.
  - Manejar eventos de teclado y mouse.  
- **Estados importantes:**
  - `id_inicio`, `id_destino`: origen y destino para el flujo máximo.
  - `ultimo_flujo`, `ultimo_valor`, `iteraciones`: resultados del cálculo.
  - `corte_S`: conjunto de nodos alcanzables para visualizar el corte mínimo.

### 4) Sistema de transformaciones (zoom & pan)
- Permite navegar el lienzo de forma interactiva.  
- **Variables:**
  - `zoom`: factor de escala.
  - `offset`: desplazamiento del lienzo.  
- **Funciones:**
  - `w2s(x,y)`: convierte coordenadas de **mundo → pantalla**.
  - `s2w(sx,sy)`: convierte coordenadas de **pantalla → mundo**.  
- **Eventos soportados:**
  - Rueda del mouse para zoom.
  - Botón medio/derecho o espacio + arrastre para paneo.
  - Teclas `+` y `-` para zoom centrado en el canvas.

---

## Desarrollado por

**Sebastián Rojas**  
Código: **U202110299**  
Universidad / UPC

Grupo: **2**

Año: 2025  