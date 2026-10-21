import tempfile
import unittest
from pathlib import Path

from file_benchmark import build_graph, closure, execute, one_trial, outputs, write_inputs

ROOT = Path(__file__).parent / ".file-benchmark-tests"
ROOT.mkdir(exist_ok=True)


def temporary_workspace():
    return tempfile.TemporaryDirectory(dir=ROOT)


class FileBenchmarkTests(unittest.TestCase):
    def test_complete_declared_graph_is_correct(self):
        with temporary_workspace() as temporary:
            rows = one_trial(7, 32, 3, 0.0, Path(temporary))
        self.assertTrue(all(row["stale"] == 0 for row in rows))

    def test_missing_dependencies_can_preserve_stale_output(self):
        actual, _, _ = build_graph(2, 64, 3, 0.0)
        self.assertEqual(len(actual), 64)
        self.assertEqual(closure([[], [0], [1]], {0}), {0, 1, 2})

    def test_real_output_changes_after_input_change(self):
        with temporary_workspace() as temporary:
            root = Path(temporary)
            graph = [[], [0], [1]]
            write_inputs(root, 3)
            before, _, _ = execute(root, graph, None, None, "before")
            write_inputs(root, 3, changed=0)
            after, _, _ = execute(root, graph, None, None, "after")
            self.assertNotEqual(outputs(before, 3), outputs(after, 3))

    def test_trial_is_structured(self):
        with temporary_workspace() as temporary:
            rows = one_trial(3, 16, 1, 0.2, Path(temporary))
        self.assertEqual({r["policy"] for r in rows}, {"full", "transitive", "audit-0.02", "audit-0.10"})
        self.assertTrue(all(r["elapsed_seconds"] >= 0 for r in rows))
