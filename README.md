# LLM-Transitivity

Use the installed Inspect workflow to evaluate the reasoning corpus.
The completed full-corpus report is below. For another paid run, follow the
[full-corpus guide](docs/full_corpus.md) and its input checks.

## Full-corpus results

[Guía paso a paso en español: instalación, generación y explorador](docs/guia_informe_es.md).

The completed run contains 54,000 cases evaluated by six models: 324,000 responses
in 108 tasks. Read the [full report](reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2/report.md)
or download the [continuous, single-page PDF](reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2/report.pdf).
You can also use the [HTML report](reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2/index.html).
Use the separate [interactive tables and case explorer](reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2/explorer.html)
to filter results and inspect original responses.
The report measures agreement with source labels, not audited logical validity.

Build a new report offline from the closed native evidence:

```sh
uv run --locked transitivity report --run results/full/2026-11-06_01-23-40-040fd7b7 --output reports/full/2026-11-06_01-23-40-040fd7b7/new-analysis
```

The output directory must not exist. The command makes no provider API calls.
The HTML report and explorer must be served locally; GitHub shows their source.
From the repository root, run:

```sh
uv run --locked python -m http.server 8000 --bind 127.0.0.1
```

Leave that terminal open. Open the
[HTML report](http://localhost:8000/reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2/index.html)
or the [interactive explorer](http://localhost:8000/reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2/explorer.html).
Press `Ctrl+C` to stop the server. The report links to the separate explorer.

Git LFS stores every file in the completed run, plus the report's compressed
SQLite database and response CSV. The run contains about 15.4 GB of evidence.
Run `git lfs pull` after cloning and follow the
[report bundle instructions](reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2/README.md)
to restore the database. All report assets and dataset files are local. See the
[architecture guide](docs/architecture.md#offline-full-corpus-report) for checks
and data responsibilities.

## Static analysis and interpretation

Read the new [interpretation in Markdown](reports/full/2026-11-06_01-23-40-040fd7b7/interpretation-v1/report.md),
[static HTML](reports/full/2026-11-06_01-23-40-040fd7b7/interpretation-v1/index.html),
or [continuous PDF](reports/full/2026-11-06_01-23-40-040fd7b7/interpretation-v1/report.pdf).
It explains model differences, condition contrasts, answer format, and costs in
simplified English. It adds descriptive crosses and 12 static figures in eight
groups. Source-label agreement is not an audit of logical validity.

Unlike the interactive explorer, this HTML opens directly from disk. It has no
JavaScript or external assets. The Markdown, HTML, and PDF share the same text
and values. The original report and native evidence remain unchanged.

To reproduce the interpretation in a new directory:

```sh
uv run --locked transitivity interpret --report reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v1 --output reports/full/2026-11-06_01-23-40-040fd7b7/new-interpretation
```

The command is defined for this completed run and scoring version. It checks the
source report before rendering. The destination must not exist. No API key,
model calls, or browser service is needed. The output includes SVG and PNG
figures, CSV tables, shared document blocks, summary data, input hashes, and a
validation record. DuckDB and ReportLab are installed by `uv sync --locked`.

The original report now separates false positives and false negatives, with
class-specific error rates and coverage for every condition. Positive means
`yes`; comparisons use source labels, not audited logical validity.
The [previous original report](reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v1/report.md),
[previous PDF](output/pdf/full-corpus-report-continuous.pdf), and
[static interpretation](reports/full/2026-11-06_01-23-40-040fd7b7/interpretation-v1/report.md)
remain unchanged. Each new `report` command also creates a continuous `report.pdf`.

## Saved data

All derived files below belong to the same
[report bundle](reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2/).

| File or folder | Contents |
| --- | --- |
| `tables/responses.csv` | Response text, model, UID, interpretation, scores, tokens, and duration; corpus and preflight rows |
| `tables/totals.csv`, `tables/by_*.csv` | Model totals and condition breakdowns |
| `tables/pairwise.csv` | Paired model comparisons |
| `tables/costs.csv`, `tables/generations.csv` | Costs and generation records |
| `data/*.json` | 18 files with 54,000 cases, original prompts, source labels, conditions, and six responses per case |
| `summary.json` | Configuration and aggregate results |
| `validation.json`, `provenance.json` | Reconciliation checks and source hashes |
| `analysis.sqlite.gz` | Compressed derived SQLite database |

The CSV response table contains 324,000 corpus rows and six preflight rows.
Missing costs remain unknown, not zero. Filters and uninterpretable answers
remain separate from `no`. The case JSON files contain corpus responses only.

## Explore results with DuckDB

Open the saved report in DuckDB UI:

```sh
uv run --locked transitivity explore --report reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v2
```

Expand the database and its `report` schema. `case_details` contains original
prompts and all six responses. `responses` contains response rows; filter
`phase = 'corpus'` to exclude preflight. Other views expose the CSV summaries.
Empty CSV files, such as a ledger with no cost conflicts, have no view.

The command keeps running until you press `Ctrl+C`. Use `--port 4214` to select
another port, or `--no-browser` to print the URL without opening a browser.
The UI downloads its extension and web assets. Queries run locally. Source
files stay unchanged. Local database state is saved in `.local/duckdb/`, which
Git ignores. Stop another UI process on the selected port before you start.

For example, use a SQL notebook in DuckDB UI:

```sql
SELECT model, count(*) AS responses
FROM report.responses
WHERE phase = 'corpus'
GROUP BY model;

SELECT uid, prompt, target, responses
FROM report.case_details
LIMIT 20;
```

This command reads CSV and JSON files directly. You do not need to decompress
SQLite or rebuild the report. DuckDB UI is separate from the HTML case explorer.

## Documentation

| Topic | Source |
| --- | --- |
| Project conventions and preservation | [Constitution](CONSTITUTION.md) |
| Domain terms | [Glossary](GLOSSARY.md) |
| Original pilot procedure and routing | [Pilot guide](docs/pilot.md) |
| Full-corpus execution and recovery | [Full-corpus guide](docs/full_corpus.md) |
| Detailed installation and report instructions in Spanish | [Spanish guide](docs/guia_informe_es.md) |
| Cost estimation procedure | [Cost procedure](docs/pilot_costs.md) |
| Package responsibilities and dependencies | [Architecture](docs/architecture.md) |
| Dataset files and formats | [Dataset catalog](docs/dataset_catalog.md) |
| Inspect metadata and call exports | [Metadata guide](docs/inspect_metadata.md) |
| Dated public model snapshots | [Model cards](docs/model_cards/README.md) |

The generated dataset inventory and saved model cards are dated reference
artifacts. Use the matching execution guide for commands. Saved run closures and reports
record the results of each completed experiment.
[CHANGELOG.md](CHANGELOG.md) records historical changes to the original runner.
It is not the release history of the installed package; use Git history for that.

## Install uv

### macOS

Open Terminal and run:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

Open PowerShell and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, close and reopen your terminal. Check the installation:

```sh
uv --version
```

See the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for details and other installation methods.

## Environment setup

Install Git and Git LFS before cloning. The
[Spanish guide](docs/guia_informe_es.md) includes installation steps for macOS
and Windows. Use a full clone, not a ZIP download or shallow clone: input
verification needs the original Git revision. Preserve line endings so source
hashes remain valid on Windows.

```sh
git lfs install
git -c core.longpaths=true -c core.autocrlf=false clone --branch tobe/runs-2026-11-05 https://github.com/MrPabloVS/LLM-Transitivity.git
cd LLM-Transitivity
git config core.longpaths true
git config core.autocrlf false
git lfs pull
uv python install 3.14
uv sync --locked
```

The LFS download includes the complete run evidence. Allow space for the clone,
LFS objects, and derived outputs. `uv sync --locked` installs the package,
DuckDB, Inspect, and development tools from the lockfile.

Before generating a report, enable UTF-8 in the same terminal.
On macOS:

```sh
export PYTHONUTF8=1
```

On Windows PowerShell:

```powershell
$env:PYTHONUTF8 = "1"
```

Reading saved reports, using DuckDB, and generating reports need no API key.
For new model calls only, create `.env` in the repository with
`OPENROUTER_API_KEY=your-key`. Do not commit this file.

## Installed commands

Run `uv run --locked transitivity --help` for the command list. Add `--help`
after a subcommand to inspect its arguments without starting it.

| Command | Purpose |
| --- | --- |
| `report` | Build a report from a closed full-corpus run without provider calls |
| `interpret` | Produce static analysis, figures, and a continuous PDF from a validated report |
| `explore` | Open DuckDB UI over an existing report |
| `datasets` | Prepare or verify experiment inputs |
| `pilot` | Preview or run a coverage pilot or preflight |
| `followup` | Prepare or run the follow-up program |
| `full` | Prepare, run, or resume a full-corpus experiment |
| `costs` | Request public quotes and save a new estimate |
| `export` | Export saved calls, with optional generation metadata requests |

From another directory, select both the uv project and repository root:

```sh
uv run --locked --project /path/to/repository transitivity --root /path/to/repository explore --report reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v1
```

The installed commands replace the removed root Python adapters.

## Historical benchmark runner

`runBenchmark.py` preserves the script from the main baseline. It reads user
prompts from `prompts/userPrompts/` and writes results under `data/` and `logs/`.
It does not use the pilot configuration or its input checks.

This script expects eight fields per input record. `HS_test.json` has seven
fields and is not compatible. Use the Inspect commands below for the pilot.

## Inspect Flow pilot

`uv sync --locked` installs the `llm_transitivity` package from `src/`.
Use the installed commands above to select the required workflow. See the
[architecture guide](docs/architecture.md) for module responsibilities,
compatibility, provenance, and failure handling.

Available commands:

```sh
uv run --locked transitivity --help
uv run --locked transitivity datasets verify
uv run --locked transitivity pilot --dry-run
uv run --locked transitivity costs --help
uv run --locked transitivity export --help
```

`transitivity costs` saves each estimate to a new directory under
`results/cost_estimates/` and prints its path. See the
[cost procedure](docs/pilot_costs.md) for assumptions and checks.

See the [six-model coverage pilot](docs/pilot.md) for model pairs, fixed
providers, historical price snapshots, reasoning settings, and verification
commands. This original pilot differs from Pilot 2.0, Pilot 3, and the full run.
In the full run, Sonnet 5.5 and Gemini 3.5 Flash-Lite have reasoning enabled;
use the frozen run configuration and full-corpus report for exact conditions.
The [dataset catalog](docs/dataset_catalog.md) explains filenames and links all
18 full datasets and their pilot samples.
All full datasets can also be adapted to Inspect with source verification; see
[complete dataset preparation](docs/dataset_catalog.md#complete-datasets-in-inspect). The generated
[dataset inventory](docs/dataset_inventory.md) records counts and all 108 observed strata.
Its old script commands are capture-time text. Use `transitivity datasets verify`
for current verification.

The Flow configuration uses five cases per stratum: 540 cases per model,
or 3,240 planned responses across six models. It uses the original `zeroShot`
system message and verifies sentence preservation against a fixed Git revision.
It preserves source identifiers, original row numbers, hashes, and labels as
sample metadata. Scoring measures agreement with the source labels: `valid`
expects `yes`, and `invalid` expects `no`. This does not establish logical validity.

The scorer trims outer whitespace and ignores letter case. Format compliance
requires only `yes` or `no`. Content interpretation also accepts an initial
`yes` or `no` followed by whitespace or punctuation, with an optional `Answer:`
prefix. It also accepts a final line that contains only `yes` or `no`, with an
optional `Answer:` prefix and one optional `.`, `!`, or `?`. For example,
`Yes, it follows.` can agree with the source label while failing the format
requirement. Responses with both whole words `yes` and `no`
are marked ambiguous. Other text is not interpreted. These conservative rules
do not interpret arbitrary explanations or resolve contradictions in prose.
Score metadata records the extraction rule version and the answer position.
Existing logs keep the scores and rules used when they were created.

The current extraction rule is `initial_or_final_line_v2`, with scoring version
`source-label-deterministic-v3`. It also accepts balanced bold `**yes**` or
`**no**` initially or on the final line, with one optional final punctuation
mark. A complete final line `Therefore, yes.` or `Therefore, no.` is accepted
with optional `.`, `!`, or `?`. These forms remain strict-format violations.
See the [pilot results](docs/pilot_report.md) for the derived reevaluation;
native historical logs retain their original scores.

`source_agreement` uses interpreted answers as its denominator.
`format_compliant_rate` uses all scored samples as its denominator.
Response rates report answered, empty, filtered, invalid-format, ambiguous, and output-error
categories over scored samples. Inspect records execution errors separately;
those samples are not scored and are outside these rate denominators. Inspect
logs must therefore be checked for errors as well as response coverage.

Preview the pilot without model calls:

```sh
uv run --locked transitivity datasets verify
uv run --locked transitivity pilot --dry-run
```

After the readiness sequence, run the pilot with `OPENROUTER_API_KEY` in `.env`:

```sh
uv run --locked transitivity pilot
```

The run command requests 3,240 model responses, plus any retries.
Each managed run keeps all six models and 18 datasets together under
`results/pilot/<local-date-time>-<run-id>/`: `inspect/`, `openrouter_calls/`,
`provenance/`, and `summary/`. Folder timestamps use Buenos Aires time.
Provenance is saved before model calls; call exports and a log index are saved
when the run finishes or unwinds after an error. See the pilot guide for details.
The legacy runner and the 10-case `HS.json` smoke dataset remain available.
The full datasets are not executed by this pilot configuration.

See the [Inspect Flow guide](https://meridianlabs-ai.github.io/inspect_flow/)
and the [Inspect OpenRouter guide](https://inspect.aisi.org.uk/providers.html#openrouter).

## Haiku follow-up

The [Haiku follow-up](docs/haiku_followup.md) prepares two 540-case Haiku pilots
and a separate 216-case load selection. It uses a six-model preflight, coverage
at 16, and direct load at 64 with one active task. The default Sonnet experiment
is unchanged. Use `uv run --locked transitivity followup --dry-run` to preview
all 48 tasks and 2,382 planned responses without API calls.

The [latest follow-up results](docs/haiku_followup_results.md) include the Haiku
comparison and the reason the 64-slot load was not executed.

## Pilot 2.0

See [the preparation guide](docs/pilot2.md) for the six-model selection, fixed
providers, unchanged 540-case input selection, and 108-task schedule at 32 samples
per task. The [saved cards](docs/model_cards/README.md#pilot-20) include manufacturer
documents and full endpoint snapshots. The [completed results](docs/pilot2_results.md) include 3,240 coverage responses,
per-model checks, retries, filters, and reported costs.

## Pilot 3

See [Pilot 3](docs/pilot3.md) for the Haiku 5.5 replacement and the 108-task
schedule at 64 samples per task. Read the [completed results](docs/pilot3_results.md).
The full corpus is a separate run.

## Full corpus

The [full-corpus procedure](docs/full_corpus.md) uses all 54,000 cases for each
of the six Pilot 3 models, with 108 tasks in total, six active tasks, 32 samples per task,
and adaptive model connections.
Use `transitivity full --dry-run` to check the 324,000-response configuration.

## Development checks

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
uv build
```

Global Ruff checks also inspect preserved historical code. Report existing
failures separately; do not rewrite historical files to fix lint findings.

## Contributors

- Eduardo Barrio
- Bruno Da Ré
- Pablo Vazquez Soldano
- Lourdes De Carolis
- Tomas Gomez Ansede
- Guadalupe Fernández Fagioli
- Nadia Belén Martínez Szego
- Sofia de Arias Vargas
- Lourdes Nazarena Toneatti
