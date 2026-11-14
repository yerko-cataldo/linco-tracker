# Changelog

## 2026-11-13
- Toda la app se reorganiza para que lo relacionado esté junto. Nutrición y Entreno tienen vistas como Finanzas: Nutrición → Hoy, Planificar, Cuerpo y metas, Mi base; Entreno → Hoy, Progreso, Ejercicios.
- El peso, la fase y las metas de nutrición y de peso quedan juntos en Nutrición → Cuerpo y metas. Las metas de entreno, bajo y estudio se editan en su pestaña; Perfil queda para tus datos, exportar y compartir.
- Los precios de tus alimentos pasan de Finanzas a Nutrición → Planificar, junto a la lista de compras.
- El Coach deja de ser una pestaña: se abre como panel lateral sobre cualquier pestaña, desde la navegación o un botón flotante.
- Métricas pasa a Perfil → Uso de la app.
- Finanzas se reorganiza en 5 vistas, cada una con una pregunta: Resumen (cómo voy), Plan (qué decidí), Análisis (en qué se va), Movimientos (los datos) y Ajustes. El mes se elige una vez, arriba, para todas. Antes eran 20 bloques en una sola página.
- Finanzas: "Tu plan del mes", una planilla con lo que entra, tus fijos, cuánto quieres gastar en cada categoría variable y cuánto ahorrar, con plan frente a real en cada línea, lo que queda sin asignar y lo que gastaste fuera del plan (con botón para sumarlo). Se escribe como en Excel: Enter baja de fila, la última fila de cada grupo agrega una línea y se pueden pegar filas desde Excel. Se puede armar solo con tus movimientos o partir con una plantilla. Con plan, el presupuesto y los topes salen de él.
- Finanzas: "Tu sueldo", el ciclo de pago a pago: cuánto te queda por día hasta el próximo sueldo, hasta qué día te alcanza a tu ritmo y, en los ciclos anteriores, cuánto sobró o qué día se acabó la plata.
- Finanzas: anotar rápido en una línea ("almuerzo 8.500", "uber 4.500 ayer", "sueldo 1.850.000") con categoría y tipo deducidos, y pegar varias filas desde Excel o tus notas con vista previa y aviso de duplicados. Los movimientos a mano ahora se editan, y la lista se descarga en CSV para Excel.
- Los montos aceptan "450 mil", "15 lucas", "8,5k" y "1,2M" en toda la app.
- El agente ve lo que entró en el rango y tu plan del mes.
- La cartola de la cuenta ahora importa el sueldo y los demás abonos (antes solo las transferencias de personas e instituciones, para las devoluciones). Las líneas de ingreso del plan sugieren el remitente que calza con su monto, y la fila de agregar entiende "Sueldo 2.200.000 el 25".

## 2026-11-09
- Nutrición: fases definición, recomposición, mantención, pausa de dieta y volumen limpio, en Perfil y metas → "Fase y metas de nutrición". Cada fase tiene un ritmo en % del peso por semana, ajustable dentro de un rango, y sus propias reglas de proteína y grasa. La recomposición pasa de −400 kcal a −0,1 % del peso por semana.
- La mantención se mide con tus datos (kcal registradas y tendencia de peso de 28 días) y solo usa la fórmula cuando faltan datos. Antes de cambiar de fase se ven las metas actuales y las nuevas lado a lado.
- Historial de metas: cada cambio queda guardado desde su fecha y cada día se evalúa con las metas que tenía (calendario, constancia, rango semanal, días en meta). El historial se ve en el panel de la fase, y el gráfico de peso marca cada fase con una banda de color.
- El ajuste de kcal usa solo los pesajes desde que empezó la fase, se puede aplicar con un botón y avisa si la meta de peso contradice la fase.
- El coach y el agente conocen la fase, su ritmo y el historial de metas.

## 2026-11-07
- Finanzas: transferencias recurrentes, semanales o mensuales (por ejemplo, el arriendo el 1 de cada mes), en la sección nueva del mismo nombre. Cada una tiene un monto aproximado (±10%) o un rango ("de $25.000 a $30.000"): cualquier monto dentro cuenta como hecha, sin cambiar nada a mano. El destinatario se reconoce por el RUT del comprobante o por el nombre, y el RUT y el banco se llenan solos con el último comprobante. Lo pagado unos días antes cuenta para el vencimiento (el arriendo del 29 vale para el 1). "Omitir esta vez" salta un periodo.
- Las transferencias se agregan y se editan en la misma sección, y la app sugiere las que ya se repiten en tu historial (mismo destinatario cada semana o cada mes), con su día y su rango de montos.
- Notificaciones push en el celular. Desde el vencimiento, a la hora elegida, llega un aviso diario mientras falte la transferencia, con el monto y la cuenta de destino. Cuando llega el correo "Hicimos la transferencia", otro aviso confirma que quedó registrada y si calza con el monto. Se activan por dispositivo; en iPhone, con la app agregada a la pantalla de inicio. La app ahora es instalable (manifest e íconos).
- Finanzas: categoría "Inversiones y ahorro" (grupo Ahorro e inversión), que no cuenta como gasto: no suma al gasto del mes, al presupuesto ni al calendario, y "Cómo vas" la muestra aparte. Fintual, Racional, fondos mutuos, depósitos a plazo y APV caen ahí solos.
- Finanzas: categorías propias. Se crean desde el selector de categoría de cualquier movimiento ("+ nueva categoría…") o en Presupuesto, topes y reglas → Tus categorías, con su grupo y si cuentan como gasto.
- Finanzas: movimientos a mano (efectivo, inversiones, otra tarjeta) desde Movimientos → "Agregar un movimiento a mano", con fecha, descripción, monto, tipo y categoría. Se pueden borrar.

## 2026-11-02
- Nutrición: los alimentos tienen versión cruda y cocida. Al registrar una compra de carne, pollo o pescado que no está en tu base (carne molida, pechuga cruda), se agregan las dos versiones con valores de referencia. "Agregar un alimento" busca solo los valores: del catálogo, o los estima la IA para que los revises. Si un alimento del armado de comida no está, se agrega desde ahí mismo.
- Precios de los alimentos: cada alimento tiene precio por kg con su fuente, desde tu última compra detallada (lo comprado crudo o seco se ajusta por la cocción) o, si nunca lo compraste, desde Unimarc (producto, precio, link y fecha de consulta). Costo de cada comida, del día, de las comidas frecuentes y de la lista de compras. Nuevo endpoint `/api/precio` y colección `prices`.
- Finanzas: rediseño. Arriba, cómo vas en el mes en una frase, lo que pide atención y lo que cuesta comer; el resto en secciones plegables. El detalle de una compra es una ventana con una tarjeta por producto.
- Secciones plegables en todas las pestañas, que recuerdan si quedaron abiertas en cada dispositivo.
- Entreno: drop sets. En la serie activa, "drop set" la marca como seguida de la anterior y propone el 75% de la carga; "+ drop set" agrega una al final de un ejercicio terminado. No cuentan para récords ni para la progresión, valen media serie efectiva por músculo y no suman descanso a la duración estimada.
- Entreno: superseries. "Superserie con el siguiente" junta dos o más ejercicios para alternarlos sin descanso entre ellos (etiquetas A1, A2…); la serie activa va alternando y la duración estimada cuenta 15 s de cambio dentro de la vuelta. La próxima sesión del mismo tipo las propone de nuevo, y "Pegar rutina" guarda como superserie los ejercicios escritos con "/".

## 2026-10-29
- Finanzas: tarjeta de débito. Cada tarjeta se reconoce por los últimos 4 dígitos de su alerta de Visa y se marca como crédito o débito en el nuevo panel Tarjetas (una sin tipo cuenta como crédito). El gasto del mes suma ambas; cada movimiento muestra su tarjeta, la lista tiene filtro por tipo y "Lo más importante" separa crédito y débito. El ciclo de facturación y las cuotas son solo de crédito. Si llega una compra con una tarjeta sin tipo, "Por revisar" lo avisa.
- Finanzas: "Importar cartola" (ahora en Tarjetas) acepta también la cartola de la cuenta BICE. Importa solo las compras con débito, con la fecha y hora de la compra, y las concilia con las alertas de débito; deja fuera transferencias, pagos de cuentas, el pago de la tarjeta e intereses. Avisa si los cargos no suman el total impreso.
- Finanzas: la cartola de la cuenta también importa transferencias a otras personas, pagos de cuentas por internet y cargos del banco, y suman al gasto del mes. El destinatario hace de comercio, así que su categoría se elige una vez en "Por revisar". Nuevas categorías: "Arriendo y gastos comunes" (en Casa), "Transferencias" y "Comisiones e intereses" (en Otros). El pago de la tarjeta de crédito, los abonos y las transferencias entre tus cuentas quedan fuera. El filtro de movimientos suma "Solo transferencias y pagos" y "Lo más importante" separa el gasto por medio de pago.
- Finanzas: devoluciones. La cartola de la cuenta importa las transferencias que recibes (de personas y de instituciones como la isapre, sin el sueldo ni tus propias cuentas). No suman hasta que eliges qué son: devolución de una compra (resta en su fecha, categoría y medio de pago, y la compra muestra "te devolvieron … tu parte …") o devolución en una categoría. Sugiere la compra de otros abonos de esos días ya marcados o la más grande de los 10 días anteriores.
- Finanzas: las transferencias llegan al momento. Los correos "Hicimos la transferencia" de BICE reenviados a la dirección de alertas crean el movimiento (destinatario, monto, fecha y hora) por revisar; al importar la cartola de la cuenta se unen a su fila sin duplicarse. Solo acepta reenvíos de los correos en `FORWARD_FROM` con DKIM y DMARC válidos, y descarta las transferencias a tus propias cuentas.
- Finanzas: corrige la conciliación de la cartola de crédito, que podía unir una fila con una alerta de débito del mismo monto y fecha.

## 2026-10-23
- Compartir con amigos: link de solo lectura sin login (`/s/<código>`), que se crea, cambia y desactiva en Perfil. Muestra solo las áreas marcadas (por defecto entreno, bajo y estudio; nutrición es opcional) y nunca peso, perfil, InBody ni coach. La constancia y el rango se calculan con las áreas compartidas. El Worker filtra los datos y la página va con `noindex`. Requiere una excepción Bypass en Cloudflare Access para `/s`.
- Entreno: los calentamientos de gimnasio asumen que llegas en bici. Sale el cardio de 5 min y quedan movilidad dinámica y series de aproximación (~4 min), con una nota para sumar cardio si demoras más de 15 min en empezar.
- Entreno: calentamiento sugerido para cada tipo de sesión, en una línea plegable que aparece antes de la primera serie. Son 4 a 8 minutos de movilidad y activación y, en las sesiones de gimnasio, series de aproximación del primer ejercicio.
- Entreno: los ejercicios pendientes se proponen en orden ideal: multiarticulares, aislamiento de músculos grandes, aislamiento de músculos chicos y core al final. Dentro de cada grupo se mantiene el orden habitual, y arrastrar sigue mandando.
- Core: la rutina base es solo con colchoneta: elevación de piernas, crunch inverso, plancha, plancha lateral y bicho muerto. Sale la rueda abdominal.
- Entreno: ilustraciones para 28 ejercicios, antes 7. Cubren las rutinas base de Push, Pull, Legs, Full body y Core: press banca, press inclinado con mancuernas, press militar, elevaciones laterales, extensión de tríceps, jalón en máquina, remo en polea, sentadilla, sentadilla hack, extensión de cuádriceps, peso muerto rumano, curl femoral (acostado y sentado), elevación de talones, aductores, abductores, elevación de piernas, rueda abdominal, plancha, plancha lateral y bicho muerto.
- Entreno: los ejercicios de tiempo (plancha, plancha lateral) parten en 30 s en vez de 10 la primera vez.
- Entreno: nuevo tipo de sesión "Core" (abdominales). Rutina base para hacer en casa: crunch inverso, elevación de piernas, rueda abdominal, plancha lateral y bicho muerto. Los ejercicios de abdomen y oblicuos quedan como Core en el catálogo, su descanso estimado es de 60–90 s y la plancha lateral cuenta sus reps como segundos. "Pegar rutina" reconoce "core" o "abs" después de la fecha, y los abdominales al final de otra sesión no cambian su tipo.
- Entreno: los ejercicios terminados también se reordenan con el ícono ⠿ (o las flechas), entre sí, incluso con el entreno cerrado o en días anteriores. El orden queda guardado y es el que se propone la próxima vez.
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
