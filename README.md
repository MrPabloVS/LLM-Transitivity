# LLM-Transitivity

Use the installed Inspect workflow for the six-model coverage pilot.
Preparation has restarted. See [current preparation status](docs/pilot.md#current-preparation-status)
and complete the [readiness sequence](docs/pilot.md#readiness-sequence) before a paid run.

## Documentation

| Topic | Source |
| --- | --- |
| Project conventions and preservation | [Constitution](CONSTITUTION.md) |
| Domain terms | [Glossary](GLOSSARY.md) |
| Pilot procedure, routing decision, and readiness | [Pilot guide](docs/pilot.md) |
| Cost estimation procedure | [Cost procedure](docs/pilot_costs.md) |
| Package responsibilities and dependencies | [Architecture](docs/architecture.md) |
| Dataset files and formats | [Dataset catalog](docs/dataset_catalog.md) |
| Inspect metadata and call exports | [Metadata guide](docs/inspect_metadata.md) |
| Dated public model snapshots | [Model cards](docs/model_cards/README.md) |

The generated dataset inventory and saved model cards are dated reference
artifacts. Use the guides above for current commands and execution status.
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

1. [Install uv](#install-uv). The project uses Python 3.14.
2. Run `uv sync --locked` in the project folder to install the locked dependencies.
3. Create `.env` in the project folder with `OPENROUTER_API_KEY=your-key`.

Use the [Inspect Flow pilot](#inspect-flow-pilot) for the current workflow.

## Historical benchmark runner

`runBenchmark.py` preserves the script from the main baseline. It reads user
prompts from `prompts/userPrompts/` and writes results under `data/` and `logs/`.
It does not use the pilot configuration or its input checks.

This script expects eight fields per input record. `HS_test.json` has seven
fields and is not compatible. Use the Inspect commands below for the pilot.

## Inspect Flow pilot

`uv sync --locked` installs the `llm_transitivity` package from `src/`.
The installed `transitivity` command provides `pilot`, `datasets`, `costs`,
and `export` subcommands. See the
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

From another directory, select both the uv project and repository root:

```sh
uv run --locked --project /path/to/repository transitivity --root /path/to/repository pilot --dry-run
```

The installed commands replace the removed root Python adapters.

See the [six-model coverage pilot](docs/pilot.md) for model pairs, fixed
providers, prices, settings without reasoning, and verification commands.
The [dataset catalog](docs/dataset_catalog.md) explains filenames and links all
18 full datasets and their pilot samples. The generated
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

## Contributors:  
Eduardo Barrio  
Bruno Da Ré  
Pablo Vazquez Soldano  
Lourdes De Carolis  
Tomas Gomez Ansede  
Guadalupe Fernández Fagioli  
Nadia Belén Martínez Szego  
Sofia de Arias Vargas  
Lourdes Nazarena Toneatti
