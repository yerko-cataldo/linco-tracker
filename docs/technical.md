# Detalles técnicos

El contexto general del proyecto (stack, modelo de datos, API y principios) está en `CLAUDE.md`. Este archivo documenta piezas puntuales.

## Entreno

### Checklist del día
- Al elegir Push, Pull, Legs o Full body se cargan los ejercicios habituales del tipo: los de las últimas 3 sesiones de ese tipo, ordenados por su posición promedio. Sin historial, se usa `DEFAULT_ROUTINE`.
- Cada ejercicio parte con las series de su última sesión. Si en todas las series a la carga más alta hubo 12 reps o más, la carga sube (2,5 kg bajo 40 kg, 5 kg desde 40 kg, 5 o 10 lb, o un nivel) y las reps bajan a 8. Si ninguna llegó a 6, la carga baja cerca de un 10% (`nextStep()`).
- Al marcar una serie se guarda con `t` (marca de tiempo). El descanso de la serie anterior se calcula como el intervalo entre ambas marcas menos 30 s (`SET_SEC`), con tope de 10 min.
- Duración de la sesión (`sessionMin()`, vía `gymDur()`): se estima desde las series, no se mide. Cada serie dura 15 s de preparación (`SET_PREP_SEC`) más 3 s por repetición (`REP_SEC`); en los ejercicios isométricos (`ISO_EX`, hoy la plancha) las reps son segundos. Entre dos series se suma el descanso medido acotado a 2–3 min (`REST_LO`, `REST_HI`), o 2 min 30 s si no se midió; después de la última serie no se suma descanso. Se calcula al leer, así que vale para todos los días con series, también los anteriores. `act.gymMin` solo se usa en días sin series (registro manual o rápido; sin valor, 40 min). En días con series, un valor escrito en "Minutos" se guarda en `act.gymMinManual` y reemplaza al estimado; borrarlo vuelve al estimado.
- El cronómetro cuenta desde la última serie marcada, sin límite, sonido ni vibración. Al recargar la página dentro de 30 min, retoma desde esa serie.
- Orden de la lista: primero los ejercicios con series, en el orden en que se hicieron; después los pendientes, en el orden habitual o en el que se eligió arrastrando el ícono ⠿ (o con las flechas del teclado sobre él). Como `habitual()` lee el orden de ejecución, el orden en que entrenas hoy es el que se propone la próxima vez.
- "Terminar entreno" guarda `act.end` (marca de tiempo) y detiene el cronómetro. Un entreno cerrado (`wEnded()`: con series y `act.end`, o de un día anterior) muestra solo los ejercicios hechos y un resumen; "Retomar entreno" borra `act.end` y vuelve a cargar los pendientes.
- Lo que no se guarda (ediciones de carga sin marcar, series agregadas o quitadas, ejercicios ocultos, el orden de los pendientes y "Retomar entreno" en un día anterior) vive en el objeto `W` y se pierde al recargar.

### Lectura de notas (`parseRoutine()`)
- Una fecha ambigua con reps ("15/10") cuenta como fecha solo si es posterior a la sesión en curso y de los últimos 60 días. Si no, se lee como reps.
- Dos bloques con la misma fecha se juntan en una sola sesión.
- "Ejercicio carga×reps" en la misma línea se separa en nombre y serie. Las líneas con forma de serie que no se entienden quedan en "No entendí estas líneas".

### Nombres de ejercicios
- `exInfo()` busca coincidencia exacta con el nombre o un alias del catálogo. Si no la hay, busca un prefijo, pero solo cuando las palabras restantes están en `EX_DESC` ("máquina", "polea", "con", "una mano"…).

## Ilustraciones de ejercicios
- Estilo silueta: figura plana de perfil armada desde articulaciones (hombro, codo, muñeca, cadera, rodilla, tobillo), con cinemática inversa para codo y rodilla, volumen por formas redondeadas y el músculo trabajado en `--act`.
- Fuente: `tools/ilustraciones/silueta_lib.py` (figura, aparatos y colores) y un `pose_*.py` por ejercicio.
- Para regenerar: `py tools/ilustraciones/build.py`. El script reemplaza el objeto `ILLU` de `public/index.html` entre `/* ILLU:inicio */` y `/* ILLU:fin */`.
- Los colores son clases (`.b`, `.m`, `.mk`…) definidas en el CSS de la app con sus tokens, así que funcionan en modo claro y oscuro.
