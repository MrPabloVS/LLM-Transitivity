# Estado y pendientes — 2026-11-04

Completado el procesamiento de todos los presentes: `HS_HF_PR_500`, `HS_LF_PR` y `HS_NS_PR_500`, con `zeroShot` y los tres IDs de modelo acordados. Hay 13.500 registros verificados: 13.493 respuestas de texto y 7 filtros del proveedor en Claude/LF. Se reutilizaron 211 resultados históricos de GPT/LF. No quedan filas sin registrar dentro de este alcance.

Los comandos exactos, fases, horas con zona, logs, errores y reanudaciones están en [CORRIDAS.md](CORRIDAS.md). Los seis procesos LF/NS se lanzaron en paralelo con un límite de 10 llamadas por proceso; la recuperación de Claude se hizo con dos por proceso.

## Resultados registrados

La coincidencia se calcula contra las etiquetas originales y con el normalizador estricto `strip().lower().rstrip(".")`. Los textos explicativos y los filtros no cuentan como coincidencias; eso no implica una evaluación semántica negativa de las explicaciones.

| Dataset | Modelo | Texto / filtrados | Coincidencias con etiquetas | Costo nuevo registrado USD |
| --- | --- | --- | --- | --- |
| `HS_HF_PR_500` | GPT-4o mini | 1500 / 0 | 1016/1.500 | 0.0152304 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | 1500 / 0 | 1000/1.500 | 0.1218963435 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | 1500 / 0 | 286/1.500 | 3.708729 |
| `HS_LF_PR` | GPT-4o mini | 1500 / 0 | 1106/1.500 | 0.017592 |
| `HS_LF_PR` | DeepSeek v4.1 flash | 1500 / 0 | 1000/1.500 | 0.1583320744 |
| `HS_LF_PR` | Claude Sonnet 4.5 | 1493 / 7 | 4/1.500 | 5.561514 |
| `HS_NS_PR_500` | GPT-4o mini | 1500 / 0 | 986/1.500 | 0.0215169 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | 1500 / 0 | 1000/1.500 | 0.1496106357 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | 1500 / 0 | 66/1.500 | 4.896636 |

Total nuevo registrado: **USD 14.6510573536**. La prueba inicial de tres casos (USD 0,00003045) y los logs históricos de GPT/LF (USD 0,0036459) están separados. No se registraron todos los intentos fallidos/interrumpidos, por lo que el total no sustituye el estado de cuenta de OpenRouter.

Los archivos `summaries/<dataset>_zeroShot.json` contienen conteos por variante, respuestas no reconocidas, filtros, costos y tokens desglosados por log. `summaries/<dataset>_label_audit.json` conserva la auditoría por fila y `summaries/HS_LF_PR_legacy_migration.json` documenta las 211 copias históricas.

## Hallazgos que limitan la evaluación

- **Etiquetas:** en cada dataset, las 500 filas etiquetadas como válidas no canónicas son inválidas bajo implicación material: `Q → R`, `P → Q`, por tanto `R → P`. Las tablas de verdad auditaron las 4.500 filas de origen y encontraron 1.500 etiquetas discrepantes en total. No se modificaron los prompts ni las etiquetas.
- **Formato de Claude:** 1.178 textos HF, 1.489 LF y 1.434 NS contienen algo distinto de la respuesta normalizada `yes`/`no`. Hay además 7 filtros en LF. El evaluador estricto no interpreta esas explicaciones, por lo que sus porcentajes no miden por sí solos la capacidad lógica.
- **Filtros:** filas LF 131, 148, 407, 631, 648, 725 y 1054. Se conservó la respuesta API `content_filter`, con texto nulo y trazabilidad al error. No se deben volver a consultar automáticamente ni tratar como un `no`.
- **Reutilización:** GPT/LF combina 211 resultados históricos con 1.289 nuevos; no es una repetición independiente realizada en una única fecha.
- **HTTP 402:** se recuperaron los 43 casos afectados reduciendo concurrencia. La clave aún tenía saldo y no se confirmó la causa exacta del error.

## Cambios realizados

- Dependencias y lockfile con `uv`; README actualizado.
- Nombre de salida con ID, validez y forma canónica; se verificaron nombres únicos en los datasets.
- Concurrencia acotada, reintentos temporales, timeout y escritura centralizada y atómica.
- Reanudación que verifica prompt, sistema, modelo, ID y etiquetas; conserva resultados terminales filtrados.
- Validación de formato y colisiones antes de las llamadas; logs con fila y prompt de origen.
- Persistencia de errores y filtros, evaluación reproducible, auditoría formal y cinco pruebas locales aprobadas.

## Pendiente de decisión o implementación

- Revisar y corregir el generador o las etiquetas de la variante no canónica; acordar si el experimento debe repetirse después de corregirlo.
- Implementar y validar un extractor de respuesta final para las explicaciones de Claude, separando corrección lógica y cumplimiento del formato solicitado.
- Definir cómo reportar los filtros del proveedor y el denominador de las métricas; se conservan como resultados terminales separados.
- Acordar la ejecución de los seis datasets de pasado/futuro. No se lanzaron.
- Definir repeticiones, temperatura, semilla y demás parámetros para medir variabilidad. No se fijaron en estas corridas.
- Acordar si se añade `chainOfThought`. No se ejecutó.
- Separar cada repetición en una carpeta propia y evitar que dos procesos escriban sobre el mismo destino. Sin `--resume`, el runner todavía reemplaza resultados del mismo dataset/modelo/sistema.
- Unificar etiquetas y adaptar los formatos antiguos `HS_test`, `Csf` y `Csf2`, que se rechazan antes de la API.
- Registrar cada intento de API y su costo, incluidos errores y filtros intermedios; conciliar con la facturación del proveedor.
- Añadir cancelación ordenada de tareas pendientes y verificar la pausa de corridas paralelas.
