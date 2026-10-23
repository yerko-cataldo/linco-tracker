# Changelog

## 2026-10-23
- Entreno: el campo Minutos vuelve a ser editable en días con series. Si escribes los minutos, reemplazan al estimado; si lo borras, vuelve al estimado. La actividad del día se guarda al cambiar un campo o con Enter, sin depender del botón.
- Catálogo: "Jalón al pecho" se separa en "Jalón al pecho en máquina" y "Jalón al pecho con polea". Las series anteriores registradas como "Jalón al pecho" quedan como máquina; la ilustración y la rutina habitual de Pull pasan a la de polea.

## 2026-10-22
- Entreno: botón "Terminar entreno". Guarda la marca de cierre, detiene el cronómetro, quita los ejercicios que no se hicieron y deja un resumen (ejercicios, series, duración, récords). "Retomar entreno" lo reabre. Los días anteriores con series se muestran cerrados.
- Entreno: los ejercicios pendientes se reordenan arrastrando el ícono ⠿ (o con las flechas del teclado). Los ejercicios con series suben y quedan en el orden en que se hicieron.
- Entreno: la duración del gimnasio se estima desde las series (15 s de preparación más 3 s por repetición, y descansos de 2 a 3 min entre series) en vez de medirse entre la primera y la última serie marcada. Aplica también a los días anteriores. "Pegar rutina" muestra la duración estimada y el campo Minutos queda calculado cuando hay series.

## 2026-10-16
- Entreno: checklist "Entrenar hoy". Al elegir Push, Pull, Legs o Full body carga los ejercicios habituales con la carga propuesta (doble progresión). Se marca cada serie con un toque, se ajusta con − / +, se pueden quitar series y ejercicios, y "Terminar ejercicio" lo cierra sin hacer todas las series.
- Entreno: cronómetro desde la última serie, sin límite ni alarma. El descanso y la duración de la sesión se calculan solos.
- Entreno: mapa muscular de la semana (frente y espalda), progreso por ejercicio con gráfico e historial de sesiones con récords.
- Entreno: catálogo de 94 ejercicios con músculos principales y secundarios, nota de enfoque, búsqueda y filtros por grupo.
- Entreno: ilustraciones en silueta para los ejercicios habituales de Pull, generadas con `tools/ilustraciones/`.
- Entreno: "Pegar rutina desde tus notas" convierte texto libre (fecha, ejercicio, series, niveles, pares "a/b" y descansos) en series, con vista previa.
- Series con unidad (kg, lb o nivel), descanso y marca de tiempo; detección de series de aproximación.
- Récords: solo cuenta la mejor serie del día, comparada con las sesiones anteriores.
