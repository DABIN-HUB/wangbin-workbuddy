# Confirmed rules input

The assistant extracts actual source columns from the user's file and target columns from the supplied template or explicit field description, asks about conflicts, then writes an UTF-8 JSON rule file. Do not require the end user to produce JSON. Each `fields` key is a target field. `sources` lists candidate original headers; more than one existing header for one target remains pending. Specify `rule_source` and `rule_id`; omitted required means UNKNOWN, not false. Only explicitly confirmed constraints should appear.

```json
{"fields":{"customer_code":{"sources":["customer_code"],"rule_id":"CODE","rule_source":"confirmed template","required":true,"data_type":"text","unique_group":"customer_code"},"customer_name":{"sources":["customer_name"],"rule_id":"NAME","rule_source":"confirmed template","required":true},"region":{"sources":["region"],"rule_id":"REGION","rule_source":"confirmed reference rule","reference_key":"region"}}}
```

`data_type` supports `text` or `date`; for date pass Python `strptime` format under `date_format`, e.g. `%Y-%m-%d`, only once confirmed. `min_length`, `max_length`, `allowed_values`, and `unique_group` are optional. For a composite key use the same `unique_group` on every key field; missing members are not comparable. Reference table is separately supplied by `--reference`, and must contain `reference_key` column. No target file means omit `--rules` and report unknown target constraints. No row is silently deleted; `--split` requires explicit consent and leaves an isolation file.

Each invocation is a fresh run: preserve old report, supply updated rules/reference file and compare row IDs and finding categories. Files should be located in a user-authorized directory, never inferred by recursive traversal. Local script does not verify file ownership or WorkBuddy host capabilities.
