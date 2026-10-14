import unittest
import run_i3_03_01_bound_diagnostic as d


def case(sequence, order_q, order_motion, order_n, utilities, ref=10):
    orders={'Q':order_q,'motion':order_motion,'N':order_n}
    return {'accepted':True,'sequence':sequence,'positive_records':[i for i,u in utilities.items() if u>ref+d.TOL],
            'first_positive':{n:d.first_positive(o,utilities,ref) for n,o in orders.items()},
            'curves':{n:{'K1':d.curve(o,utilities,ref,1),'K2':d.curve(o,utilities,ref,2)} for n,o in orders.items()}}


class DiagnosticDecision(unittest.TestCase):
    def test_reference_fallback_empty_and_zero(self):
        self.assertEqual(d.curve([],{},10,1)['effective_utility'],10)
        self.assertEqual(d.curve([1],{1:8},10,1)['relative_utility'],0)
        self.assertIsNone(d.curve([1],{1:1},0,1)['relative_utility'])

    def test_secondary_all_pool_cannot_rescue_primary(self):
        c=case(26,[1,2],[1,2],[1,2],{1:8,2:12})
        self.assertGreater(c['curves']['Q']['K2']['effective_utility'],10)
        self.assertFalse(d.quality([c]*5)['passed'])

    def test_wins_against_both_and_late_positive_veto(self):
        good=case(26,[2,1],[1,2],[1,2],{1:8,2:12})
        empty=case(1,[],[],[],{})
        self.assertTrue(d.quality([good]+[empty]*4)['passed'])
        late=case(38,[3,1,2],[1,2,3],[1,2,3],{1:11,2:10,3:9})
        self.assertFalse(d.quality([good,late]+[empty]*3)['no_later_than_motion'])

    def test_no_silent_zero_reference_exclusion(self):
        good=case(26,[2,1],[1,2],[1,2],{1:8,2:12})
        zero=case(1,[],[],[],{},0)
        metrics=d.quality([good]*4+[zero])
        self.assertFalse(metrics['evaluable'])
        self.assertEqual(d.outcome(True,True,metrics),'INCONCLUSIVE_QUALITY_METRICS')

    def test_independent_resource_and_engineering_gate(self):
        metrics={'evaluable':True,'passed':True}
        self.assertEqual(d.outcome(False,True,metrics),'BOUND_ENGINEERING_FAIL')
        self.assertEqual(d.outcome(True,False,metrics),'BOUND_PREPARATION_FAIL')
        self.assertEqual(d.outcome(True,True,metrics),'DIAGNOSTIC_SIGNAL_ONLY')


if __name__=='__main__':
    unittest.main()
