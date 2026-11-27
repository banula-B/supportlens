"""Evaluate the running SupportLens API using only the Python standard library."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {'answered', 'clarification_needed', 'insufficient_evidence'}


def load_cases(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    cases = data['cases']
    ids = set()
    for case in cases:
        if not case['id'] or case['id'] in ids or not case['turns']:
            raise ValueError('Scenario IDs must be unique and turns nonempty.')
        ids.add(case['id'])
        for turn in case['turns']:
            if turn['expected_status'] not in STATUSES:
                raise ValueError('Invalid expected status.')
            if not isinstance(turn['question'], str) or not turn['question'].strip():
                raise ValueError('Question cannot be blank.')
            if len(turn['question']) > 2000:
                raise ValueError('Question exceeds the API limit.')
            if not isinstance(turn['acceptable_citation_ids'], list):
                raise ValueError('Citation labels must be a list.')
    return cases, hashlib.sha256(raw).hexdigest()


def request_answer(base_url, question, history, timeout):
    # Only questions and actual prior responses reach the service: no labels.
    payload = json.dumps({'question': question, 'history': history}).encode('utf-8')
    request = Request(base_url.rstrip('/') + '/ask', data=payload,
                      headers={'Content-Type': 'application/json'}, method='POST')
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def inspect_response(data, expected):
    if not isinstance(data, dict) or type(data.get('withheld')) is not bool:
        raise ValueError('Malformed API response.')
    withheld = data['withheld']
    answer = data.get('answer')
    sources = data.get('sources')
    verification = data.get('verification_status')
    if not isinstance(sources, list):
        raise ValueError('Malformed source list.')
    if withheld:
        return dict(actual_status=None, status_match=None,
                    structural_ok=answer is None and sources == [],
                    citation_label_match=None,
                    display_gate_ok=answer is None and verification in {'unsupported', 'uncertain'},
                    contract_pass=False)
    if not isinstance(answer, dict) or answer.get('status') not in STATUSES:
        raise ValueError('Malformed answer.')
    text = answer.get('answer')
    ids = answer.get('citation_ids')
    if not isinstance(text, str) or not text.strip() or not isinstance(ids, list):
        raise ValueError('Malformed answer content.')
    if any(not isinstance(i, str) for i in ids):
        raise ValueError('Malformed citation IDs.')
    if any(not isinstance(s, dict) or not isinstance(s.get('id'), str) for s in sources):
        raise ValueError('Malformed sources.')
    inline = set(re.findall(r'\[(doc-[^\]\s]+)\]', text))
    declared = set(ids)
    source_ids = {s['id'] for s in sources}
    status = answer['status']
    structural = inline == declared == source_ids
    structural = structural and (bool(declared) if status == 'answered' else not declared)
    gate = verification == ('supported' if status == 'answered' else 'not_checked')
    label_match = None
    if expected['acceptable_citation_ids'] and status == 'answered':
        label_match = bool(declared & set(expected['acceptable_citation_ids']))
    match = status == expected['expected_status']
    return dict(actual_status=status, status_match=match, structural_ok=structural,
                citation_label_match=label_match, display_gate_ok=gate,
                contract_pass=match and structural and gate and label_match is not False)


def summarize(report):
    rows = report['turns']
    completed = [r for r in rows if 'checks' in r]
    statuses = [r for r in completed if r['checks']['status_match'] is not None]
    answered = [r for r in completed if r['checks']['actual_status'] == 'answered']
    latencies = [r['latency_seconds'] for r in completed]
    return {
        'planned_turns': report['planned_turns'], 'attempted_turns': len(rows),
        'unattempted_turns': report['planned_turns'] - len(rows),
        'processing_errors': sum('error' in r for r in rows),
        'completed_responses': len(completed),
        'status_matches': sum(r['checks']['status_match'] for r in statuses),
        'status_evaluated': len(statuses),
        'structural_checks_passed': sum(r['checks']['structural_ok'] for r in completed),
        'structural_checks_evaluated': len(completed),
        'answered_responses': len(answered),
        'answered_with_supported_verdict': sum(r['response']['verification_status'] == 'supported' for r in answered),
        'withheld_responses': sum(r['response']['withheld'] for r in completed),
        'automated_contract_passes': sum(r['checks']['contract_pass'] for r in completed),
        'contract_evaluated': len(completed),
        'mean_completed_latency_seconds': round(statistics.mean(latencies), 3) if latencies else None,
        'median_completed_latency_seconds': round(statistics.median(latencies), 3) if latencies else None,
        'human_accuracy_review': 'pending; no automatic accuracy score',
    }


def save_report(report, folder):
    folder.mkdir(parents=True, exist_ok=True)
    report['summary'] = summarize(report)
    target = folder / 'results.json'
    temporary = folder / 'results.tmp'
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(target)
    lines = ['# Conversation development checks', '',
             'Automated passes measure response contracts, not answer accuracy.', '',
             f"Run state: {report['state']}", '', '| Metric | Value |', '|---|---|']
    lines += [f'| {key} | {value} |' for key, value in report['summary'].items()]
    lines += ['', '## Manual review', '',
              'Read results.json for actual histories, complete responses and per-turn review criteria.',
              'Check factual correctness, completeness, intent preservation and appropriate abstention.',
              'The model verifier is not independent ground truth. Human review fields start as null.', '']
    (folder / 'summary.md').write_text('\n'.join(lines), encoding='utf-8')


def run(cases, digest, args):
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    folder = args.output / run_id
    report = dict(run_id=run_id, dataset_sha256=digest, state='running',
                  configuration_note=args.note,
                  history_policy='Last 8 messages from successful displayed exchanges; reset per scenario.',
                  planned_turns=sum(len(c['turns']) for c in cases),
                  selected_scenarios=[c['id'] for c in cases], turns=[])
    save_report(report, folder)
    try:
        for case in cases:
            history = []
            for index, expected in enumerate(case['turns'], 1):
                print(f"\n[{case['id']} / turn {index}] {expected['question']}", flush=True)
                row = dict(scenario=case['id'], turn=index, category=case['category'],
                           question=expected['question'], history_sent=list(history),
                           expected=expected, human_review={'correct': None, 'notes': ''})
                start = time.perf_counter()
                try:
                    data = request_answer(args.url, expected['question'], history, args.timeout)
                    row['response'] = data
                    row['checks'] = inspect_response(data, expected)
                except (Exception, KeyboardInterrupt) as error:
                    # Do not write provider bodies, environment variables or exception strings.
                    row['error'] = {'type': type(error).__name__}
                    if isinstance(error, HTTPError):
                        row['error']['http_status'] = error.code
                    row['latency_seconds'] = round(time.perf_counter() - start, 3)
                    report['turns'].append(row)
                    report['state'] = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'stopped_on_error'
                    save_report(report, folder)
                    print(f"Stopped: {row['error']}. No retry was sent.", flush=True)
                    return report, folder
                row['latency_seconds'] = round(time.perf_counter() - start, 3)
                report['turns'].append(row)
                checks = row['checks']
                print(f"Expected: {expected['expected_status']} | Actual: {checks['actual_status']}", flush=True)
                print(f"Automated contract: {'PASS' if checks['contract_pass'] else 'FAIL'} | {row['latency_seconds']:.2f}s", flush=True)
                save_report(report, folder)
                # Match the browser: withheld or structurally unsafe responses never enter context.
                if (not data['withheld'] and checks['structural_ok'] and checks['display_gate_ok']):
                    text = data['answer']['answer']
                    if len(text) <= 4000:
                        history.extend([{'role':'user','content':expected['question']},
                                        {'role':'assistant','content':text}])
                        history = history[-8:]
                    else:
                        history = []
                else:
                    # Later turns depend on this exchange. Mark them unattempted rather than
                    # fabricate a successful answer or evaluate a broken conversation.
                    break
        report['state'] = 'complete' if len(report['turns']) == report['planned_turns'] else 'complete_with_skipped_turns'
    finally:
        save_report(report, folder)
    return report, folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'evaluation' / 'conversations.json')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--case', action='append', dest='case_ids', help='Scenario ID; repeat to select several.')
    selection.add_argument('--all', action='store_true', help='Run all scenarios; consumes API quota.')
    parser.add_argument('--list', action='store_true', help='List scenarios without making requests.')
    parser.add_argument('--dry-run', action='store_true', help='Show selected scope without requests.')
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--timeout', type=float, default=210)
    parser.add_argument('--output', type=Path, default=ROOT / 'evaluation' / 'runs')
    parser.add_argument('--note', default='', help='Optional model/configuration note; never include secrets.')
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('Timeout must be positive.')
    url = urlsplit(args.url)
    if url.scheme not in {'http','https'} or not url.hostname or url.username or url.password or url.query or url.fragment:
        parser.error('Use an HTTP(S) base URL without credentials, query or fragment.')
    cases, digest = load_cases(args.dataset)
    if args.list:
        for case in cases:
            print(f"{case['id']}: {len(case['turns'])} turn(s), {case['category']}")
        return
    requested = args.case_ids or ['smoke']
    if not args.all and set(requested) - {c['id'] for c in cases}:
        parser.error('Unknown case ID. Use --list.')
    selected = cases if args.all else [c for c in cases if c['id'] in requested]
    count = sum(len(c['turns']) for c in selected)
    maximum = sum(2 + 3 * (len(c['turns']) - 1) for c in selected)
    print(f'Selected: {len(selected)} scenarios, {count} turns. Up to {maximum} hosted calls in the normal pipeline (no retries).')
    if args.dry_run:
        return
    report, folder = run(selected, digest, args)
    print('\n' + json.dumps(report['summary'], indent=2))
    print(f'\nSaved report: {folder.resolve()}')
    print('Automated passes do not establish answer accuracy. Review the saved answers.')
    if report['state'] != 'complete' or report['summary']['automated_contract_passes'] != count:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
