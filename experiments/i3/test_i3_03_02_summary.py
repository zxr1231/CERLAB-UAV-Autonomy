import unittest
from summarize_i3_03_02 import comparison,effective,passes,verdict


class FinalDecision(unittest.TestCase):
    def test_fallback_and_equal_actual_scores(self):
        t={'complete':True,'routes':[{'exact':{'valid':True,'utility':9}},{'exact':{'valid':True,'utility':15}}]}
        self.assertEqual(effective(t,10,1),10)
        self.assertEqual(effective(t,10,2),15)
        t['complete']=False;self.assertEqual(effective(t,10),10)

    def test_paired_loss_not_hidden_by_reference_improvement(self):
        rows=[{'reference_utility':10,'equal_count':{'3':11,'1':12}},{'reference_utility':10,'equal_count':{'3':10,'1':10}}]
        c=comparison(rows,1);self.assertEqual(c['losses'],1);self.assertLess(c['mean_absolute_delta'],0);self.assertFalse(passes(c))

    def test_zero_denominator_and_two_wins(self):
        rows=[{'reference_utility':0,'equal_count':{'3':2,'1':1}},{'reference_utility':0,'equal_count':{'3':3,'1':2}}]
        c=comparison(rows,1);self.assertIsNone(c['mean_relative_delta_to_reference']);self.assertTrue(passes(c))
        self.assertFalse(passes(comparison(rows[:1],1)))

    def test_value_without_runtime_is_partial_only(self):
        self.assertEqual(verdict(True,True,False),'PARTIAL_SUPPORT_OFFLINE_VALUE_ONLY')
        self.assertEqual(verdict(True,False,True),'METHOD_NOT_SUPPORTED')
        self.assertEqual(verdict(False,True,True),'EVIDENCE_INSUFFICIENT_ENGINEERING_FAILURE')


if __name__=='__main__':unittest.main()
