# Routing Cycle Detector

Finds the longest routing cycle in a pipe-delimited file of claim routing data.

## Dataset

- **Small example:** `example_input.txt` (included in repo).
- **Large dataset:** Download from [Google Drive](https://drive.google.com/file/d/10WF0EwKH7pac1Pxp3BmRwC_1B1Lxuix0/view?usp=sharing) and save as `large_input_v1.txt` (not in repo; listed in `.gitignore`).

## Usage

**Try it (copy any command — uses included `example_input.txt`):**

```bash
# Run on small file (all data in memory)
python3 my_solution.py example_input.txt

# Sorted mode: sort first, then run (one group in memory at a time)
sort -t'|' -k3,3 -k4,4 example_input.txt > sorted_input.txt
python3 my_solution.py --sorted sorted_input.txt

# Validate that input is sorted (use with --sorted only)
python3 my_solution.py --sorted --validate sorted_input.txt

# Stdin
cat example_input.txt | python3 my_solution.py -
sort -t'|' -k3,3 -k4,4 example_input.txt | python3 my_solution.py --sorted -
```

**With the large dataset** (download `large_input_v1.txt` first; see Dataset above):

```bash
python3 my_solution.py large_input_v1.txt
sort -t'|' -k3,3 -k4,4 large_input_v1.txt > sorted_input.txt
python3 my_solution.py --sorted sorted_input.txt
sort -t'|' -k3,3 -k4,4 large_input_v1.txt | python3 my_solution.py --sorted -
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
sort -t'|' -k3,3 -k4,4 large_input_v1.txt > sorted_input.txt
```

## Testing

```bash
python3 -m unittest test_my_solution -v
```
