# BBDD consolidada de alimentos (eCook + alimentos reales)

Versión: 04-10-2026 · Fuentes: fichas nutricionales ecook.cl (compra semana 21-09-2026, consultadas 28-09-2026) + tabla propia de alimentos reales.

## Convenciones del esquema

- **Decimales con punto.** Celda vacía = dato no disponible (no se asume 0).
- **Divisor + Unidad** = cantidad a la que se refieren los macros de esa fila. Para escalar: `macro_consumido = macro_fila × (cantidad_consumida / Divisor)`.
- **Base**: `envase` = valores del envase completo comprado (eCook). `100g` = por 100 g. `unidad` = por unidad / lámina / scoop.
- **Estado**: crudo / cocido / preparado (según la fuente). Importa al pesar: no mezclar gramos crudos con valores de cocido.
- **G_sat, Fibra, Sodio_mg, Stock_inicial, Semáforo** solo existen para eCook; en alimentos reales quedan vacíos.
- **Semáforo** (solo eCook): Rojo = grasa >35 g o saturada >15 g por envase (máx 1/semana o ½ envase). Amarillo = sodio >1.500 mg.

## Tabla

| ID | Alimento | Origen | Estado | Base | Divisor | Unidad | Kcal | P | C | G | G_sat | Fibra | Sodio_mg | Stock_inicial | Semáforo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| eco_01 | Lentejas con longaniza | eCook | preparado | envase | 400 | g | 528 | 31.8 | 69.8 | 15.0 | 4.8 | 11.9 | 1640 | 3 | Amarillo (sodio) |
| eco_02 | Porotos con longaniza | eCook | preparado | envase | 400 | g | 446 | 29.9 | 33.2 | 21.5 | 6.1 | 24.9 | 1166 | 3 | Verde |
| eco_03 | Lasagna bolognesa individual | eCook | preparado | envase | 375 | g | 764 | 48.9 | 25.9 | 52.0 | 25.5 | 0.8 | 2201 | 2 | Rojo |
| eco_04 | Strogonoff de pollo | eCook | preparado | envase | 210 | g | 275 | 39.2 | 6.8 | 10.3 | 4.5 | 0.5 | 914 | 5 | Verde |
| eco_05 | Pollo a la mostaza (miel) | eCook | preparado | envase | 200 | g | 286 | 38.5 | 14.6 | 8.4 | 2.9 | 0 | 866 | 5 | Verde |
| eco_06 | Beef bourguignon | eCook | preparado | envase | 180 | g | 710 | 49.1 | 7.0 | 50.3 | 21.0 | 0.6 | 536 | 0 | Rojo |
| eco_07 | Cerdo al jugo | eCook | preparado | envase | 200 | g | 374 | 38.3 | 6.2 | 20.7 | 2.4 | 1.1 | 663 | 4 | Verde |
| eco_08 | Mechada al jugo | eCook | preparado | envase | 175 | g | 709 | 53.3 | 3.0 | 54.3 | 22.0 | 0.6 | 507 | 2 | Rojo |
| eco_09 | Mechada al vino tinto | eCook | preparado | envase | 175 | g | 767 | 53.1 | 5.5 | 54.8 | 23.0 | 0 | 608 | 4 | Rojo |
| eco_10 | Pulled pork BBQ | eCook | preparado | envase | 200 | g | 587 | 38.2 | 23.0 | 37.6 | 13.0 | 0 | 1705 | 5 | Rojo |
| eco_11 | Strogonoff de vacuno | eCook | preparado | envase | 180 | g | 771 | 54.3 | 4.8 | 60.2 | 25.4 | 0.5 | 650 | 5 | Rojo |
| eco_12 | Salmón al eneldo | eCook | preparado | envase | 170 | g | 351 | 38.8 | 1.1 | 21.4 | 3.1 | 0.2 | 83 | 6 | Verde |
| rea_01 | Posta rosada | Real | crudo | 100g | 100 | g | 130 | 21 | 0 | 4 | | | | | |
| rea_02 | Lomo liso | Real | crudo | 100g | 100 | g | 190 | 22 | 0 | 11 | | | | | |
| rea_03 | Asiento | Real | crudo | 100g | 100 | g | 150 | 21 | 0 | 7 | | | | | |
| rea_04 | Pechuga de pollo | Real | cocido | 100g | 100 | g | 165 | 31 | 0 | 3.6 | | | | | |
| rea_05 | Chuleta de cerdo | Real | cocido | 100g | 100 | g | 230 | 24 | 0 | 14 | | | | | |
| rea_06 | Arroz blanco | Real | cocido | 100g | 100 | g | 130 | 2.7 | 28 | 0.3 | | | | | |
| rea_07 | Fideos | Real | cocido | 100g | 100 | g | 138 | 4.5 | 26 | 1 | | | | | |
| rea_08 | Brócoli al vapor | Real | cocido | 100g | 100 | g | 34 | 2.8 | 6.6 | 0.4 | | | | | |
| rea_09 | Tomate fresco | Real | crudo | 100g | 100 | g | 18 | 0.9 | 3.9 | 0.2 | | | | | |
| rea_10 | Palta | Real | crudo | 100g | 100 | g | 160 | 2 | 9 | 15 | | | | | |
| rea_11 | Frutos secos mixtos | Real | crudo | 100g | 100 | g | 600 | 20 | 20 | 50 | | | | | |
| rea_12 | Aceite de oliva | Real | crudo | 100g | 100 | g | 884 | 0 | 0 | 100 | | | | | |
| rea_13 | Avena integral | Real | crudo | 100g | 100 | g | 389 | 17 | 66 | 7 | | | | | |
| rea_14 | Yogur Griego Protein Quillayes | Real | preparado | 100g | 100 | g | 74 | 9.5 | 3.5 | 2.5 | | | | | |
| rea_15 | Leche s/lactosa | Real | preparado | 100g | 100 | g | 60 | 3 | 4.7 | 0.5 | | | | | |
| rea_16 | Huevo duro | Real | cocido | unidad | 1 | unidad | 78 | 6.5 | 0.5 | 5.5 | | | | | |
| rea_17 | Huevo revuelto c/aceite | Real | cocido | unidad | 1 | unidad | 85 | 6.5 | 0.5 | 6.5 | | | | | |
| rea_18 | Pan hallulla | Real | preparado | unidad | 1 | unidad | 250 | 6.5 | 40 | 6.5 | | | | | |
| rea_19 | Plátano (mediano) | Real | crudo | unidad | 1 | unidad | 105 | 1.3 | 27 | 0.4 | | | | | |
| rea_20 | Jamón de pavo (lámina) | Real | preparado | unidad | 1 | lámina | 15 | 2.6 | 0.4 | 0.3 | | | | | |
| rea_21 | Creatina (scoop 5 g) | Real | crudo | unidad | 1 | scoop | 0 | 0 | 0 | 0 | | | | | |
| rea_22 | Miel de abeja | Real | crudo | 100g | 100 | g | 304 | 0 | 82 | 0 | | | | | |
| rea_23 | Mantequilla de maní | Real | preparado | 100g | 100 | g | 590 | 25 | 20 | 50 | | | | | |
| rea_24 | Arándanos | Real | crudo | 100g | 100 | g | 57 | 1 | 15 | 0.3 | | | | | |
| rea_25 | Lechuga | Real | crudo | 100g | 100 | g | 15 | 1 | 3 | 0.2 | | | | | |
| rea_26 | Queso rallado | Real | preparado | 100g | 100 | g | 466 | 49 | 0 | 30.1 | | | | | |

## Cambios al consolidar

1. **Creatina estaba duplicada**: la segunda fila tenía divisor 0 (rompe cualquier escalado `/Divisor`) y una columna corrida (4 valores en vez de 5). Dejé una sola fila: scoop de 5 g.
2. Comas decimales pasadas a punto (3,6 → 3.6).
3. Los macros de eCook se mantienen **por envase completo**, tal como en la BBDD original; no los normalicé a 100 g para no alterar la fuente.
4. La columna **Estado** es nueva (la inferí del nombre original: "cruda", "cocida", "al vapor", "duro"). En los ítems sin indicación (p. ej. avena, miel, queso, yogur) puse crudo/preparado según tipo de producto; revísala si la vas a usar para algo fino.

## Valores a revisar (consistencia Atwater, 4-4-9)

- **Leche s/lactosa**: 3 P + 4.7 C + 0.5 G ≈ 35 kcal, pero declara 60. Lo esperable para 60 kcal sería ~3 g de grasa (leche entera); probable error en G.
- **Palta**: macros dan ~179 kcal vs 160 declaradas (~12 % de diferencia; en parte es fibra, pero conviene confirmar).
- **Queso rallado**: 49 g de proteína/100 g es alto incluso para un queso duro madurado (parmesano ronda 36–38 g). Verifica contra la etiqueta del producto que usas.
- Brócoli, arándanos, plátano y mantequilla de maní difieren 8–20 % por fibra/redondeo; aceptable.

Si me confirmas los valores corregidos de leche, palta y queso, actualizo la tabla. También puedo exportarla a CSV o al Excel `BBDD_eCook_plan.xlsx` si el otro proyecto lo prefiere.
