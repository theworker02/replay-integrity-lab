import unittest
from experiment import audited, closure, evaluate, trial

class ReplayTests(unittest.TestCase):
    def test_chain_requires_transitive_invalidation(self):
        graph = [[], [0], [1], []]
        self.assertEqual(closure(graph, {0}), {0,1,2})
        old = evaluate(graph, [0]*4)
        expected = evaluate(graph, [1,0,0,0])
        self.assertEqual(evaluate(graph, [1,0,0,0], old, {0,1,2}), expected)
        self.assertNotEqual(evaluate(graph, [1,0,0,0], old, {0,1}), expected)

    def test_audit_fallback(self):
        graph = [[], [0], [1]]
        stale = evaluate(graph, [0,0,0])
        result, work, detected = audited(graph, [1,0,0], stale, [2], 4, 1)
        self.assertTrue(detected)
        self.assertEqual(result, evaluate(graph, [1,0,0]))
        self.assertEqual(work, {0,1,2})

    def test_empty_cache_audit(self):
        expected = evaluate([[]], [1])
        self.assertEqual(audited([[]], [1], expected, [], 0, .1), (expected, set(), False))

    def test_complete_dependencies_across_seeds(self):
        for seed in range(100):
            for row in trial(seed, 32, 3, 0):
                if row['policy'] != 'direct':
                    self.assertEqual(row['stale'], 0)

    def test_repeatability(self):
        self.assertEqual(trial(4,64,3,.2), trial(4,64,3,.2))

    def test_full_replay_reference_with_missing_edges(self):
        for seed in range(20):
            row = trial(seed,64,3,.2)[0]
            self.assertEqual(row['stale'], 0)
            self.assertEqual(row['work'], 64)

if __name__ == '__main__':
    unittest.main()
