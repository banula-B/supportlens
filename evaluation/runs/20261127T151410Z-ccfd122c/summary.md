# Conversation development checks

Automated passes measure response contracts, not answer accuracy.

Run state: stopped_on_error

| Metric | Value |
|---|---|
| planned_turns | 11 |
| attempted_turns | 5 |
| unattempted_turns | 6 |
| processing_errors | 1 |
| completed_responses | 4 |
| status_matches | 4 |
| status_evaluated | 4 |
| structural_checks_passed | 4 |
| structural_checks_evaluated | 4 |
| answered_responses | 4 |
| answered_with_supported_verdict | 4 |
| withheld_responses | 0 |
| automated_contract_passes | 4 |
| contract_evaluated | 4 |
| mean_completed_latency_seconds | 1.389 |
| median_completed_latency_seconds | 1.302 |
| human_accuracy_review | pending; no automatic accuracy score |

## Manual review

Read results.json for actual histories, complete responses and per-turn review criteria.
Check factual correctness, completeness, intent preservation and appropriate abstention.
The model verifier is not independent ground truth. Human review fields start as null.
