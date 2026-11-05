# LLM-Transitivity

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

## Instructions for running the benchmark  
1. [Install uv](#install-uv). The project uses Python 3.14.
2. Run `uv sync --locked` in the project folder to prepare the Python environment and install the locked dependencies.
3. Create a file named exactly .env in the project folder and write your API KEY like this: OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxx  
4. Run the benchmark: `uv run --locked runBenchmark.py HS --system zeroShot --model anthropic/claude-sonnet-4.5`
 - HS is the user prompts file name without .json  
 - --system picks the system prompt file (default zeroShot).  
 - --model picks the model, in provider/model format from openrouter.ai/models (default openai/gpt-4o-mini). 


## Inspect Flow trial

See the [six-model coverage pilot](docs/pilot.md) for model pairs, fixed
providers, prices, settings without reasoning, and verification commands.
The [dataset catalog](docs/dataset_catalog.md) explains filenames and links all
18 full datasets and their pilot samples. The generated
[dataset inventory](docs/dataset_inventory.md) records counts and all 108 observed strata.

The Flow configuration uses five cases per stratum: 540 cases per model,
or 3,240 planned responses across six models. It uses the original `zeroShot`
system message and verifies sentence preservation against a fixed Git revision.
It preserves source identifiers, original row numbers, hashes, and labels as
sample metadata. Scoring measures agreement with the source labels: `valid`
expects `yes`, and `invalid` expects `no`. This does not establish logical validity.

The scorer trims outer whitespace and ignores letter case. Format compliance
requires only `yes` or `no`. Content interpretation also accepts an initial
`yes` or `no` followed by whitespace or punctuation, with an optional `Answer:`
prefix. For example, `Yes, it follows.` can agree with the source label while
failing the format requirement. Responses with both whole words `yes` and `no`
are marked ambiguous. Other text is not interpreted. These conservative rules
do not interpret arbitrary explanations or resolve contradictions in prose.

`source_agreement` uses interpreted answers as its denominator.
`format_compliant_rate` uses all scored samples as its denominator.
Response rates report answered, empty, filtered, invalid-format, ambiguous, and output-error
categories over scored samples. Inspect records execution errors separately;
those samples are not scored and are outside these rate denominators. Inspect
logs must therefore be checked for errors as well as response coverage.

Preview the trial without model calls:

```sh
uv run --locked prepare_pilot.py verify
uv run --locked run_pilot.py --dry-run
```

To run the trial with your `OPENROUTER_API_KEY` in `.env`:

```sh
uv run --locked run_pilot.py
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
