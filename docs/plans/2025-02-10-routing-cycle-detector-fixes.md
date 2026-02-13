# Routing Cycle Detector Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical and important bugs in the routing cycle detector solution identified during code review.

**Architecture:** The solution uses streaming input processing with two modes (sorted/unsorted). Per-group cycle detection uses DFS with backtracking. Fixes are localized to cycle detection logic, tie-breaking, and validation/warning code.

**Tech Stack:** Python 3, standard library only (collections, unittest, tempfile)

---

## Task 1: Fix Self-Loop Handling

**Issue:** Self-loops (A→A) are incorrectly excluded from being counted as cycles of length 1.

**Files:**
- Modify: `/Users/ruby/Documents/dev/thoughtfulai/my_solution.py:25`
- Modify: `/Users/ruby/Documents/dev/thoughtfulai/test_my_solution.py:32-33`

**Step 1: Update the cycle detection condition**

In `my_solution.py`, line 25, change from:
```python
if nb == start and len(visited) > 1:
```
to:
```python
if nb == start and len(visited) >= 1:
```

**Step 2: Run existing tests to verify expected failures**

Run: `python3 -m pytest test_my_solution.py::TestFindLongestCycle::test_self_loop -v`
Expected: FAIL - test expects 0 but will get 1

**Step 3: Update the self-loop test to expect correct behavior**

In `test_my_solution.py`, line 32-33, change from:
```python
def test_self_loop(self):
    """Self-loop A→A: current implementation does not count (visited size must be > 1)."""
    self.assertEqual(find_longest_cycle([(0, 0)]), 0)
```
to:
```python
def test_self_loop(self):
    """Self-loop A→A: counts as cycle length 1 per problem definition."""
    self.assertEqual(find_longest_cycle([(0, 0)]), 1)
```

**Step 4: Run self-loop test to verify it passes**

Run: `python3 -m pytest test_my_solution.py::TestFindLongestCycle::test_self_loop -v`
Expected: PASS

**Step 5: Update related test for self-loop in run_unsorted**

In `test_my_solution.py`, line 92-96, change from:
```python
def test_single_line_self_loop(self):
    """A|A|1|2: self-loop not counted as cycle by current impl."""
    key, length = self._write_and_run("A|A|1|2\n")
    self.assertIsNone(key)
    self.assertEqual(length, 0)
```
to:
```python
def test_single_line_self_loop(self):
    """A|A|1|2: self-loop counts as cycle length 1."""
    key, length = self._write_and_run("A|A|1|2\n")
    self.assertEqual(key, ("1", "2"))
    self.assertEqual(length, 1)
```

**Step 6: Run the updated test**

Run: `python3 -m pytest test_my_solution.py::TestRunUnsorted::test_single_line_self_loop -v`
Expected: PASS

**Step 7: Run all tests to ensure no regressions**

Run: `python3 -m pytest test_my_solution.py -v`
Expected: All PASS (after self-loop test updates)

**Step 8: Commit**

```bash
git add my_solution.py test_my_solution.py
git commit -m "fix: count self-loops as valid cycles of length 1"
```

---

## Task 2: Fix Tie-Breaking for Deterministic Lexicographic Ordering

**Issue:** Unsorted mode may not reliably produce lexicographically smallest result for ties.

**Files:**
- Modify: `/Users/ruby/Documents/dev/thoughtfulai/my_solution.py:62-64`

**Step 1: Update tie-breaking logic in run_unsorted**

In `my_solution.py`, line 62-64, change from:
```python
if cycle_len > best_len or (
    cycle_len == best_len and (best_key is None or key < best_key)
):
```
to:
```python
if cycle_len > best_len or (
    cycle_len == best_len and (best_key is None or key < best_key)
):
```

**Analysis:** The current logic is actually correct for Python 3.7+ (dict insertion order). However, we want deterministic output regardless of input order. The sorted mode already handles this correctly. We should update the unsorted mode to explicitly sort keys before processing, OR document that output order depends on input order.

**Implementation decision:** Since sorting adds overhead, and the spec says "any one is acceptable" for ties, we'll document the behavior rather than force sorting.

**Step 1 (revised): Update docstring to clarify tie-breaking behavior**

In `my_solution.py`, line 32, update the docstring from:
```python
def run_unsorted(path):
    """Accumulate all groups in memory, then find longest cycle per group. Use path or stdin when path is '-'."""
```
to:
```python
def run_unsorted(path):
    """Accumulate all groups in memory, then find longest cycle per group. Use path or stdin when path is '-'.
    Note: For ties in cycle length, the first group encountered in input order is selected.
    For deterministic lexicographic ordering, use sorted mode with --sorted flag."""
```

**Step 2: Run tests to verify no behavior change**

Run: `python3 -m pytest test_my_solution.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add my_solution.py
git commit -m "docs: clarify tie-breaking behavior for unsorted mode"
```

---

## Task 3: Add Validation/Warning for Sorted Mode

**Issue:** `--sorted` flag assumes input is sorted but doesn't validate.

**Files:**
- Modify: `/Users/ruby/Documents/dev/thoughtfulai/my_solution.py:70-141`
- Test: `/Users/ruby/Documents/dev/thoughtfulai/test_my_solution.py`

**Step 1: Add validation helper function**

Add after line 67 (after `run_unsorted` function):
```python
def validate_sorted_order(f):
    """Check if input is sorted by (claim_id, status_code). Returns True if sorted, False otherwise."""
    prev_key = None
    line_number = 0
    for line in f:
        line_number += 1
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 4:
            continue
        src, dst, claim_id, status_code = parts
        key = (claim_id, status_code)
        if prev_key is not None and key < prev_key:
            return False, line_number
        prev_key = key
    f.seek(0)
    return True, 0
```

**Step 2: Update run_sorted to use validation**

In `my_solution.py`, line 136-141, change from:
```python
def run_sorted(path):
    """Assume input is sorted by (claim_id, status_code). Use path or stdin when path is '-'."""
    if path == "-":
        return run_sorted_stream(sys.stdin)
    with open(path) as f:
        return run_sorted_stream(f)
```
to:
```python
def run_sorted(path, validate=False):
    """Assume input is sorted by (claim_id, status_code). Use path or stdin when path is '-'."""
    if path == "-":
        if validate:
            is_sorted, line_num = validate_sorted_order(sys.stdin)
            if not is_sorted:
                print(f"Warning: Input may not be sorted (disorder detected at line {line_num})", file=sys.stderr)
        return run_sorted_stream(sys.stdin)
    with open(path) as f:
        if validate:
            is_sorted, line_num = validate_sorted_order(f)
            if not is_sorted:
                print(f"Warning: Input may not be sorted (disorder detected at line {line_num})", file=sys.stderr)
        return run_sorted_stream(f)
```

**Step 3: Add --validate flag to CLI**

In `my_solution.py`, line 144-154, change from:
```python
def main():
    argv = sys.argv[1:]
    if not argv:
        print("Usage: python3 my_solution.py [--sorted] <input_file|->", file=sys.stderr)
        sys.exit(1)

    sorted_mode = argv[0] == "--sorted"
    path = argv[1] if sorted_mode else argv[0]
    if sorted_mode and len(argv) < 2:
        print("Usage: python3 my_solution.py [--sorted] <input_file|->", file=sys.stderr)
        sys.exit(1)
```
to:
```python
def main():
    argv = sys.argv[1:]
    if not argv:
        print("Usage: python3 my_solution.py [--sorted] [--validate] <input_file|->", file=sys.stderr)
        sys.exit(1)

    sorted_mode = argv[0] == "--sorted"
    validate_mode = "--validate" in argv
    if validate_mode:
        argv.remove("--validate")

    path = argv[1] if sorted_mode else argv[0]
    if sorted_mode and len(argv) < 2:
        print("Usage: python3 my_solution.py [--sorted] [--validate] <input_file|->", file=sys.stderr)
        sys.exit(1)

    best_key, best_len = (run_sorted(path, validate=validate_mode) if sorted_mode else run_unsorted(path))
```

**Step 4: Write test for validation**

Add to `test_my_solution.py` after line 173 (in `TestRunSortedStream` class):
```python
def test_validate_sorted_detects_unsorted(self):
    """Validation should detect unsorted input."""
    import subprocess
    content = "A|B|b|1\nB|A|a|1\n"  # 'b' < 'a' - unsorted
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        result = subprocess.run(
            [os.environ.get("PYTHON", "python3"), "my_solution.py", "--sorted", "--validate", path],
            cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
            capture_output=True,
            text=True,
        )
        self.assertIn("Warning", result.stderr)
    finally:
        os.unlink(path)

def test_validate_sorted_passes_sorted(self):
    """Validation should pass for sorted input."""
    import subprocess
    content = "A|B|a|1\nB|A|b|1\n"  # properly sorted
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        result = subprocess.run(
            [os.environ.get("PYTHON", "python3"), "my_solution.py", "--sorted", "--validate", path],
            cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
            capture_output=True,
            text=True,
        )
        self.assertNotIn("Warning", result.stderr)
    finally:
        os.unlink(path)
```

**Step 5: Run validation tests**

Run: `python3 -m pytest test_my_solution.py::TestRunSortedStream::test_validate_sorted_detects_unsorted -v`
Run: `python3 -m pytest test_my_solution.py::TestRunSortedStream::test_validate_sorted_passes_sorted -v`
Expected: PASS for both

**Step 6: Run all tests**

Run: `python3 -m pytest test_my_solution.py -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add my_solution.py test_my_solution.py
git commit -m "feat: add --validate flag to check sorted input order"
```

---

## Task 4: Document Memory Limitations

**Issue:** The `run_unsorted` function's `sys_map` grows indefinitely.

**Files:**
- Modify: `/Users/ruby/Documents/dev/thoughtfulai/my_solution.py:32-34`
- Create: `/Users/ruby/Documents/dev/thoughtfulai/README.md`

**Step 1: Update run_unsorted docstring with memory notes**

In `my_solution.py`, line 32-34, change from:
```python
def run_unsorted(path):
    """Accumulate all groups in memory, then find longest cycle per group. Use path or stdin when path is '-'."""
    sys_map = {}
```
to:
```python
def run_unsorted(path):
    """Accumulate all groups in memory, then find longest cycle per group. Use path or stdin when path is '-'.

    Memory: Stores all groups and all unique system names in memory. For large files,
    use sorted mode (--sorted) which streams one group at a time.
    """
    sys_map = {}
```

**Step 2: Create README.md with usage guide**

Create `/Users/ruby/Documents/dev/thoughtfulai/README.md`:
```markdown
# Routing Cycle Detector

Finds the longest routing cycle in a pipe-delimited file of claim routing data.

## Usage

```bash
# For small files (all data in memory)
python3 my_solution.py input.txt

# For large files (streaming, requires sorted input)
python3 my_solution.py --sorted input.txt

# Validate input is sorted (catches errors early)
python3 my_solution.py --sorted --validate input.txt

# Use with stdin
cat input.txt | python3 my_solution.py -
sort -t'|' -k3,3 -k4,4 input.txt | python3 my_solution.py --sorted -
```

## Output Format

```
<claim_id>,<status_code>,<cycle_length>
```

## Performance

- **Unsorted mode:** All data loaded into memory. Suitable for files < 1GB.
- **Sorted mode:** Streams one group at a time. Suitable for files of any size.

To sort your data:
```bash
sort -t'|' -k3,3 -k4,4 input.txt > sorted_input.txt
```

## Testing

```bash
python3 -m pytest test_my_solution.py -v
```
```

**Step 3: Run tests to ensure no behavior change**

Run: `python3 -m pytest test_my_solution.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add my_solution.py README.md
git commit -m "docs: add README with usage guide and memory notes"
```

---

## Task 5: Verify Fix on Example Input

**Files:**
- Test: `/Users/ruby/Documents/dev/thoughtfulai/example_input.txt`

**Step 1: Run solution on example input**

Run: `python3 my_solution.py example_input.txt`
Expected: Output format `<claim_id>,<status_code>,<cycle_length>`

**Step 2: Verify output manually**

Check that the output makes sense given the input data.

**Step 3: Run tests one final time**

Run: `python3 -m pytest test_my_solution.py -v`
Expected: All PASS

**Step 4: Update solution.txt if needed**

If the fix changes the result on the large input, re-run:
```bash
python3 my_solution.py large_input_v1.txt > solution.txt
```

**Step 5: Final commit**

```bash
git add solution.txt
git commit -m "chore: update solution.txt after fixes"
```

---

## Summary

This plan addresses all critical and important issues:

1. **Self-loop handling** - Now correctly counts as cycle length 1
2. **Tie-breaking** - Documented behavior for both modes
3. **Sorted validation** - Added `--validate` flag to catch unsorted input
4. **Memory documentation** - Added README and docstring notes
5. **Verification** - Final testing on example input

Each task follows TDD principles and commits frequently for easy rollback.
