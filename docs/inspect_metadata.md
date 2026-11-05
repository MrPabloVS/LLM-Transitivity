# Inspect tags and metadata

The coverage pilot records three levels of information. Inspect supplies the
evaluation IDs, run IDs, timestamps, model configuration, transcripts, usage,
scores, and sample errors. Project metadata adds experimental context and source
provenance. The task display name includes the dataset and its pilot case count.

## Evaluation identity and runtime

All tasks in one Flow launch share an `experiment_run_id`. `experiment_id`
identifies the protocol across launches. Inspect's native IDs remain available.
The configuration creation time uses UTC; it is not the model request time.

Evaluation metadata records:

- Phase, protocol, metadata version, scorer version, and source-label basis.
- Git revision, branch, and dirty state. An original-data revision separately
  anchors the research inputs.
- Python, uv, platform, and direct runtime dependency versions.
- Hashes of project configuration and package Python sources,
  including the lockfile. A dirty Git revision alone does not identify the
  current code.
- Pilot manifest hash, selection method, cases per stratum, and pilot case count.
- Requested output limit, reasoning policy, fallback policy, caching, retry,
  timeout, concurrency, and omitted sampling parameters.

Metadata uses an allowlist. It does not copy environment variables, `.env`
contents, API keys, arbitrary command-line arguments, or authentication headers.

## Task labels

Native evaluation tags support filtering by project, experiment, phase, protocol,
model, model developer, requested provider, dataset, dataset family, frequency,
verbal time, connectors, generation group (`earlier` or `later`), and requested
reasoning policy. Each group contains one model per developer.

Task metadata also records the original, working, and pilot dataset paths and
hashes; source and pilot counts; source condition values; the system prompt hash;
and requested model and provider IDs. It preserves factory metadata when Flow
applies its overrides.

`requested_provider` is a configuration choice. `actual_provider` starts as null,
and `reasoning_verified` starts as false. These are not automatically certified
by a dry run or changed to success by a completed evaluation. Confirm them from
actual API responses and reported token usage during result review. A missing
reasoning token count is not proof of zero reasoning.

## Sample labels and provenance

Every sample records:

- A stable `sample_uid` shared across models, based on the working dataset,
  original row, and sentence hash. Native pilot sample IDs are original row numbers.
- The pilot dataset and row, working dataset, original file and row, and original
  source identifier. The original identifier can be a structured JSON value.
- Sentence hash and original and working record hashes.
- Dataset family, case type, frequency, verbal time, connectors, normalized
  source validity and canonical form, expected answer, and stratum ID.
- Raw original labels in `original_labels`, including the Spanish labels where
  present. Approved translations do not replace this provenance.
- Protocol, experiment ID, and explicit notice that logical validity is unaudited.

Samples have a `tags` list inside their metadata for frequency, tense, connectors,
source validity, and canonical form. This is sample metadata, not a native
sample-level tags field.

## Outputs and verification

Detailed sample logs and model API request/response snapshots are enabled.
Use native outputs for finish reasons, provider-reported usage, and raw response
details where supplied. Distinguish provider-reported charges from estimates;
this metadata layer does not calculate or certify billing.

The scorer records the raw answer, interpreted answer, expected answer, response
category, and format compliance. Inspect records execution errors separately.
The scoring rules and denominators remain documented in the README.

## OpenRouter details for each call

The bounded generation solver attaches `openrouter_http_calls` to each sample.
It restores capture context after success, error or cancellation, and isolates
concurrent samples.
It records every observed HTTP attempt through Inspect's SDK client, including
retry responses: request method, URL, headers, complete parsed JSON body,
HTTP status, response headers, complete parsed JSON response, UTC timestamps,
and measured HTTP duration. Non-JSON bodies are retained as decoded text.
Requests with no received response remain marked as such. Native Inspect errors
and retry events remain available separately.

All response fields are retained, including fields that our analysis does not
yet recognize. This includes choices, provider, usage and cost breakdowns,
token details, finish reasons, upstream metadata, and future extensions when
OpenRouter supplies them. Credentials and cookies are redacted. These are
structured application-level snapshots, not packet captures or byte-for-byte
copies of compressed HTTP traffic. Streaming is explicitly disabled for the pilot.

After generation, the collector fetches
[`GET /generation?id=...`](https://openrouter.ai/docs/api/api-reference/generations/get-request-&-usage-metadata-for-a-generation)
for every generation ID observed in captured responses, including retry IDs.
`openrouter_calls` preserves all lookup attempts, statuses, headers, complete
JSON, and lookup durations. Each lookup has a 15-second timeout and up to three
attempts for transient failures. It adds no new model generation, but adds
metadata requests and wall-clock time. Lookup failures do not replace the model
answer or fabricate usage. Samples that fail before the post-generation solver
can be enriched later through the exporter.

Generation details can include provider and upstream IDs, native and normalized
token counts, reasoning and cache tokens, total cost, provider responses, latency,
generation and moderation times, cancellation, region, service tier, BYOK, and
routing information. Missing values remain missing or null; zero remains zero.
Available fields depend on OpenRouter and the provider. Costs are preserved as
reported, not recalculated as certified billing. See
[usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting).

Export a run's `.eval` logs without additional API requests:

```sh
uv run --locked transitivity export results/pilot/<run-directory>
```

Refresh delayed or unavailable generation metadata with read-only API requests:

```sh
uv run --locked transitivity export results/pilot/<run-directory> --fetch
```

Exports retain the full native model events, project provenance, captured HTTP
attempts, errors, retries, and generation details, linked to evaluation IDs,
sample IDs, stable sample UIDs, and generation IDs. New JSON files are written
under `openrouter_calls/` in the run directory. Original logs and earlier
exports are preserved.

The optional `--fetch --include-stored-content` flags also query
[`GET /generation/content`](https://openrouter.ai/docs/api/api-reference/generations/get-stored-prompt-completion-and-error-content-for-a-generation).
That endpoint may require management-key permissions and previously stored
content. The exporter records denied access or unavailable content without
changing account retention settings or requesting broader credentials.

Tests mock the real OpenRouter SDK transport, force an HTTP 503 retry followed
by success, and verify capture of both responses, unknown fields, IDs, zero and
null values, generation lookups, export, and secret redaction. Other tests cover
delayed metadata, authorization failure, non-JSON responses, and network errors.

Tests run a real Flow evaluation with a local mock model, then read the `.eval`
file to check that evaluation tags, task metadata, and sample provenance survive
serialization. They also verify that a sentinel API key is absent from the
project metadata snapshot. This does not test any external model or provider.
