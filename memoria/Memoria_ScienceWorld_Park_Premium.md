# ScienceWorld Park · Memoria del Proyecto
Luis Villegas Rivera · Python · PySide6 · Peewee · SQLite · PyInstaller · 2026

---

## ÍNDICE DE CONTENIDOS
1. INFORMACIÓN GENERAL  
1.1 Objetivo del sistema  
1.2 Alcance  
2. CONCEPTO DEL PROYECTO  
2.1 Título  
2.2 Descripción general  
2.3 Funcionalidades destacadas  
3. JUSTIFICACIÓN DEL PROYECTO  
3.1 Necesidad del mercado  
3.2 Innovación tecnológica  
3.3 Beneficios esperados  
4. TECNOLOGÍAS EMPLEADAS  
4.1 Lenguaje de programación  
4.2 Base de datos  
4.3 Librerías principales  
4.4 Arquitectura  
5. INGENIERÍA DEL SOFTWARE  
5.1 Storyboard  
5.2 Diagrama de flujo (lógico)  
5.3 Estructura del proyecto  
6. DIFICULTADES ENCONTRADAS  
6.1 Técnicas  
6.2 Base de datos  
6.3 Lógica de negocio  
7. ANÁLISIS DAFO  
7.1 Matriz DAFO  
8. ANÁLISIS DE DATOS  
8.1 Tablas principales  
9. PROYECCIÓN FUTURA  
9.1 Mejoras inmediatas  
9.2 Funcionalidades avanzadas  
10. CONCLUSIONES  
10.1 Logros alcanzados  
10.2 Valoración personal  
10.3 Impacto esperado

---

## 1. INFORMACIÓN GENERAL
**Cliente:** Uso personal / Proyecto académico  
**Tipo de proyecto:** Aplicación de escritorio — Simulador de gestión de parque temático científico  
**Desarrollador:** Luis Villegas Rivera  
**Fecha de entrega:** 2026-04-28  
**Tecnologías:** Python · PySide6 · Peewee · SQLite · PyInstaller

### 1.1 Objetivo del sistema
Desarrollar una aplicación de escritorio profesional que simule la gestión integral de un parque temático de ciencia, con control de economía, personal, atracciones, logística, eventos aleatorios y progresión por fases. El sistema debe mantener persistencia local, flujo de partida completo (login → carga/creación → simulación), y una interfaz retro limpia orientada a decisiones de gestión.

### 1.2 Alcance
- Login, registro, selección y creación de partidas con modo y dificultad.
- Motor de simulación por ticks (1 tick = 1 hora in-game).
- Economía operativa: ingresos por taquilla + gastos por nóminas, logística y reparaciones.
- Catálogo de atracciones con construcción por fases y tiempos de obra.
- Gestión de plantilla y control de requisitos de personal por proyecto.
- Logística de inventario con pedidos y consumo operativo.
- Dashboard con KPIs y historial de eventos.
- Persistencia SQLite embebida y distribución ejecutable.

---

## 2. CONCEPTO DEL PROYECTO
### 2.1 Título
**ScienceWorld Park — Sistema de Gestión de Parque Temático Científico (Desktop Manager)**

### 2.2 Descripción general
ScienceWorld Park es un simulador de gestión donde el jugador administra un parque de divulgación científica dividido en ocho secciones temáticas. El núcleo jugable combina planificación estratégica (construcción, contratación, precios), operación diaria (tick, incidencias, stock, mantenimiento) y decisiones de crecimiento (priorización de proyectos, equilibrio económico y reputacional).  
El sistema integra una UX retro unificada, orientada a legibilidad y rapidez de operación.

### 2.3 Funcionalidades destacadas
**Motor de simulación**
- Tick horario con cierre diario y procesamiento de ciclos económicos.
- Afluencia dinámica por reputación, hora y estado viral.
- Degradación de atracciones y eventos aleatorios con impacto real.

**Gestión de atracciones**
- Operativas, obras en curso y cartera de proyectos separadas por pestañas.
- Construcción por días y prioridad (baja/media/alta).
- Límite de obras simultáneas y reasignación de técnicos.
- Restricciones por fase de desbloqueo y requisitos de personal.

**Gestión empresarial**
- Finanzas por categoría con P&L diario e histórico.
- Inventario ampliado y compra de suministros transaccional.
- Control de empleados activos, contratación y coste operativo.

---

## 3. JUSTIFICACIÓN DEL PROYECTO
### 3.1 Necesidad del mercado
Los simuladores académicos suelen resolver lógica de negocio pero no integran una capa UX sólida y un flujo empresarial completo. Este proyecto cubre ese hueco: une dominio, persistencia, simulación y GUI en una misma solución mantenible.

### 3.2 Innovación tecnológica
- Motor desacoplado de la vista (señales + actualización de panel activo).
- Persistencia robusta con migraciones incrementales en SQLite/Peewee.
- Sistema de construcción con cola limitada, prioridad y sobrecarga técnica.
- Tema retro global consistente con densidad UI configurable y persistente.

### 3.3 Beneficios esperados
**Para usuario/jugador**
- Curva de aprendizaje baja y visión clara del estado del parque.
- Decisiones estratégicas con consecuencias reales.
- Experiencia visual coherente y ligera.

**Para desarrollador**
- Base sólida para escalar a más secciones, eventos y sistemas.
- Arquitectura modular útil como portafolio profesional.
- Código testable y empaquetable como ejecutable standalone.

---

## 4. TECNOLOGÍAS EMPLEADAS
### 4.1 Lenguaje de programación
Python 3.11

### 4.2 Base de datos
SQLite embebida con ORM Peewee (WAL + FK + migraciones).

### 4.3 Librerías principales
- `PySide6`: interfaz gráfica de escritorio.
- `peewee`: modelado ORM y consultas.
- `bcrypt`: hashing de credenciales.
- `pytest` / `pytest-qt`: validación automatizada.
- `pyinstaller`: empaquetado ejecutable.

### 4.4 Arquitectura
- `core/`: motor y eventos.
- `models/`: persistencia y seeds.
- `domain/`: lógica de dominio desacoplada.
- `gui/`: vistas y ventanas.
- `tests/`: pruebas unitarias y de integración básica.

---

## 5. INGENIERÍA DEL SOFTWARE
### 5.1 Storyboard (ficheros principales)
| Fichero | Responsabilidad |
|---|---|
| `main.py` | Arranque de app, inicialización de DB, login y ventana principal |
| `gui/login_window.py` | Login, registro y creación/carga de partida |
| `gui/main_window.py` | Shell principal, sidebar, navegación y control de tiempo |
| `core/motor.py` | Tick, economía diaria, eventos, degradación y riesgo operativo |
| `gui/vistas/atracciones.py` | Operativas, obras y cartera de proyectos |
| `gui/vistas/finanzas.py` | KPIs financieros, P&L y histórico |
| `gui/vistas/logistica.py` | Pedidos de inventario y stock |
| `gui/vistas/personal.py` | Plantilla y contratación |
| `models/db.py` | Inicialización de tablas, migraciones y seeds por dificultad |

### 5.2 Diagrama de flujo (lógico)
El diagrama se encuentra en:

`diagramas_flujo/flujo_principal_scienceworld.mmd`

### 5.3 Estructura del proyecto
```
Proyecto_06_LuisVillegas/
├─ core/
├─ domain/
├─ gui/
│  ├─ vistas/
│  ├─ login_window.py
│  └─ main_window.py
├─ models/
├─ tests/
├─ diagramas_flujo/
│  └─ flujo_principal_scienceworld.mmd
├─ memoria/
│  └─ Memoria_ScienceWorld_Park_Premium.md
├─ main.py
└─ scienceworld.db
```

---

## 6. DIFICULTADES ENCONTRADAS
### 6.1 Técnicas
- Sincronizar refresco de vistas con tick sin bloquear UI.
- Mantener tema visual uniforme al coexistir estilos heredados.
- Evitar sobrecarga visual al ampliar funcionalidades.

### 6.2 Base de datos
- Evolución del esquema con nuevas columnas sin romper partidas existentes.
- Seeds incrementales para no depender de DB vacía.
- Cohesión entre defaults ORM y migraciones SQL.

### 6.3 Lógica de negocio
- Balance entre requisitos de personal, fases y economía para construir.
- Penalizar sobrecarga sin volver injugable la progresión.
- Ajustar afluencia y reputación para mantener loop de juego estable.

---

## 7. ANÁLISIS DAFO
### 7.1 Matriz DAFO
**FORTALEZAS**
- Arquitectura modular y legible.
- Simulación end-to-end conectada (login→partida→motor→vistas).
- UX retro consistente y configurable.
- Persistencia local sólida.

**DEBILIDADES**
- Balance todavía ajustable en economía avanzada.
- Sin sistema multijugador ni online.
- Dependencia actual de escritorio (no web/mobile).

**OPORTUNIDADES**
- Exportación de reportes PDF/CSV desde interfaz.
- Modo campaña narrativo y objetivos por hitos.
- Integración de analítica avanzada por sección.

**AMENAZAS**
- Incremento de complejidad si se añaden más subsistemas sin refactor.
- Crecimiento de deuda técnica visual si no se centraliza aún más la UI.
- Dependencia de cambios en librerías GUI/ORM.

---

## 8. ANÁLISIS DE DATOS
### 8.1 Tablas principales
| Tabla | Descripción | Campos clave |
|---|---|---|
| `parque` | Estado global de la partida | dinero, reputacion, dia_actual, hora_actual |
| `atracciones` | Catálogo y estado operativo | tipo, integridad, construida, en_construccion, prioridad |
| `empleados` | Plantilla de personal | tipo, salario_mes, seccion, activo |
| `inventario` | Productos y stock | categoria, stock_actual, stock_minimo, stock_maximo |
| `finanzas` | Movimientos económicos | tipo, categoria, importe, dia_juego, hora_juego |
| `eventos_log` | Historial de incidencias | tipo, descripcion, dia_juego, hora_juego |
| `usuarios` / `partidas` | Acceso y sesiones de juego | username, password_h, modo, dificultad_key |

---

## 9. PROYECCIÓN FUTURA
### 9.1 Mejoras inmediatas
- Persistencia de más preferencias UI (filtros por vista, orden de tablas).
- Panel de alertas críticas con acciones sugeridas.
- Ajuste fino del balance por dificultad.
- Reporte diario exportable.

### 9.2 Funcionalidades avanzadas
- Sistema de préstamos y rating crediticio.
- Árbol tecnológico y desbloqueos I+D.
- Simulación de colas por atracción y perfil de visitante.
- Integración de minimapa operativo por secciones.

---

## 10. CONCLUSIONES
### 10.1 Logros alcanzados
- Plataforma de gestión funcional con flujo completo de juego.
- Integración profesional entre motor, persistencia y GUI.
- Sistema de atracciones avanzado con cartera de proyectos realista.
- UX retro global limpia, consistente y configurable.
- Base técnica lista para evolución por fases.

### 10.2 Valoración personal
El proyecto consolida una arquitectura de escritorio robusta, donde la dificultad principal fue mantener coherencia entre crecimiento funcional y claridad visual. La refactorización de UX y la unificación de estilos aumentaron notablemente la mantenibilidad.

### 10.3 Impacto esperado
- Referencia sólida de proyecto manager desktop en Python.
- Base escalable para nuevas mecánicas de simulación.
- Entregable de portafolio técnico con valor académico y profesional.

---
Fecha: 2026 · Versión del documento: 1.0 · Autor: Luis Villegas Rivera
