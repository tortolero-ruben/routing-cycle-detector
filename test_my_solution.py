#!/usr/bin/env python3
"""
Unit tests for my_solution.py. Covers find_longest_cycle, run_unsorted, run_sorted, and CLI.
Edge cases: empty input, single edge, self-loops, ties, malformed lines, deterministic output.
"""
import io
import tempfile
import unittest
import os

# Import after potential path setup; run from project root: python -m pytest test_my_solution.py
# or: python -m unittest test_my_solution
from my_solution import (
    find_longest_cycle,
    run_unsorted,
    run_sorted,
    run_sorted_stream,
)


class TestFindLongestCycle(unittest.TestCase):
    """Tests for find_longest_cycle() in isolation. Edges are (src_int, dst_int)."""

    def test_empty_edges(self):
        self.assertEqual(find_longest_cycle([]), 0)

    def test_single_edge_no_cycle(self):
        """One edge A→B: no path back to A."""
        self.assertEqual(find_longest_cycle([(0, 1)]), 0)

    def test_self_loop(self):
        """Self-loop A→A: should count as cycle length = 1."""
        self.assertEqual(find_longest_cycle([(0, 0)]), 1)

    def test_two_node_cycle(self):
        """A→B, B→A → cycle length 2."""
        self.assertEqual(find_longest_cycle([(0, 1), (1, 0)]), 2)

    def test_three_node_cycle(self):
        """A→B, B→C, C→A → cycle length 3."""
        self.assertEqual(find_longest_cycle([(0, 1), (1, 2), (2, 0)]), 3)

    def test_chain_no_cycle(self):
        """A→B→C→D: no cycle."""
        self.assertEqual(find_longest_cycle([(0, 1), (1, 2), (2, 3)]), 0)

    def test_multiple_cycles_same_graph(self):
        """Graph has both 2-cycle and 3-cycle; longest wins."""
        edges = [(0, 1), (1, 0), (0, 2), (2, 3), (3, 0)]
        self.assertEqual(find_longest_cycle(edges), 3)

    def test_duplicate_edges(self):
        """Duplicate edges (same edge twice) still form one 2-cycle."""
        self.assertEqual(find_longest_cycle([(0, 1), (1, 0), (0, 1)]), 2)

    def test_four_node_cycle(self):
        """A→B→C→D→A → 4."""
        self.assertEqual(
            find_longest_cycle([(0, 1), (1, 2), (2, 3), (3, 0)]), 4
        )

    def test_tree_no_cycle(self):
        """Tree: no back edge."""
        self.assertEqual(
            find_longest_cycle([(0, 1), (0, 2), (1, 3), (2, 4)]), 0
        )


class TestRunUnsorted(unittest.TestCase):
    """Tests for run_unsorted() with temp files."""

    def _write_and_run(self, content):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            return run_unsorted(path)
        finally:
            os.unlink(path)

    def test_empty_file(self):
        key, length = self._write_and_run("")
        self.assertIsNone(key)
        self.assertEqual(length, 0)

    def test_single_line_one_edge(self):
        """One group, one edge: no cycle."""
        key, length = self._write_and_run("A|B|1|2\n")
        self.assertIsNone(key)
        self.assertEqual(length, 0)

    def test_single_line_self_loop(self):
        """A|A|1|2: self-loop counts as cycle length 1."""
        key, length = self._write_and_run("A|A|1|2\n")
        self.assertEqual(key, ("1", "2"))
        self.assertEqual(length, 1)

    def test_two_line_two_cycle(self):
        """Same group, 2-cycle → output that group with length 2."""
        key, length = self._write_and_run("A|B|99|88\nB|A|99|88\n")
        self.assertEqual(key, ("99", "88"))
        self.assertEqual(length, 2)

    def test_spec_example(self):
        """Spec example: longest cycle is 123,197 with length 3."""
        content = """Epic|Availity|123|197
Availity|Optum|123|197
Optum|Epic|123|197
Epic|Availity|891|45
Availity|Epic|891|45
"""
        key, length = self._write_and_run(content)
        self.assertEqual(key, ("123", "197"))
        self.assertEqual(length, 3)

    def test_tie_lexicographic_smallest_wins(self):
        """Two groups both have cycle length 2; (a,1) < (b,1) so (a,1) wins."""
        content = "X|Y|a|1\nY|X|a|1\nX|Y|b|1\nY|X|b|1\n"
        key, length = self._write_and_run(content)
        self.assertEqual(key, ("a", "1"))
        self.assertEqual(length, 2)

    def test_malformed_line_skipped(self):
        """Line with wrong field count is skipped; valid lines still processed."""
        content = "A|B|1|2\nbad\nC|D|1|2\nD|C|1|2\n"
        key, length = self._write_and_run(content)
        self.assertEqual(key, ("1", "2"))
        self.assertEqual(length, 2)

    def test_empty_lines_skipped(self):
        content = "\n\nA|B|1|2\n\nB|A|1|2\n\n"
        key, length = self._write_and_run(content)
        self.assertEqual(key, ("1", "2"))
        self.assertEqual(length, 2)

    def test_longest_wins(self):
        """One group with length 2, one with length 3; length 3 wins."""
        content = (
            "A|B|g1|s1\nB|A|g1|s1\n"
            "P|Q|g2|s2\nQ|R|g2|s2\nR|P|g2|s2\n"
        )
        key, length = self._write_and_run(content)
        self.assertEqual(key, ("g2", "s2"))
        self.assertEqual(length, 3)


class TestRunSortedStream(unittest.TestCase):
    """Tests for run_sorted_stream() with StringIO (sorted input)."""

    def test_empty(self):
        key, length = run_sorted_stream(io.StringIO(""))
        self.assertIsNone(key)
        self.assertEqual(length, 0)

    def test_spec_example_sorted(self):
        """Same as spec but lines sorted by (claim_id, status_code)."""
        content = """Epic|Availity|123|197
Availity|Optum|123|197
Optum|Epic|123|197
Availity|Epic|891|45
Epic|Availity|891|45
"""
        key, length = run_sorted_stream(io.StringIO(content))
        self.assertEqual(key, ("123", "197"))
        self.assertEqual(length, 3)

    def test_tie_lexicographic(self):
        """Sorted order: (a,1) then (b,1). Both length 2; (a,1) wins."""
        content = "X|Y|a|1\nY|X|a|1\nX|Y|b|1\nY|X|b|1\n"
        key, length = run_sorted_stream(io.StringIO(content))
        self.assertEqual(key, ("a", "1"))
        self.assertEqual(length, 2)


class TestSortedVsUnsortedSameResult(unittest.TestCase):
    """Unsorted and sorted mode must produce the same result (deterministic tie-break)."""

    def test_same_content_same_output(self):
        content = """Epic|Availity|123|197
Availity|Optum|123|197
Optum|Epic|123|197
Epic|Availity|891|45
Availity|Epic|891|45
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            u_key, u_len = run_unsorted(path)
            sorted_lines = sorted(
                [L for L in content.strip().split("\n") if L],
                key=lambda L: (L.split("|")[2], L.split("|")[3]),
            )
            s_key, s_len = run_sorted_stream(io.StringIO("\n".join(sorted_lines) + "\n"))
            self.assertEqual(u_key, s_key)
            self.assertEqual(u_len, s_len)
        finally:
            os.unlink(path)


class TestCLI(unittest.TestCase):
    """CLI output format: claim_id,status_code,cycle_length."""

    def test_cli_spec_example(self):
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Epic|Availity|123|197\nAvaility|Optum|123|197\nOptum|Epic|123|197\nEpic|Availity|891|45\nAvaility|Epic|891|45\n")
            path = f.name
        try:
            out = subprocess.check_output(
                [os.environ.get("PYTHON", "python3"), "my_solution.py", path],
                cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            self.assertEqual(out, "123,197,3")
        finally:
            os.unlink(path)

    def test_cli_sorted_stdin(self):
        """sort ... | python3 my_solution.py --sorted - produces same as unsorted on same data."""
        import subprocess
        content = "A|B|1|2\nB|A|1|2\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            unsorted_out = subprocess.check_output(
                [os.environ.get("PYTHON", "python3"), "my_solution.py", path],
                cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            sorted_out = subprocess.check_output(
                [os.environ.get("PYTHON", "python3"), "my_solution.py", "--sorted", "-"],
                input=content,
                cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            self.assertEqual(unsorted_out, sorted_out)
            self.assertEqual(unsorted_out, "1,2,2")
        finally:
            os.unlink(path)

    def test_cli_empty_file(self):
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            path = f.name
        try:
            out = subprocess.check_output(
                [os.environ.get("PYTHON", "python3"), "my_solution.py", path],
                cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            self.assertEqual(out, "0,0,0")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
