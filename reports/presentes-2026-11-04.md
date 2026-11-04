# Modelos, vocabulario y validez lógica

Informe de las ejecuciones del 2026-11-04. Sistema: `zeroShot`. Tres modelos y tres datasets de presente.

**13.500 registros; 13.493 decisiones extraíbles; 7 filtros del proveedor; 211 resultados históricos reutilizados.**

[Abrir la versión HTML interactiva](presentes-2026-11-04.html). Incluye los argumentos y respuestas completos, filtros, búsqueda y evidencia de extracción.

## Antes de comparar

En cada dataset, las 500 filas etiquetadas como válidas no canónicas tienen premisas `Q → R`, `P → Q` y conclusión `R → P`. Esa conclusión es inválida bajo implicación material. Hay 1.500 etiquetas discrepantes en las 4.500 filas de origen de presente, equivalentes a 4.500 observaciones al considerar los tres modelos.

La referencia principal de este informe es la validez auditada. Las etiquetas y los resultados originales no se modificaron. La respuesta extraída es una decisión explícita, no una evaluación de todos los pasos de la explicación.

## Lectura de los resultados

- GPT-4o mini obtiene 83,87 % en LF, frente a 98,67 % en HF y 98,80 % en NS. Son diferencias descriptivas; GPT/LF mezcla 211 resultados históricos con 1.289 nuevos.
- DeepSeek responde correctamente los 4.500 casos auditados. Claude tiene 4.493 decisiones extraíbles correctas y siete filtros: 99,84 % sobre todos sus casos.
- Claude incluye texto adicional en 4.101 respuestas. Separar extracción y formato cambia sustancialmente la interpretación de sus resultados.

## Comparación principal

**Denominador: todos los casos**, incluidos filtros y casos no interpretables. La última columna usa la etiqueta original, pero la misma decisión extraída; no es el evaluador estricto anterior.

| Dataset | Modelo | Correctas auditadas / total | Corrección | Cobertura | Correctas según etiqueta original |
| --- | --- | ---: | ---: | ---: | ---: |
| `HS_HF_PR_500` | GPT-4o mini | 1480 / 1500 | 98,67 % | 100,00 % | 1016 / 1500 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | 1500 / 1500 | 100,00 % | 100,00 % | 1000 / 1500 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | 1500 / 1500 | 100,00 % | 100,00 % | 1000 / 1500 |
| `HS_LF_PR` | GPT-4o mini | 1258 / 1500 | 83,87 % | 100,00 % | 1106 / 1500 |
| `HS_LF_PR` | DeepSeek v4.1 flash | 1500 / 1500 | 100,00 % | 100,00 % | 1000 / 1500 |
| `HS_LF_PR` | Claude Sonnet 4.5 | 1493 / 1500 | 99,53 % | 99,53 % | 994 / 1500 |
| `HS_NS_PR_500` | GPT-4o mini | 1482 / 1500 | 98,80 % | 100,00 % | 986 / 1500 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | 1500 / 1500 | 100,00 % | 100,00 % | 1000 / 1500 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | 1500 / 1500 | 100,00 % | 100,00 % | 1000 / 1500 |

## Falsos positivos y falsos negativos

**Positivo = responder `yes`: aceptar el argumento como válido.** VP: válido aceptado; FP: inválido aceptado; FN: válido rechazado; VN: inválido rechazado. La referencia de estas tablas es la validez auditada.

Tasa de falsos positivos = `FP / (FP + VN)`; tasa de falsos negativos = `FN / (FN + VP)`. Los filtros y las decisiones no resueltas quedan fuera de estas tasas y de la matriz; no se convierten en respuestas negativas. La cobertura por clase se muestra aparte. La corrección principal anterior mantiene todos los casos en su denominador.

| Dataset | Modelo | VP | FP | FN | VN | Tasa FP | Tasa FN |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `HS_HF_PR_500` | GPT-4o mini | 498 | 18 | 2 | 982 | 18/1000 · 1,80 % | 2/500 · 0,40 % |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | 500 | 0 | 0 | 1000 | 0/1000 · 0,00 % | 0/500 · 0,00 % |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | 500 | 0 | 0 | 1000 | 0/1000 · 0,00 % | 0/500 · 0,00 % |
| `HS_LF_PR` | GPT-4o mini | 499 | 241 | 1 | 759 | 241/1000 · 24,10 % | 1/500 · 0,20 % |
| `HS_LF_PR` | DeepSeek v4.1 flash | 500 | 0 | 0 | 1000 | 0/1000 · 0,00 % | 0/500 · 0,00 % |
| `HS_LF_PR` | Claude Sonnet 4.5 | 497 | 0 | 0 | 996 | 0/996 · 0,00 % | 0/497 · 0,00 % |
| `HS_NS_PR_500` | GPT-4o mini | 484 | 2 | 16 | 998 | 2/1000 · 0,20 % | 16/500 · 3,20 % |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | 500 | 0 | 0 | 1000 | 0/1000 · 0,00 % | 0/500 · 0,00 % |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | 500 | 0 | 0 | 1000 | 0/1000 · 0,00 % | 0/500 · 0,00 % |

| Dataset | Modelo | Válidos interpretables / total válidos | Inválidos interpretables / total inválidos | Filtrados | Sin resolver |
| --- | --- | ---: | ---: | ---: | ---: |
| `HS_HF_PR_500` | GPT-4o mini | 500/500 | 1000/1000 | 0 | 0 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | 500/500 | 1000/1000 | 0 | 0 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | 500/500 | 1000/1000 | 0 | 0 |
| `HS_LF_PR` | GPT-4o mini | 500/500 | 1000/1000 | 0 | 0 |
| `HS_LF_PR` | DeepSeek v4.1 flash | 500/500 | 1000/1000 | 0 | 0 |
| `HS_LF_PR` | Claude Sonnet 4.5 | 497/500 | 996/1000 | 7 | 0 |
| `HS_NS_PR_500` | GPT-4o mini | 500/500 | 1000/1000 | 0 | 0 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | 500/500 | 1000/1000 | 0 | 0 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | 500/500 | 1000/1000 | 0 | 0 |

### Falsos positivos según la variante inválida

La variante originalmente llamada válida no canónica es inválida bajo la auditoría. Se compara por separado con la variante inválida canónica.

| Dataset | Modelo | Variante de origen | FP | VN | Tasa FP | Cobertura de inválidos |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `HS_HF_PR_500` | GPT-4o mini | Inválida canónica | 0 | 500 | 0,00 % | 500/500 |
| `HS_HF_PR_500` | GPT-4o mini | Válida no canónica (inválida auditada) | 18 | 482 | 3,60 % | 500/500 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | Inválida canónica | 0 | 500 | 0,00 % | 500/500 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | Válida no canónica (inválida auditada) | 0 | 500 | 0,00 % | 500/500 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | Inválida canónica | 0 | 500 | 0,00 % | 500/500 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | Válida no canónica (inválida auditada) | 0 | 500 | 0,00 % | 500/500 |
| `HS_LF_PR` | GPT-4o mini | Inválida canónica | 67 | 433 | 13,40 % | 500/500 |
| `HS_LF_PR` | GPT-4o mini | Válida no canónica (inválida auditada) | 174 | 326 | 34,80 % | 500/500 |
| `HS_LF_PR` | DeepSeek v4.1 flash | Inválida canónica | 0 | 500 | 0,00 % | 500/500 |
| `HS_LF_PR` | DeepSeek v4.1 flash | Válida no canónica (inválida auditada) | 0 | 500 | 0,00 % | 500/500 |
| `HS_LF_PR` | Claude Sonnet 4.5 | Inválida canónica | 0 | 497 | 0,00 % | 497/500 |
| `HS_LF_PR` | Claude Sonnet 4.5 | Válida no canónica (inválida auditada) | 0 | 499 | 0,00 % | 499/500 |
| `HS_NS_PR_500` | GPT-4o mini | Inválida canónica | 0 | 500 | 0,00 % | 500/500 |
| `HS_NS_PR_500` | GPT-4o mini | Válida no canónica (inválida auditada) | 2 | 498 | 0,40 % | 500/500 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | Inválida canónica | 0 | 500 | 0,00 % | 500/500 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | Válida no canónica (inválida auditada) | 0 | 500 | 0,00 % | 500/500 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | Inválida canónica | 0 | 500 | 0,00 % | 500/500 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | Válida no canónica (inválida auditada) | 0 | 500 | 0,00 % | 500/500 |

## Desglose por variante original

“Válida no canónica” conserva el nombre de origen; su validez auditada es inválida en estos datos.

| Dataset | Modelo | Variante original | Correctas auditadas / total |
| --- | --- | --- | ---: |
| `HS_HF_PR_500` | GPT-4o mini | Válida canónica | 498 / 500 |
| `HS_HF_PR_500` | GPT-4o mini | Inválida canónica | 500 / 500 |
| `HS_HF_PR_500` | GPT-4o mini | Válida no canónica | 482 / 500 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | Válida canónica | 500 / 500 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | Inválida canónica | 500 / 500 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | Válida no canónica | 500 / 500 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | Válida canónica | 500 / 500 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | Inválida canónica | 500 / 500 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | Válida no canónica | 500 / 500 |
| `HS_LF_PR` | GPT-4o mini | Válida canónica | 499 / 500 |
| `HS_LF_PR` | GPT-4o mini | Inválida canónica | 433 / 500 |
| `HS_LF_PR` | GPT-4o mini | Válida no canónica | 326 / 500 |
| `HS_LF_PR` | DeepSeek v4.1 flash | Válida canónica | 500 / 500 |
| `HS_LF_PR` | DeepSeek v4.1 flash | Inválida canónica | 500 / 500 |
| `HS_LF_PR` | DeepSeek v4.1 flash | Válida no canónica | 500 / 500 |
| `HS_LF_PR` | Claude Sonnet 4.5 | Válida canónica | 497 / 500 |
| `HS_LF_PR` | Claude Sonnet 4.5 | Inválida canónica | 497 / 500 |
| `HS_LF_PR` | Claude Sonnet 4.5 | Válida no canónica | 499 / 500 |
| `HS_NS_PR_500` | GPT-4o mini | Válida canónica | 484 / 500 |
| `HS_NS_PR_500` | GPT-4o mini | Inválida canónica | 500 / 500 |
| `HS_NS_PR_500` | GPT-4o mini | Válida no canónica | 498 / 500 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | Válida canónica | 500 / 500 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | Inválida canónica | 500 / 500 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | Válida no canónica | 500 / 500 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | Válida canónica | 500 / 500 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | Inválida canónica | 500 / 500 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | Válida no canónica | 500 / 500 |

## Formato y respuesta explícita

El formato estricto conserva el normalizador original: `strip().lower().rstrip(".")`. La extracción admite además una decisión explícita al inicio seguida de puntuación o una última línea formada por `yes`/`no`, con Markdown o `Answer:` opcionales. Señales contradictorias quedan como conflicto; ausencia de señales, sin resolver. No se infiere una respuesta de “yes or no” ni de la explicación completa.

| Dataset | Modelo | Formato estricto / total | Decisión extraíble / total | Precisión sobre interpretables | Filtrados |
| --- | --- | ---: | ---: | ---: | ---: |
| `HS_HF_PR_500` | GPT-4o mini | 1500 / 1500 | 1500 / 1500 | 98,67 % | 0 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | 1500 / 1500 | 1500 / 1500 | 100,00 % | 0 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | 322 / 1500 | 1500 / 1500 | 100,00 % | 0 |
| `HS_LF_PR` | GPT-4o mini | 1500 / 1500 | 1500 / 1500 | 83,87 % | 0 |
| `HS_LF_PR` | DeepSeek v4.1 flash | 1500 / 1500 | 1500 / 1500 | 100,00 % | 0 |
| `HS_LF_PR` | Claude Sonnet 4.5 | 4 / 1500 | 1493 / 1500 | 100,00 % | 7 |
| `HS_NS_PR_500` | GPT-4o mini | 1500 / 1500 | 1500 / 1500 | 98,80 % | 0 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | 1500 / 1500 | 1500 / 1500 | 100,00 % | 0 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | 66 / 1500 | 1500 / 1500 | 100,00 % | 0 |

## Costos registrados

Total nuevo registrado: **USD 14,65106**. Suma `usage.cost` de los logs de las corridas del 4 de noviembre, incluidos una sola vez los siete últimos filtros recuperados.

Quedan separados la prueba inicial de tres casos (USD 0,00003045), los logs históricos y los intentos fallidos o interrumpidos no registrados por completo. Este total no sustituye una conciliación de facturación. Los logs históricos pueden contener repeticiones y no determinan el costo exacto de los 211 resultados reutilizados.

| Dataset | Modelo | USD nuevos | Tokens nuevos registrados | Registros nuevos en logs | USD históricos |
| --- | --- | ---: | ---: | ---: | ---: |
| `HS_HF_PR_500` | GPT-4o mini | USD 0,01523 | 97.009 | 1.500 | USD 0,00000 |
| `HS_HF_PR_500` | DeepSeek v4.1 flash | USD 0,12190 | 310.933 | 1.500 | USD 0,00000 |
| `HS_HF_PR_500` | Claude Sonnet 4.5 | USD 3,70873 | 323.423 | 1.500 | USD 0,00000 |
| `HS_LF_PR` | GPT-4o mini | USD 0,01759 | 113.404 | 1.289 | USD 0,00365 |
| `HS_LF_PR` | DeepSeek v4.1 flash | USD 0,15833 | 405.941 | 1.500 | USD 0,00000 |
| `HS_LF_PR` | Claude Sonnet 4.5 | USD 5,56151 | 482.006 | 1.500 | USD 0,00000 |
| `HS_NS_PR_500` | GPT-4o mini | USD 0,02152 | 138.937 | 1.500 | USD 0,00000 |
| `HS_NS_PR_500` | DeepSeek v4.1 flash | USD 0,14961 | 398.936 | 1.500 | USD 0,00000 |
| `HS_NS_PR_500` | Claude Sonnet 4.5 | USD 4,89664 | 435.156 | 1.500 | USD 0,00000 |

## Filtros y procedencia

- Claude/LF: filas 131, 148, 407, 631, 648, 725 y 1054, contadas desde 1. El proveedor devolvió `content_filter`; se preservó texto nulo. Ningún filtro se interpreta como `no`.
- Los 211 resultados históricos pertenecen a GPT/LF. Se comprobaron prompt, sistema, modelo, ID, etiquetas y respuesta antes de reutilizarlos. No equivalen a una repetición nueva.
- Cada caso se identifica por dataset y fila; los IDs de base están compartidos entre las tres variantes.

## Método y límites

- La auditoría enumera todas las asignaciones de verdad de las cláusulas, tratadas como proposiciones atómicas independientes. Busca si ambas premisas pueden ser verdaderas y la conclusión falsa.
- Corrección principal = correctas / total. Cobertura = decisiones extraíbles / total. Precisión sobre interpretables = correctas / decisiones extraíbles. Cumplimiento de formato = respuestas directas normalizadas / total.
- La corrección principal mantiene filtros y respuestas sin decisión en el denominador. El informe no juzga la validez de cada paso de las explicaciones.
- No hubo repeticiones nuevas, temperatura ni semilla fijadas. Las variantes no son réplicas independientes. No se atribuye causalidad al vocabulario ni se realizan pruebas de significancia.
- No se hicieron nuevas llamadas a modelos para producir este análisis.

## Configuración y trazabilidad

Instrucción de sistema: `Answer only with 'yes' or 'no' and nothing else.`.

[Registro de comandos y corridas](../CORRIDAS.md) · [Pendientes](../PENDIENTES.md).

- `prompts/userPrompts/HS_HF_PR_500.json`: 1500 filas; SHA-256 `4179b37ee0679559e134eb27037f8dde2cbdf4b14317b267eda8142e86a98620`.
- `prompts/userPrompts/HS_LF_PR.json`: 1500 filas; SHA-256 `3c3d0e9e746f3ba32204f86df7f124c7aa118b09ab0b3e3985facc9a351b175e`.
- `prompts/userPrompts/HS_NS_PR_500.json`: 1500 filas; SHA-256 `17265dfa25c958ee375bd39ba07aa17d4694e8c72426e9bc41657c2b281414b5`.

Logs utilizados para costos:

- `logs/HS_HF_PR_500_openai_gpt-4o-mini_2026-11-04_12-42.json`
- `logs/HS_HF_PR_500_openai_gpt-4o-mini_zeroShot_2026-11-04_12-45-26_217901.json`
- `logs/HS_HF_PR_500_deepseek_deepseek-v4.1-flash_zeroShot_2026-11-04_12-51-42_135179.json`
- `logs/HS_HF_PR_500_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_12-55-21_065222.json`
- `logs/HS_LF_PR_openai_gpt-4o-mini_zeroShot_2026-11-04_13-04-38_885700.json`
- `logs/HS_LF_PR_openai_gpt-4o-mini_2026-10-26_19-03.json`
- `logs/HS_LF_PR_openai_gpt-4o-mini_2026-10-26_19-14.json`
- `logs/HS_LF_PR_deepseek_deepseek-v4.1-flash_zeroShot_2026-11-04_13-04-38_954555.json`
- `logs/HS_LF_PR_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-04-39_069548.json`
- `logs/HS_LF_PR_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-17-42_948364.json`
- `logs/HS_LF_PR_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-20-26_095253_filtered_from_errors.json`
- `logs/HS_NS_PR_500_openai_gpt-4o-mini_zeroShot_2026-11-04_13-04-39_042859.json`
- `logs/HS_NS_PR_500_deepseek_deepseek-v4.1-flash_zeroShot_2026-11-04_13-04-39_024233.json`
- `logs/HS_NS_PR_500_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-04-39_003891.json`
- `logs/HS_NS_PR_500_anthropic_claude-sonnet-4.5_zeroShot_2026-11-04_13-17-42_963362.json`

Generado: 2026-11-04T13:56:43.914070-03:00 (hora de Buenos Aires).
