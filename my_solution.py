#!/usr/bin/env python3
"""
Routing Cycle Detector: finds the longest simple directed cycle per (claim_id, status_code).
Use --sorted when input is already sorted by (claim_id, status_code) to hold only one group in memory.
"""
import sys
from collections import defaultdict


def find_longest_cycle(edges):
    """Find longest simple cycle in a small directed graph. Returns cycle length (number of hops)."""
    adj = defaultdict(list)
    nodes = set()
    for s, d in edges:
        adj[s].append(d)
        nodes.add(s)
        nodes.add(d)

    best = 0
    for start in nodes:
        stack = [(start, frozenset([start]))]
        while stack:
            node, visited = stack.pop()
            for nb in adj[node]:
                if nb == start and len(visited) >= 1:
                    best = max(best, len(visited))
                elif nb not in visited:
                    stack.append((nb, visited | {nb}))
    return best


def run_unsorted(path):
    """Accumulate all groups in memory, then find longest cycle per group. Use path or stdin when path is '-'."""
    sys_map = {}
    groups = defaultdict(set)
    f = sys.stdin if path == "-" else open(path)
    try:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("|")
            if len(parts) != 4:
                continue
            src, dst, claim_id, status_code = parts
            s = sys_map.setdefault(src, len(sys_map))
            d = sys_map.setdefault(dst, len(sys_map))
            groups[(claim_id, status_code)].add((s, d))
    finally:
        if path != "-":
            f.close()

    best_len = 0
    best_key = None
    n_groups = len(groups)
    for i, (key, edges) in enumerate(groups.items()):
        if (i + 1) % 100000 == 0:
            print(f"Progress: {i + 1}/{n_groups} groups", file=sys.stderr)
        if len(edges) < best_len:
            continue
        cycle_len = find_longest_cycle(edges)
        if cycle_len > 0 and (cycle_len > best_len or (
            cycle_len == best_len and (best_key is None or key < best_key)
        )):
            best_len = cycle_len
            best_key = key
    return best_key, best_len


def run_sorted_stream(f):
    """Assume input is sorted by (claim_id, status_code). Hold only one group in memory. f: file-like."""
    best_len = 0
    best_key = None
    current_key = None
    current_edges = set()
    node_to_idx = {}
    n_groups = 0

    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 4:
            continue
        src, dst, claim_id, status_code = parts
        key = (claim_id, status_code)

        if key != current_key:
            if (
                current_key is not None
                and len(current_edges) >= 1
                and len(current_edges) >= best_len
            ):
                node_to_idx.clear()
                int_edges = set()
                for a, b in current_edges:
                    s = node_to_idx.setdefault(a, len(node_to_idx))
                    d = node_to_idx.setdefault(b, len(node_to_idx))
                    int_edges.add((s, d))
                cycle_len = find_longest_cycle(int_edges)
                if cycle_len > 0 and (cycle_len > best_len or (
                    cycle_len == best_len and (best_key is None or current_key < best_key)
                )):
                    best_len = cycle_len
                    best_key = current_key
            current_key = key
            current_edges = set()
            n_groups += 1
            if n_groups % 100000 == 0:
                print(f"Progress: {n_groups} groups", file=sys.stderr)

        current_edges.add((src, dst))

    if (
        current_key is not None
        and len(current_edges) >= 1
        and len(current_edges) >= best_len
    ):
        node_to_idx.clear()
        int_edges = set()
        for a, b in current_edges:
            s = node_to_idx.setdefault(a, len(node_to_idx))
            d = node_to_idx.setdefault(b, len(node_to_idx))
            int_edges.add((s, d))
        cycle_len = find_longest_cycle(int_edges)
        if cycle_len > 0 and (cycle_len > best_len or (
            cycle_len == best_len and (best_key is None or current_key < best_key)
        )):
            best_len = cycle_len
            best_key = current_key

    return best_key, best_len


def run_sorted(path):
    """Assume input is sorted by (claim_id, status_code). Use path or stdin when path is '-'."""
    if path == "-":
        return run_sorted_stream(sys.stdin)
    with open(path) as f:
        return run_sorted_stream(f)


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

    best_key, best_len = (run_sorted(path) if sorted_mode else run_unsorted(path))

    if best_key is None:
        print("0,0,0")
    else:
        print(f"{best_key[0]},{best_key[1]},{best_len}")


if __name__ == "__main__":
    main()
