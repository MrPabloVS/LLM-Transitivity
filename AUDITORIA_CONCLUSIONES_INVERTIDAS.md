# Auditoría de conclusiones invertidas

Generada: 2026-11-04T13:28:12-03:00.

Encontramos **4.500 registros etiquetados como válidos que son inválidos bajo implicación material proposicional**, repartidos en nueve datasets de 1.500 casos (500 por dataset). Son los registros 1001–1500 de cada archivo, etiquetados como no canónicos. También hay **una copia adicional** de un caso afectado en el dataset de prueba de tres preguntas: 4.501 entradas afectadas contando esa copia.

Los registros se cuentan desde 1 dentro del array JSON; no son números de línea ni el ID compartido por las variantes. Se preservaron todos los prompts, etiquetas y resultados originales. No se hicieron llamadas a la API.

## Ubicaciones

| Archivo | Casos revisados | Afectados | Registros afectados | Líneas afectadas |
| --- | ---: | ---: | --- | --- |
| [HS_HF_FU_500.json](prompts/userPrompts/HS_HF_FU_500.json) | 1500 | 500 | 1001–1500 | 1002–1501 |
| [HS_HF_PA_500.json](prompts/userPrompts/HS_HF_PA_500.json) | 1500 | 500 | 1001–1500 | 1002–1501 |
| [HS_HF_PR_500.json](prompts/userPrompts/HS_HF_PR_500.json) | 1500 | 500 | 1001–1500 | 1002–1501 |
| [HS_LF_FU_500.json](prompts/userPrompts/HS_LF_FU_500.json) | 1500 | 500 | 1001–1500 | 1002–1501 |
| [HS_LF_PA_500.json](prompts/userPrompts/HS_LF_PA_500.json) | 1500 | 500 | 1001–1500 | 1002–1501 |
| [HS_LF_PR.json](prompts/userPrompts/HS_LF_PR.json) | 1500 | 500 | 1001–1500 | 1002–1501 |
| [HS_NS_FU_500.json](prompts/userPrompts/HS_NS_FU_500.json) | 1500 | 500 | 1001–1500 | 1002–1501 |
| [HS_NS_PA_500.json](prompts/userPrompts/HS_NS_PA_500.json) | 1500 | 500 | 1001–1500 | 1002–1501 |
| [HS_NS_PR_500.json](prompts/userPrompts/HS_NS_PR_500.json) | 1500 | 500 | 1001–1500 | 1002–1501 |

Prueba adicional: `HS_HF_PR_smoke_20261104_123831.json`, 3 casos revisados; afectado el registro 3, que empieza en la línea 54. Es una copia del dataset HF presente y no aumenta el total de 4.500 del conjunto principal.

## Qué se comprobó

Se revisaron 13.500 registros de los nueve datasets grandes y los tres registros de la prueba corta. Se extrajeron las dos premisas y la conclusión de la plantilla inglesa `if … then …, if … then … therefore if … then …`. Cada cláusula completa se trató como una proposición atómica independiente. Se enumeraron todas las asignaciones de verdad: un argumento es inválido si alguna hace verdaderas ambas premisas y falsa la conclusión. Las etiquetas `valid` y `valido` se interpretaron como válidas.

Además de comprobar esa discrepancia, se confirmó que todos los registros afectados tienen premisas `B → C` y `A → B`, conclusión `C → A` y etiqueta válida/no canónica. El contraejemplo `A = falso`, `B = falso`, `C = verdadero` satisface ambas premisas y refuta la conclusión. En los nueve datasets grandes, cada caso tiene un registro equivalente etiquetado `invalid`, con las mismas premisas en otro orden y exactamente la misma conclusión. El CSV identifica ese registro y su línea.

No se encontraron otras discrepancias de validez en los 13.503 casos de esta plantilla revisados. Esta auditoría se limita a la interpretación proposicional indicada: no evalúa relaciones semánticas adicionales entre las cláusulas.

## Ejemplo exacto en inglés

Archivo: `prompts/userPrompts/HS_HF_PR_500.json`. Se agregan saltos de línea entre premisas y conclusión para facilitar la lectura; el CSV conserva el texto original completo.

**Registro 501, línea 502 — etiqueta original: `invalid`, `canonic`.**

> If the man loses the money then the student sees the car.  
> If the student sees the car then the family loves the school.  
> Therefore, if the family loves the school then the man loses the money.

**Registro 1001, línea 1002 — etiqueta original: `valid`, `non-canonic`.**

> If the student sees the car then the family loves the school.  
> If the man loses the money then the student sees the car.  
> Therefore, if the family loves the school then the man loses the money.

Los dos argumentos tienen la misma validez: solo se permutan las premisas. Lo inconsistente es asignarles etiquetas de validez opuestas. Si se pretendía una variante válida no canónica, su conclusión debería ser:

> Therefore, if the man loses the money then the family loves the school.

## Listado completo y alcance

[Descargar el listado de 4.501 entradas afectadas](summaries/conclusiones_invertidas.csv). Incluye archivo, registro, línea inicial, ID, etiquetas originales, validez auditada, texto completo en inglés, asignación A/B/C, contraejemplo, registro equivalente etiquetado inválido y SHA-256 del archivo fuente.

Los siguientes archivos fueron inspeccionados pero quedan fuera de esta auditoría porque no tienen el formato de ocho campos de los datasets grandes:

- `Csf.json`: 1 registros sin auditar semánticamente.
- `Csf2.json`: 1 registros sin auditar semánticamente.
- `HS_test.json`: 72 registros sin auditar semánticamente.

## Consecuencia para el análisis

Las respuestas `no` a estos 500 casos por dataset son correctas según esta interpretación lógica, aunque no coincidan con la etiqueta original. Deben distinguirse ambas métricas. Las corridas actuales no contienen la condición pretendida de argumentos válidos con premisas permutadas. Cambiar solo las etiquetas permitiría evaluar el material existente, pero no recuperaría esa condición experimental. Para medirla hace falta corregir las conclusiones en una nueva versión del dataset y acordar una nueva ejecución; esta auditoría no modifica ni relanza nada.
