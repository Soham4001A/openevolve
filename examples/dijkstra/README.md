# Dijkstra's Algorithm Evolution Example

This example demonstrates how OpenEvolve can be used to evolve implementations of classic algorithms, specifically Dijkstra's algorithm for finding the shortest paths in a weighted graph with non-negative edge weights.

## Problem Overview

Dijkstra's algorithm finds the shortest paths from a single source node to all other nodes in a graph. The goal for OpenEvolve in this example is:

- To evolve a Python function `dijkstra_algorithm(graph, start_node)`.
- The input `graph` is represented as a dictionary of dictionaries: `{'nodeA': {'nodeB': weight, ...}}`.
- The `start_node` is a string identifier for the starting node.
- The function should return a dictionary where keys are node identifiers and values are the shortest distances from the `start_node`.
- Distances to unreachable nodes should be `float('infinity')`.
- If the `start_node` is not in the graph or the graph is empty, the function should return `None`.
- The primary objective is correctness across a variety of test graphs.

## Our Approach

We structure the evolution process, potentially in phases, to guide OpenEvolve towards a correct and robust solution.

### Phase 1: Achieving Basic Correctness

The initial phase focuses on getting the fundamental logic of Dijkstra's algorithm right.
- The `initial_program.py` starts with a basic, somewhat naive template for `dijkstra_algorithm`.
- The LLM is prompted to complete or fix this implementation, focusing on core concepts like distance initialization, node traversal, path relaxation, and use of a priority queue (e.g., `heapq`).
- The `evaluator.py` tests the evolved functions against a set of diverse graphs, checking for correctness.

Configuration highlights for Phase 1 (example):
```yaml
max_iterations: 100
population_size: 50
prompt:
  system_message: |
    You are an expert programmer ... Your task is to implement or improve `dijkstra_algorithm(graph, start_node)`...
    Focus on correctness first... Consider ... a priority queue (min-heap using `heapq`) ...
evaluator:
  cascade_thresholds: [0.3, 0.6] # Score based on correctness * validity