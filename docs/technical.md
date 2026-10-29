# Detalles técnicos

El contexto general del proyecto (stack, modelo de datos, API y principios) está en `CLAUDE.md`. Este archivo documenta piezas puntuales.

## Entreno

### Checklist del día
- Al elegir Push, Pull, Legs, Full body o Core se cargan los ejercicios habituales del tipo: los de las últimas 3 sesiones de ese tipo, ordenados por su posición promedio. Sin historial, se usa `DEFAULT_ROUTINE`.
- Cada ejercicio parte con las series de su última sesión. Si en todas las series a la carga más alta hubo 12 reps o más, la carga sube (2,5 kg bajo 40 kg, 5 kg desde 40 kg, 5 o 10 lb, o un nivel) y las reps bajan a 8. Si ninguna llegó a 6, la carga baja cerca de un 10% (`nextStep()`).
- Al marcar una serie se guarda con `t` (marca de tiempo). El descanso de la serie anterior se calcula como el intervalo entre ambas marcas menos 30 s (`SET_SEC`), con tope de 10 min.
- Duración de la sesión (`sessionMin()`, vía `gymDur()`): se estima desde las series, no se mide. Cada serie dura 15 s de preparación (`SET_PREP_SEC`) más 3 s por repetición (`REP_SEC`); en los ejercicios isométricos (`ISO_EX`, hoy la plancha y la plancha lateral) las reps son segundos. Entre dos series se suma el descanso medido acotado a 2–3 min (`REST_LO`, `REST_HI`), o 2 min 30 s si no se midió; en los ejercicios de core (`t: "core"` en `EX_CAT`) el rango es 60–90 s (`CORE_REST_LO`, `CORE_REST_HI`), o 75 s; después de la última serie no se suma descanso. Se calcula al leer, así que vale para todos los días con series, también los anteriores. `act.gymMin` solo se usa en días sin series (registro manual o rápido; sin valor, 40 min). En días con series, un valor escrito en "Minutos" se guarda en `act.gymMinManual` y reemplaza al estimado; borrarlo vuelve al estimado.
- El cronómetro cuenta desde la última serie marcada, sin límite, sonido ni vibración. Al recargar la página dentro de 30 min, retoma desde esa serie.
- Orden de la lista: primero los ejercicios con series, en el orden en que se hicieron o en el que se eligió arrastrándolos (eso reordena sus series guardadas en `act.sets`, también en días anteriores o con el entreno terminado); después los pendientes en orden ideal (`exTier()`): 0 multiarticulares (al menos dos de cuádriceps, glúteo e isquios, o un músculo del tronco con bíceps o tríceps), 1 aislamiento de músculos grandes, 2 aislamiento de músculos chicos y 3 core; `EX_ISO` corrige los que mueven una sola articulación aunque sus músculos sugieran otra cosa. Dentro de cada grupo se respeta el orden habitual, y si arrastras el ícono ⠿ (o usas las flechas del teclado sobre él) manda tu orden. Como `habitual()` lee el orden de ejecución, el orden en que entrenas hoy pesa en lo que se propone la próxima vez, pero solo dentro de cada grupo.
- Calentamiento (`WARMUP`): una línea plegable al inicio del entreno, solo antes de la primera serie y con el entreno abierto. Muestra 3 a 5 pasos fijos por tipo de sesión. Las de gimnasio (`bike: true`) asumen que llegas en bici con el cuerpo caliente: solo movilidad dinámica y series de aproximación del primer ejercicio, sin estiramiento estático, con una nota para sumar 5 min de cardio si pasan más de 15 min antes de empezar. Que esté abierta o cerrada se recuerda en `W.warmOpen` mientras la página esté abierta.
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
- Vistas: casi todas de perfil. Las que no se leen de perfil (elevaciones laterales, aductores, abductores y plancha lateral) van de frente y arman la figura en su propio `pose_*.py` con las mismas primitivas y clases. Algunas reutilizan piezas de otras: `dumbbell` de `pose_martillo.py`, `abs_overlay` de `pose_crunchinv.py` y `front_seated` de `pose_aductores.py`.
- Para revisar un dibujo, cada `pose_*.py` tiene `draw()`; renderiza el SVG en un HTML con el `CSS` de `silueta_lib.py` y míralo también a 72 px, que es su tamaño en la app.
- Para regenerar: `py tools/ilustraciones/build.py`. El script reemplaza el objeto `ILLU` de `public/index.html` entre `/* ILLU:inicio */` y `/* ILLU:fin */`.
- Los colores son clases (`.b`, `.m`, `.mk`…) definidas en el CSS de la app con sus tokens, así que funcionan en modo claro y oscuro.

## Finanzas

### Tarjetas
- Cada movimiento trae los últimos 4 dígitos de la tarjeta (`movimientos.tarjeta`) desde la alerta de Visa. El tipo y el nombre de cada tarjeta se guardan en `lib.fin.cards` (`{últimos 4: {name, kind: "credito" | "debito"}}`) y se editan en Finanzas → Tarjetas.
- Medio de pago de un movimiento (`finCardKind()`): una compra de la cartola de la cuenta (`banco_id` con prefijo `bicecta:`) es de débito, cualquier otra fila de la cuenta es `cuenta` (transferencias y pagos) y una fila de la cartola de crédito (`bice:`) es de crédito; una alerta toma el tipo de su tarjeta y, sin tipo, cuenta como crédito. Así una tarjeta de crédito que nunca se configuró sigue funcionando igual que antes.
- Gasto (`isPurchase()`, `FIN_SPEND`): compras con tarjeta en pesos, más transferencias, pagos de cuentas y cargos del banco de la cuenta. El gasto del mes, las categorías, el presupuesto y los recurrentes suman todo eso. El ciclo de facturación y las cuotas usan solo las tarjetas de crédito.
- `importCartola()` en el Worker reconoce el formato (`parseCartola()` para la tarjeta de crédito, `parseCuenta()` para la cuenta) y lee `lib.fin.cards`: la cartola de crédito se concilia solo con alertas de tarjetas que no son de débito, y la de la cuenta solo con alertas de débito. Sin esa separación, una compra con débito del mismo monto y fecha que una de crédito podía quedar unida a la fila equivocada.

### Cartola de la cuenta (`parseCuenta()`)
- CSV de BICE "Abonos y cargos" de la cuenta en pesos: columnas Fecha (`29 oct 2026`), Categoría (Abonos o Cargos), Descripción y Monto (`$2.190`), con una columna vacía a la izquierda. El periodo sale de la línea `29 oct 2026 - 1 oct 2026` y el total de cargos, de la línea siguiente a "Total cargos".
- Cada cargo se lee con `cuentaCargo()`; la fecha y hora salen de la descripción, porque la fecha de la fila es la del cargo en la cuenta (hasta 3 días después de la compra):
  1. "Cargo por Compra en COMERCIO El dd/mm/aaaa a las hh:mm:ss., Monto N" → `Compra` (débito), conciliable con alertas.
  2. "Transferencia de … Rut A desde … a DESTINATARIO Rut B a …, el aaaa-mm-dd a las hh:mm hrs." → `Transferencia`, con el destinatario como comercio. Si A = B (otra cuenta propia) se omite.
  3. "Cargo por pago SERVICIO vía internet …" → `Pago de cuenta`, con el servicio como comercio (sin el código "Portal EXP…").
  4. "Cargo Impuesto/Intereses/Comisión/Mantención …" → `Cargo del banco`.
  5. "Cargo por abono/pago de tarjeta de crédito …" → se omite: sus compras ya están en la cartola de crédito y contarlo sería doble.
- Los abonos y los cargos omitidos cuentan en `omitidos`; un cargo que no calza con ninguna forma va a `desconocidos` (se muestran en Tarjetas tras importar) y no entra.
- Transferencias, pagos y cargos del banco entran sin tarjeta y con `revisado = 0`, para elegir su categoría en "Por revisar". Una transferencia sin categoría propia, regla ni regla base va a "Transferencias". Las reglas base nuevas mandan "edificio", "condominio", "comunidad", "administración", "gastos comunes" y "arriendo" a "Arriendo y gastos comunes"; "sobregiro", "intereses", "comisión" y "mantención" a "Comisiones e intereses"; "cuentas de servicio" a "Servicios".
- Los abonos (por ejemplo, amigos que te devuelven su parte de una cuenta) no se importan ni se descuentan del gasto.
- `cuadra` compara la suma de todas las filas de cargos (no solo las compras) con el total de cargos impreso; sirve para detectar filas que el lector no entendió.
- La clave de cada fila (`banco_id`) es `bicecta:<descripción>|<monto>#<n>`, sin la fecha de la fila, para que una cartola provisoria y la definitiva del mismo periodo no dupliquen compras.
- Las compras nuevas llevan la tarjeta de débito si hay una sola configurada.
- Aviso "no aparece en la cartola" para una alerta de débito: su fecha está entre `lib.fin.cuentaDesde` y 5 días antes de `lib.fin.cuentaHasta` (el periodo cubierto por las cartolas de la cuenta importadas) y no se unió a ninguna fila. Los 5 días cubren el desfase entre la compra y el cargo. Para crédito sigue la regla de 3 días después de la última importación (`cartolaAl`).
- El filtro por tarjeta de la lista de movimientos y la tarjeta de cada movimiento se muestran solo cuando hay más de una tarjeta.
