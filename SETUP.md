# SupportLens conversation evaluation

This update adds evaluation files only. It does not replace application code or your README.

## Install

Merge the included `src`, `evaluation`, and `tests` folders into the root of your
existing SupportLens project. Keep all existing files. No new packages are needed.

The runner calls the already-running API over HTTP, so it does not load another
embedding model. Keep the API running in one terminal and use a second terminal
for evaluation. Do not submit browser questions during a run: the local API allows
only one active question at a time.

## Start small

In terminal 1, with the project environment activated:

```powershell
python -m uvicorn api:app --app-dir src --host 127.0.0.1 --port 8000 --workers 1
```

In terminal 2, from the project root:

```powershell
python -u src\evaluate_conversations.py
```

The default runs only `smoke`: one question, normally two hosted calls for generation
and verification. Report files are saved in a unique `evaluation/runs/<run-id>/` folder.

Next run a real three-turn conversation (up to eight hosted calls):

```powershell
python -u src\evaluate_conversations.py --case account_followup
```

Useful commands:

```powershell
python src\evaluate_conversations.py --list
python src\evaluate_conversations.py --all --dry-run
python -u src\evaluate_conversations.py --case topic_switch
python -u src\evaluate_conversations.py --case misleading_history
```

Only after small runs work, consider the complete development set:

```powershell
python -u src\evaluate_conversations.py --all --note "Groq openai/gpt-oss-20b; current local configuration"
```

The complete set has eight scenarios and 15 turns, with up to 37 hosted calls in
the current pipeline (excluding any SDK retry behavior). Actual usage is lower
when clarification or insufficient evidence skips verification. The runner sends
no retries and stops the full run on an HTTP, network, parsing, or processing error.
If quota is limited, run scenarios separately later; do not repeatedly retry 429s.
The `--note` value is user-supplied metadata, not a verified server configuration.

## Read the reports

- `results.json`: questions, actual history sent, expected labels, returned answers,
  checks, per-request elapsed time, and human-review fields.
- `summary.md`: counts, denominators, latency summary, and review instructions.

Files are updated after every attempted turn. A processing error remains an error,
not an answer-quality failure, and unattempted turns are counted separately.
A withheld or invalid response skips dependent turns in that scenario; later
independent scenarios can still run. No expected answer is inserted into history.

An automated PASS means that the returned status, structural citation consistency,
expected source overlap (when applicable), and display gate meet this test's contract.
It does NOT establish factual accuracy, completeness, retrieval recall, or semantic
support. Source metadata in the API response is checked for consistency; the runner
does not independently inspect the retriever's candidate set.

The model's `supported` verdict is recorded, not used as human ground truth. For each
turn, read the expected.review guidance and the actual response. Fill in the
human_review.correct and human_review.notes fields in the completed JSON report if
you want to retain your review. Do not edit reports while the runner is writing them.
The summary deliberately does not calculate an answer-accuracy percentage.

For non-answers, check that clarification is useful and that abstention is warranted.
For answers, check every assertion and whether it actually answers the user's intent.
An answer with the correct source ID can still be wrong.

Latency is wall-clock HTTP request time, including server processing and provider
waiting. Server startup/model loading are excluded. The first request may include
cold inference overhead. Model requests and token consumption are not measured;
the startup call estimate is only a planning upper bound for the current pipeline.

The corpus labels assume the current seven fictional support documents. Revise labels
if the documents change. Some examples repeat earlier manual tests, so this is a
small development regression set, not a held-out benchmark. Keep a separate unseen
set before making generalization claims.

Scenario isolation tests fresh API history; it does not automate the browser's New
chat button. The frontend reset behavior still needs its separate manual check.

## Offline tests

```powershell
python -m unittest discover -s tests -p test_conversation_evaluation.py -v
```

Twelve tests were run during preparation. They check actual-reply history propagation,
scenario isolation, history bounds, withholding, error accounting, and response checks.
These use mock API responses and do not call Groq. The full live application was not
available during preparation, so live evaluation remains to be run locally.

## Version control

Keep source and test data in git. Review generated reports before committing them:
they contain conversation text. Add `evaluation/runs/` to .gitignore if you want
local runs excluded by default; publish only selected reviewed reports later.

Suggested commit after the smoke and follow-up runs work:

```powershell
git add src/evaluate_conversations.py evaluation/conversations.json tests/test_conversation_evaluation.py
git commit -m "Add conversation regression evaluation with saved reports"
git push
```
