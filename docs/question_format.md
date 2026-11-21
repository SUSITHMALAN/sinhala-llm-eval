# Benchmark question format (proposal v0.1)

One JSON object per line (UTF-8 JSONL). This file documents
`src/lankallm/benchmark/schema.py`; if the two disagree, the code is wrong or this
page is out of date. **Any change must be agreed by both team members.**

| Field | Required | Values / notes |
|---|---|---|
| `question_id` | yes | Unique, e.g. `si-fact-001` |
| `language` | yes | `si` or `ta` |
| `category` | yes | `factual`, `hallucination`, `bias`, `safety`, `language_understanding` |
| `subcategory` | no | Free text, e.g. `history`, `false_premise`, `code_mixed` |
| `question` | yes | The prompt text, NFC-normalised |
| `expected_answer` | factual / reference_match | Reference answer |
| `evidence` | factual | Source (URL or citation) for the reference answer |
| `difficulty` | yes | `easy`, `medium`, `difficult` |
| `evaluation_method` | yes | `reference_match`, `premise_check`, `refusal_check`, `human_rubric` |
| `split` | no (default `dev`) | `dev` or `test` (test items stay private) |
| `benchmark_version` | yes | e.g. `0.1` |
| `annotator_ids` | no | Anonymous IDs such as `A1` |
| `is_placeholder` | no | `true` until native-speaker review is complete |
| `notes` | no | Free text |

Unknown fields are rejected so typos are caught early.

## Check a file

```powershell
uv run lankallm benchmark validate data/benchmark/v0.1/questions.jsonl
```

The command lists every problem with its line number or question ID, prints a
Sinhala/Tamil balance table per category, and exits non-zero if anything is wrong.
