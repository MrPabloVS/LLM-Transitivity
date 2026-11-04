# LLM-Transitivity

## Instructions for running the benchmark  
1. Check for python instalation bu running on the terminal: python --version. If it fails, Download Python from python.org/downloads. Then close and reopen the terminal.  
2. Run on the terminal: uv sync
3. Create a file named exactly .env in the project folder and write your API KEY like this: OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxx  
4. Run the benchmark as follows: uv run runBenchmark.py HS_HF_PR_500 --system zeroShot --model anthropic/claude-sonnet-4.5
 - HS_HF_PR_500 is the user prompts file name without .json
 - --system picks the system prompt file (default zeroShot).  
 - --model picks the model, in provider/model format from openrouter.ai/models (default openai/gpt-4o-mini). 
 - --workers sets the maximum simultaneous calls (default 1).
 - --resume skips saved results whose prompt, model, system prompt, ID and tags match.
 - --retries sets retries for temporary failures (default 3).

To run with five simultaneous calls and continue from saved results:
```bash
uv run runBenchmark.py HS_HF_PR_500 --system zeroShot --model openai/gpt-4o-mini --workers 5 --resume
```


## Results
Result filenames include the case ID, validity and canonical form so the three variants are saved separately: `<model>_<id>_<benchmark>_<validity>_<canonical-form>.json`.
Without `--resume`, running the same dataset and model again replaces the corresponding results from the previous run. With `--resume`, only missing or mismatched results are requested. Logs identify each new response with its source row and prompt; a resumed run writes a separate log.

Summarize saved answers against dataset labels and sum the recorded log costs:
```bash
uv run summarizeBenchmark.py HS_HF_PR_500 --model openai/gpt-4o-mini --model deepseek/deepseek-v4.1-flash --model anthropic/claude-sonnet-4.5 --output summaries/HS_HF_PR_500_zeroShot.json
```
The summary reports missing or mismatched rows and returns a nonzero exit status if a model is incomplete. Terminal provider filters are saved with `response_status: content_filter` and null response text, counted separately, and skipped on resume. Costs cover all matching logs, including repeated executions and logged filters; intermediate failed attempts are not fully captured, and diagnostic error files are not summed separately. Legacy logs without system metadata are treated as `zeroShot`.

`auditBenchmark.py` separately checks the HS templates as material propositional implications using exhaustive truth tables, preserving the original labels:
```bash
uv run auditBenchmark.py HS_HF_PR_500 --model openai/gpt-4o-mini --output summaries/HS_HF_PR_500_label_audit.json
```
Both evaluators only recognize normalized `yes`/`no` responses. Additional explanation text is counted separately as unrecognized; it is not a semantic judgment of that explanation. See `CORRIDAS.md` and `PENDIENTES.md` for the actual runs and dataset/format issues.

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
