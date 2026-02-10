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
python3 -m unittest test_my_solution -v
```
