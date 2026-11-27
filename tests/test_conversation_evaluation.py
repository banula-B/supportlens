import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from evaluate_conversations import inspect_response, load_cases, run


def response(status='answered', text='No. [doc-005]', ids=None):
    ids = ['doc-005'] if ids is None else ids
    return {'withheld':False, 'answer':{'status':status,'answer':text,'citation_ids':ids},
            'verification_status':'supported' if status == 'answered' else 'not_checked',
            'sources':[{'id':i,'title':'Test','source':'demo://test'} for i in ids]}


def turn(question='Question', status='answered', ids=None):
    return {'question':question,'expected_status':status,
            'acceptable_citation_ids':['doc-005'] if ids is None else ids,'review':'Review meaning.'}


class EvaluationTests(unittest.TestCase):
    def test_valid_answer_contract(self):
        self.assertTrue(inspect_response(response(), turn())['contract_pass'])

    def test_missing_inline_citation_fails(self):
        self.assertFalse(inspect_response(response(text='No.'), turn())['structural_ok'])

    def test_missing_source_fails(self):
        data = response(); data['sources'] = []
        self.assertFalse(inspect_response(data, turn())['structural_ok'])

    def test_wrong_labeled_source_fails(self):
        data = response(text='Claim [doc-003]', ids=['doc-003'])
        checks = inspect_response(data, turn())
        self.assertTrue(checks['structural_ok'])
        self.assertFalse(checks['contract_pass'])

    def test_nonanswer_not_claim_verified(self):
        data = response('insufficient_evidence', 'Not specified.', [])
        self.assertTrue(inspect_response(data, turn(status='insufficient_evidence', ids=[]))['contract_pass'])

    def test_withheld_draft_leak_fails(self):
        data = response(); data['withheld'] = True
        self.assertFalse(inspect_response(data, turn())['structural_ok'])

    def test_unsupported_verdict_cannot_pass(self):
        data = response(); data['verification_status'] = 'unsupported'
        self.assertFalse(inspect_response(data, turn())['contract_pass'])

    def run_fixture(self, cases, side_effect):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        args = argparse.Namespace(output=Path(temporary.name),note='offline mock',url='http://localhost',timeout=1)
        with patch('evaluate_conversations.request_answer', side_effect=side_effect) as request:
            report, folder = run(cases, 'test-hash', args)
        self.assertTrue((folder / 'results.json').exists())
        return report, request

    def test_actual_replies_and_scenario_isolation(self):
        cases = [{'id':'one','category':'test','turns':[turn('First'),turn('Follow up')]},
                 {'id':'two','category':'test','turns':[turn('New chat')]}]
        captured=[]
        def fake(url,q,history,timeout):
            captured.append(json.loads(json.dumps(history)))
            return response(text='Actual generated content. [doc-005]')
        report, _ = self.run_fixture(cases, fake)
        self.assertEqual(captured[0], [])
        self.assertEqual(captured[1][1]['content'], 'Actual generated content. [doc-005]')
        self.assertEqual(captured[2], [])
        self.assertEqual(report['summary']['automated_contract_passes'], 3)

    def test_error_stops_without_false_denominator(self):
        cases=[{'id':'one','category':'test','turns':[turn(),turn()]}]
        report, request = self.run_fixture(cases, HTTPError('http://localhost',429,'quota',{},None))
        self.assertEqual(request.call_count,1)
        self.assertEqual(report['summary']['status_evaluated'],0)
        self.assertEqual(report['summary']['processing_errors'],1)
        self.assertEqual(report['summary']['unattempted_turns'],1)

    def test_withheld_skips_dependent_turn(self):
        cases=[{'id':'one','category':'test','turns':[turn(),turn()]}]
        report, request = self.run_fixture(cases, lambda *args: {
            'withheld':True,'answer':None,'sources':[],'verification_status':'uncertain'})
        self.assertEqual(request.call_count,1)
        self.assertEqual(report['summary']['withheld_responses'],1)
        self.assertEqual(report['summary']['status_evaluated'],0)

    def test_history_is_bounded(self):
        cases=[{'id':'one','category':'test','turns':[turn(str(i)) for i in range(6)]}]
        lengths=[]
        def fake(url,q,history,timeout):
            lengths.append(len(history)); return response()
        self.run_fixture(cases,fake)
        self.assertEqual(lengths,[0,2,4,6,8,8])

    def test_dataset_loads(self):
        path=Path(__file__).resolve().parents[1]/'evaluation'/'conversations.json'
        cases, digest=load_cases(path)
        self.assertEqual(len(cases),8)
        self.assertEqual(len(digest),64)


if __name__ == '__main__':
    unittest.main()
