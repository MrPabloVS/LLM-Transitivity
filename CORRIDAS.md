# Registro de corridas — 2026-11-04

Directorio de trabajo: `/Users/andrestobelem/ws/at/LLM-Transitivity`. Branch: `tobe/dev`. Zona horaria de este registro: `America/Argentina/Buenos_Aires` (UTC−03:00).

Los comandos siguientes son los efectivamente ejecutados, no una lista de propuestas. Las horas de las tablas provienen de `created` en las respuestas de OpenRouter: identifican el intervalo de creación de las respuestas registradas, no el instante exacto de inicio/fin del proceso. El runner inicial solo incluyó minutos en el nombre del log. No se midió la concurrencia desde el servidor: se registran el modo secuencial y los límites de trabajadores configurados y anunciados por el runner.

## Configuración común

- API: `https://openrouter.ai/api/v1/chat/completions`.
- System prompt `zeroShot`: `Answer only with 'yes' or 'no' and nothing else.`
- Cada fila se envía en una conversación independiente, con un mensaje de sistema y uno de usuario.
- No se enviaron valores explícitos de temperatura, semilla, `max_tokens` ni proveedor; se utilizaron las opciones predeterminadas del servicio/modelo.
- Dependencias instaladas mediante `uv add requests python-dotenv`; ejecuciones mediante `uv run --locked`.
- La disponibilidad de los tres IDs se comprobó con `GET https://openrouter.ai/api/v1/models` antes de iniciar DeepSeek y Claude. Los IDs aparecían en el catálogo y no se sustituyeron. Los logs de las corridas completadas reportan esos mismos IDs.
- No se incluyen credenciales en este registro.

## 1. Prueba de tres casos con GPT-4o mini — completada

Se creó `prompts/userPrompts/HS_HF_PR_smoke_20261104_123831.json` seleccionando un caso por variante de `HS_HF_PR_500`, con IDs diferentes para evitar colisiones antes de modificar el nombre de salida.

Comando ejecutado por un subproceso:

```bash
uv run --locked runBenchmark.py HS_HF_PR_smoke_20261104_123831 --system zeroShot --model openai/gpt-4o-mini
```

- Intervalo de `created`: `2026-11-04T12:38:31-03:00` a `2026-11-04T12:38:35-03:00`.
- Runner original, secuencial: una llamada a la vez. Sin reanudación ni reintentos implementados.
- Resultado: 3/3 archivos, sin cortes. Coincidencias con etiquetas: 2/3. El caso no canónico recibió `no` frente a la etiqueta `valid`; ver la auditoría más abajo.
- Costo registrado: USD 0,00003045.
- Resultados: `data/zeroShot/openai_gpt-4o-mini/HS_HF_PR_smoke_20261104_123831/`.
- Log: `logs/HS_HF_PR_smoke_20261104_123831_openai_gpt-4o-mini_2026-11-04_12-38.json`.
- Esta prueba no se cuenta dentro de las corridas completas de 1.500 casos.

## 2. GPT-4o mini, dataset completo — completada

Dataset: `prompts/userPrompts/HS_HF_PR_500.json`, 1.500 filas. SHA-256: `4179b37ee0679559e134eb27037f8dde2cbdf4b14317b267eda8142e86a98620`. Modelo: `openai/gpt-4o-mini`.

Primera fase:

```bash
uv run --locked runBenchmark.py HS_HF_PR_500 --system zeroShot --model openai/gpt-4o-mini
```

- Ejecución secuencial, una llamada a la vez, después de agregar validez y forma canónica al nombre del archivo.
- Intervalo de `created` guardado: `2026-11-04T12:42:03-03:00` a `2026-11-04T12:43:46-03:00`.
- Se detuvo con SIGINT a pedido del usuario para implementar concurrencia y reanudación. Se conservaron 73 resultados válidos y 73 registros del log; el proceso terminó con código 130.
- Se interrumpió una solicitud en curso. No consta su resultado ni si generó un cobro; el costo registrado no permite resolverlo.
- Log: `logs/HS_HF_PR_500_openai_gpt-4o-mini_2026-11-04_12-42.json`.
- Costo registrado en esta fase: USD 0,0007446.

Segunda fase:

```bash
uv run --locked runBenchmark.py HS_HF_PR_500 --system zeroShot --model openai/gpt-4o-mini --workers 5 --resume
```

- Límite: 5 llamadas simultáneas. Al iniciar: 73 guardadas, 1.427 pendientes. Se reutilizaron las 73 sin volver a consultarlas.
- Intervalo de `created`: `2026-11-04T12:45:26-03:00` a `2026-11-04T12:51:41-03:00`.
- Resultado final: 1.500/1.500 archivos verificados contra su fila de origen; 0 fallos definitivos; código de salida 0. La modificación posterior a 10 trabajadores se aplicó a DeepSeek y Claude; GPT completó esta fase con 5.
- Log: `logs/HS_HF_PR_500_openai_gpt-4o-mini_zeroShot_2026-11-04_12-45-26_217901.json` (1.427 respuestas).
- Costo registrado en esta fase: USD 0,0144858.
- Resultados de ambas fases: `data/zeroShot/openai_gpt-4o-mini/HS_HF_PR_500/`.
- Total registrado: 1.500 respuestas, 97.009 tokens y USD 0,0152304.

## 3. DeepSeek, dataset completo — completada

Mismo dataset y system prompt. Modelo: `deepseek/deepseek-v4.1-flash`.

```bash
uv run --locked runBenchmark.py HS_HF_PR_500 --system zeroShot --model deepseek/deepseek-v4.1-flash --workers 10 --resume
```

- Límite: 10 llamadas simultáneas. Al iniciar: 0 guardadas, 1.500 pendientes; 0 casos reutilizados.
- Intervalo de `created`: `2026-11-04T12:51:42-03:00` a `2026-11-04T12:55:04-03:00`.
- Sin cortes ni reanudaciones adicionales. Resultado final: 1.500/1.500 archivos verificados; 0 fallos definitivos; código de salida 0.
- Resultados: `data/zeroShot/deepseek_deepseek-v4.1-flash/HS_HF_PR_500/`.
- Log: `logs/HS_HF_PR_500_deepseek_deepseek-v4.1-flash_zeroShot_2026-11-04_12-51-42_135179.json`.
- Total registrado: 1.500 respuestas, 310.933 tokens y USD 0,1218963435.

## 4. Claude Sonnet 4.5, dataset completo — completada

Mismo dataset y system prompt. Modelo: `anthropic/claude-sonnet-4.5`.

```bash
uv run --locked runBenchmark.py HS_HF_PR_500 --system zeroShot --model anthropic/claude-sonnet-4.5 --workers 10 --resume
```

- Límite: 10 llamadas simultáneas. Al iniciar: 0 guardadas, 1.500 pendientes; 0 casos reutilizados.
- Intervalo de `created`: `2026-11-04T12:55:21-03:00` a `2026-11-04T13:06:07-03:00`.
- Resultado final: 1.500/1.500 archivos verificados, 0 fallos definitivos; código de salida 0. Sin cortes ni reanudaciones adicionales.
- Total registrado: 1.500 respuestas, 323.423 tokens y USD 3,708729.
- 1.178 respuestas contienen texto adicional: no se interpretan como respuestas incorrectas en términos semánticos, pero quedan sin reconocer en la evaluación estricta `yes`/`no`.
- Resultados: `data/zeroShot/anthropic_claude-sonnet-4.5/HS_HF_PR_500/`.
- Log: `logs/HS_HF_PR_500_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_12-55-21_065222.json`.

## Evaluación HF y costos

`summarizeBenchmark.py` verifica que cada archivo corresponda al prompt, modelo, instrucciones, ID y etiquetas de su fila y tenga respuesta no vacía. Normaliza con `strip().lower().rstrip('.')`; cualquier salida distinta de `yes`/`no` queda como no reconocida y no cuenta como acierto. Compara `yes` con `valid` y `no` con `invalid`.

**Hay 500 etiquetas incorrectas bajo implicación material proposicional:** la variante `valid / non-canonic` usa `Q → R`, `P → Q`, por tanto `R → P`. Se verificaron las 1.500 filas por alcanzabilidad entre las proposiciones: las primeras 500 son válidas y las otras 1.000 inválidas. No se editaron las etiquetas ni las respuestas. Auditoría por fila: `summaries/HS_HF_PR_500_label_audit.json`. Las coincidencias con etiquetas no deben presentarse como exactitud lógica. Las salidas largas de Claude requieren además un extractor de respuesta final: los porcentajes de la tabla son métricas estrictas de formato y coincidencia, no una evaluación semántica de esas explicaciones.

| Modelo | Coincidencias con etiquetas | Coincidencias con validez proposicional auditada |
| --- | --- | --- |
| GPT-4o mini | 1.016/1.500 (67,73 %) | 1.480/1.500 (98,67 %) |
| DeepSeek | 1.000/1.500 (66,67 %) | 1.500/1.500 (100 %) |
| Claude Sonnet 4.5 | 286/1.500 (19,07 %) | 322/1.500 (21,47 %), con 1.178 salidas no reconocidas |

Los costos suman `usage.cost` de los logs enumerados. No incluyen llamadas sin respuesta registrada ni la prueba de 3 casos en el total de las corridas completas. Los tokens suman `usage.total_tokens`; no se infieren costos a partir de tarifas publicadas. Los reintentos transitorios están habilitados en las fases paralelas (hasta 3 reintentos con espera, timeout de conexión de 10 s y lectura de 120 s), pero no se instrumentó el número de intentos: 0 fallos definitivos no prueba que no haya habido reintentos.

Resumen verificable: `summaries/HS_HF_PR_500_zeroShot.json`. Los resúmenes incluyen los tres modelos de HF. Los pendientes de protocolo y las corridas no ejecutadas están en `PENDIENTES.md`.


## 5. Ampliación a todos los datasets de presente — finalizada

Se acordó ejecutar también `HS_LF_PR` y `HS_NS_PR_500` para los tres modelos, manteniendo `zeroShot`. Se lanzaron los seis procesos siguientes en paralelo, cada uno con un límite de 10 trabajadores. El máximo configurado conjunto fue 60, con un breve solapamiento con Claude/HF (otros 10) hasta las 13:06:07. No se midió el máximo real desde el servidor.

Antes de lanzarlos se copiaron 211 resultados históricos compatibles de GPT/LF al formato nuevo de nombres. Se comprobaron prompt, sistema, modelo, ID, etiquetas y respuesta. No se borraron los archivos originales. El registro de cada copia y su SHA-256 está en `summaries/HS_LF_PR_legacy_migration.json`. Por eso LF/GPT contiene 1.500 resultados de destino y además los 211 archivos originales; la verificación cuenta los destinos esperados, no todos los JSON de la carpeta.

### HS_LF_PR — openai/gpt-4o-mini

```bash
uv run --locked runBenchmark.py HS_LF_PR --system zeroShot --model openai/gpt-4o-mini --workers 10 --resume
```

- Dataset: `prompts/userPrompts/HS_LF_PR.json`, SHA-256 `3c3d0e9e746f3ba32204f86df7f124c7aa118b09ab0b3e3985facc9a351b175e`; 1.500 filas.
- Inicio: 211 reutilizados, 1289 pendientes. Límite inicial: 10 llamadas simultáneas.
- Primer proceso: 1289 respuestas de texto guardadas, 0 casos sin resultado; código de salida 0. Intervalo `created`: `2026-11-04T13:04:38-03:00` a `2026-11-04T13:06:49-03:00`.
- Estado final verificado: 1500/1.500 registros (1500 con texto, 0 filtrados). Coincidencias estrictas con etiquetas: 1106; textos no reconocidos como `yes`/`no`: 0.
- Resultados: `data/zeroShot/openai_gpt-4o-mini/HS_LF_PR/`. Resumen: `summaries/HS_LF_PR_zeroShot.json`.
- Costo nuevo registrado el 2026-11-04: USD 0.017592.
- Logs nuevos, incluidos los de recuperación o los derivados de errores:
  - `logs/HS_LF_PR_openai_gpt-4o-mini_zeroShot_2026-11-04_13-04-38_885700.json`: 1289 registros, USD 0.017592; `created` de `2026-11-04T13:04:38-03:00` a `2026-11-04T13:06:49-03:00`.
- Los logs históricos contienen 266 respuestas y USD 0.0036459; incluyen repeticiones anteriores y no se suman al costo nuevo. Los 211 resultados reutilizados no se volvieron a consultar.

### HS_LF_PR — deepseek/deepseek-v4.1-flash

```bash
uv run --locked runBenchmark.py HS_LF_PR --system zeroShot --model deepseek/deepseek-v4.1-flash --workers 10 --resume
```

- Dataset: `prompts/userPrompts/HS_LF_PR.json`, SHA-256 `3c3d0e9e746f3ba32204f86df7f124c7aa118b09ab0b3e3985facc9a351b175e`; 1.500 filas.
- Inicio: 0 reutilizados, 1500 pendientes. Límite inicial: 10 llamadas simultáneas.
- Primer proceso: 1500 respuestas de texto guardadas, 0 casos sin resultado; código de salida 0. Intervalo `created`: `2026-11-04T13:04:39-03:00` a `2026-11-04T13:08:22-03:00`.
- Estado final verificado: 1500/1.500 registros (1500 con texto, 0 filtrados). Coincidencias estrictas con etiquetas: 1000; textos no reconocidos como `yes`/`no`: 0.
- Resultados: `data/zeroShot/deepseek_deepseek-v4.1-flash/HS_LF_PR/`. Resumen: `summaries/HS_LF_PR_zeroShot.json`.
- Costo nuevo registrado el 2026-11-04: USD 0.1583320744.
- Logs nuevos, incluidos los de recuperación o los derivados de errores:
  - `logs/HS_LF_PR_deepseek_deepseek-v4.1-flash_zeroShot_2026-11-04_13-04-38_954555.json`: 1500 registros, USD 0.1583320744; `created` de `2026-11-04T13:04:39-03:00` a `2026-11-04T13:08:22-03:00`.

### HS_LF_PR — anthropic/claude-sonnet-4.5

```bash
uv run --locked runBenchmark.py HS_LF_PR --system zeroShot --model anthropic/claude-sonnet-4.5 --workers 10 --resume
```

- Dataset: `prompts/userPrompts/HS_LF_PR.json`, SHA-256 `3c3d0e9e746f3ba32204f86df7f124c7aa118b09ab0b3e3985facc9a351b175e`; 1.500 filas.
- Inicio: 0 reutilizados, 1500 pendientes. Límite inicial: 10 llamadas simultáneas.
- Primer proceso: 1473 respuestas de texto guardadas, 27 casos sin resultado; código de salida 1. Intervalo `created`: `2026-11-04T13:04:39-03:00` a `2026-11-04T13:17:11-03:00`.
- Estado final verificado: 1500/1.500 registros (1493 con texto, 7 filtrados). Coincidencias estrictas con etiquetas: 4; textos no reconocidos como `yes`/`no`: 1489.
- Resultados: `data/zeroShot/anthropic_claude-sonnet-4.5/HS_LF_PR/`. Resumen: `summaries/HS_LF_PR_zeroShot.json`.
- Costo nuevo registrado el 2026-11-04: USD 5.561514.
- Logs nuevos, incluidos los de recuperación o los derivados de errores:
  - `logs/HS_LF_PR_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-04-39_069548.json`: 1473 registros, USD 5.464461; `created` de `2026-11-04T13:04:39-03:00` a `2026-11-04T13:17:11-03:00`.
  - `logs/HS_LF_PR_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-17-42_948364.json`: 20 registros, USD 0.095139; `created` de `2026-11-04T13:18:23-03:00` a `2026-11-04T13:19:26-03:00`.
  - `logs/HS_LF_PR_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-20-26_095253_filtered_from_errors.json`: 7 registros, USD 0.001914; `created` de `2026-11-04T13:17:54-03:00` a `2026-11-04T13:18:33-03:00` (derivado de las últimas respuestas filtradas ya recibidas; no hubo nuevas llamadas).

### HS_NS_PR_500 — openai/gpt-4o-mini

```bash
uv run --locked runBenchmark.py HS_NS_PR_500 --system zeroShot --model openai/gpt-4o-mini --workers 10 --resume
```

- Dataset: `prompts/userPrompts/HS_NS_PR_500.json`, SHA-256 `17265dfa25c958ee375bd39ba07aa17d4694e8c72426e9bc41657c2b281414b5`; 1.500 filas.
- Inicio: 0 reutilizados, 1500 pendientes. Límite inicial: 10 llamadas simultáneas.
- Primer proceso: 1500 respuestas de texto guardadas, 0 casos sin resultado; código de salida 0. Intervalo `created`: `2026-11-04T13:04:39-03:00` a `2026-11-04T13:07:14-03:00`.
- Estado final verificado: 1500/1.500 registros (1500 con texto, 0 filtrados). Coincidencias estrictas con etiquetas: 986; textos no reconocidos como `yes`/`no`: 0.
- Resultados: `data/zeroShot/openai_gpt-4o-mini/HS_NS_PR_500/`. Resumen: `summaries/HS_NS_PR_500_zeroShot.json`.
- Costo nuevo registrado el 2026-11-04: USD 0.0215169.
- Logs nuevos, incluidos los de recuperación o los derivados de errores:
  - `logs/HS_NS_PR_500_openai_gpt-4o-mini_zeroShot_2026-11-04_13-04-39_042859.json`: 1500 registros, USD 0.0215169; `created` de `2026-11-04T13:04:39-03:00` a `2026-11-04T13:07:14-03:00`.

### HS_NS_PR_500 — deepseek/deepseek-v4.1-flash

```bash
uv run --locked runBenchmark.py HS_NS_PR_500 --system zeroShot --model deepseek/deepseek-v4.1-flash --workers 10 --resume
```

- Dataset: `prompts/userPrompts/HS_NS_PR_500.json`, SHA-256 `17265dfa25c958ee375bd39ba07aa17d4694e8c72426e9bc41657c2b281414b5`; 1.500 filas.
- Inicio: 0 reutilizados, 1500 pendientes. Límite inicial: 10 llamadas simultáneas.
- Primer proceso: 1500 respuestas de texto guardadas, 0 casos sin resultado; código de salida 0. Intervalo `created`: `2026-11-04T13:04:39-03:00` a `2026-11-04T13:08:22-03:00`.
- Estado final verificado: 1500/1.500 registros (1500 con texto, 0 filtrados). Coincidencias estrictas con etiquetas: 1000; textos no reconocidos como `yes`/`no`: 0.
- Resultados: `data/zeroShot/deepseek_deepseek-v4.1-flash/HS_NS_PR_500/`. Resumen: `summaries/HS_NS_PR_500_zeroShot.json`.
- Costo nuevo registrado el 2026-11-04: USD 0.1496106357.
- Logs nuevos, incluidos los de recuperación o los derivados de errores:
  - `logs/HS_NS_PR_500_deepseek_deepseek-v4.1-flash_zeroShot_2026-11-04_13-04-39_024233.json`: 1500 registros, USD 0.1496106357; `created` de `2026-11-04T13:04:39-03:00` a `2026-11-04T13:08:22-03:00`.

### HS_NS_PR_500 — anthropic/claude-sonnet-4.5

```bash
uv run --locked runBenchmark.py HS_NS_PR_500 --system zeroShot --model anthropic/claude-sonnet-4.5 --workers 10 --resume
```

- Dataset: `prompts/userPrompts/HS_NS_PR_500.json`, SHA-256 `17265dfa25c958ee375bd39ba07aa17d4694e8c72426e9bc41657c2b281414b5`; 1.500 filas.
- Inicio: 0 reutilizados, 1500 pendientes. Límite inicial: 10 llamadas simultáneas.
- Primer proceso: 1477 respuestas de texto guardadas, 23 casos sin resultado; código de salida 1. Intervalo `created`: `2026-11-04T13:04:39-03:00` a `2026-11-04T13:15:51-03:00`.
- Estado final verificado: 1500/1.500 registros (1500 con texto, 0 filtrados). Coincidencias estrictas con etiquetas: 66; textos no reconocidos como `yes`/`no`: 1434.
- Resultados: `data/zeroShot/anthropic_claude-sonnet-4.5/HS_NS_PR_500/`. Resumen: `summaries/HS_NS_PR_500_zeroShot.json`.
- Costo nuevo registrado el 2026-11-04: USD 4.896636.
- Logs nuevos, incluidos los de recuperación o los derivados de errores:
  - `logs/HS_NS_PR_500_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-04-39_003891.json`: 1477 registros, USD 4.79892; `created` de `2026-11-04T13:04:39-03:00` a `2026-11-04T13:15:51-03:00`.
  - `logs/HS_NS_PR_500_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-17-42_963362.json`: 23 registros, USD 0.097716; `created` de `2026-11-04T13:17:43-03:00` a `2026-11-04T13:18:47-03:00`.

### Recuperación de Claude y resultados filtrados

Las primeras fases de Claude/LF y Claude/NS terminaron con código 1. LF guardó 1.473 textos y dejó 27 casos: 7 respuestas vacías y 20 errores HTTP 402. NS guardó 1.477 textos y dejó 23 errores HTTP 402. La consulta de solo lectura a `/api/v1/auth/key` confirmó un límite de USD 20 y USD 5,982989207 disponibles en ese momento; `/api/v1/credits` también informó saldo positivo. El motivo exacto de los 402 no quedó capturado en la primera versión del runner; atribuirlos a reservas por concurrencia es una hipótesis, no una certeza.

Se ejecutaron los siguientes comandos en paralelo con un límite reducido de dos trabajadores por proceso, conservando modelo, prompts y parámetros de generación:

```bash
uv run --locked runBenchmark.py HS_LF_PR --system zeroShot --model anthropic/claude-sonnet-4.5 --workers 2 --resume
uv run --locked runBenchmark.py HS_NS_PR_500 --system zeroShot --model anthropic/claude-sonnet-4.5 --workers 2 --resume
```

- LF: reconoció 1.473 guardados, solicitó solo 27 pendientes y guardó 20 textos nuevos; terminó con 1.493 textos y 7 fallos, código 1.
- NS: reconoció 1.477 guardados, solicitó solo 23 pendientes y terminó con 1.500 textos, sin fallos; código 0.
- En la recuperación no aparecieron nuevos errores 402. Las siete respuestas restantes de LF se capturaron en `data/zeroShot/anthropic_claude-sonnet-4.5/HS_LF_PR/errors/` y reportan `finish_reason: content_filter`.
- Filas afectadas (índice desde 1): 131, 148, 407, 631, 648, 725 y 1054. Se habían intentado también en la primera fase; cada fase permitió hasta tres reintentos. Las primeras respuestas fallidas y los intentos intermedios no quedaron todos registrados.
- Un posprocesamiento local de Python copió las siete últimas respuestas API ya capturadas a sus archivos de destino con `responses: null`, `response_status: content_filter`, el payload API y la ruta de error de origen. No se inventó una respuesta ni se hicieron llamadas adicionales. Se creó el log derivado `*_filtered_from_errors.json` enumerado arriba. El costo de esas siete últimas respuestas (USD 0,001914) está incluido una sola vez en el costo nuevo; no se conocen todos los costos de sus intentos anteriores.
- Se adaptó el runner para registrar `content_filter` como un resultado terminal y evitar repetirlo durante `--resume`. También se persisten otros errores para facilitar el diagnóstico.

Validación final de reanudación, ejecutada después de registrar los filtros:

```bash
uv run --locked runBenchmark.py HS_LF_PR --system zeroShot --model anthropic/claude-sonnet-4.5 --workers 2 --resume
```

Salida: `saved: 1500; pending: 0`, `1500/1500 saved; 7 filtered; 0 failed`, código 0. Esta validación no hizo llamadas a la API.

## Cierre y comandos de verificación

- Total: 13.500 registros verificados (13.493 con texto y 7 filtrados). Incluye 211 resultados históricos reutilizados; 13.289 respuestas terminales corresponden a las ejecuciones nuevas. El número total de intentos API fue mayor por reintentos y una llamada interrumpida, y no puede reconstruirse exactamente.
- Costo nuevo registrado en los logs de estas nueve corridas: USD 14.6510573536. Prueba inicial de 3 casos: USD 0,00003045 adicionales. Se excluyen los logs históricos y los intentos no capturados; este total no es una conciliación completa de facturación.
- No se ejecutaron pasado, futuro, `chainOfThought` ni repeticiones nuevas. Las etiquetas originales se conservaron.
- Cinco pruebas locales pasaron: concurrencia/reanudación/persistencia, filtro terminal, auditoría lógica, reintento 429 y ausencia de reintento de autenticación. `git diff --check` pasó.

Los siguientes comandos se ejecutaron para cada dataset (se muestran completos):

```bash
uv run --locked summarizeBenchmark.py HS_HF_PR_500 --model openai/gpt-4o-mini --model deepseek/deepseek-v4.1-flash --model anthropic/claude-sonnet-4.5 --output summaries/HS_HF_PR_500_zeroShot.json
uv run --locked auditBenchmark.py HS_HF_PR_500 --model openai/gpt-4o-mini --model deepseek/deepseek-v4.1-flash --model anthropic/claude-sonnet-4.5 --output summaries/HS_HF_PR_500_label_audit.json
uv run --locked summarizeBenchmark.py HS_LF_PR --model openai/gpt-4o-mini --model deepseek/deepseek-v4.1-flash --model anthropic/claude-sonnet-4.5 --output summaries/HS_LF_PR_zeroShot.json
uv run --locked auditBenchmark.py HS_LF_PR --model openai/gpt-4o-mini --model deepseek/deepseek-v4.1-flash --model anthropic/claude-sonnet-4.5 --output summaries/HS_LF_PR_label_audit.json
uv run --locked summarizeBenchmark.py HS_NS_PR_500 --model openai/gpt-4o-mini --model deepseek/deepseek-v4.1-flash --model anthropic/claude-sonnet-4.5 --output summaries/HS_NS_PR_500_zeroShot.json
uv run --locked auditBenchmark.py HS_NS_PR_500 --model openai/gpt-4o-mini --model deepseek/deepseek-v4.1-flash --model anthropic/claude-sonnet-4.5 --output summaries/HS_NS_PR_500_label_audit.json
```

La auditoría formal no cambia el criterio de respuesta del experimento: las etiquetas se preservan, y sus inconsistencias se señalan por separado. La extracción semántica de respuestas largas de Claude sigue pendiente; los resultados estrictos no deben usarse como una clasificación de capacidad lógica entre modelos.
