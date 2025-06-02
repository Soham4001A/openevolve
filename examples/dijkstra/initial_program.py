# EVOLVE-BLOCK-START
"""Dijkstra's algorithm for finding shortest paths in a weighted graph."""
import heapq # Allow importing heapq

def dijkstra_algorithm(graph, start_node):
    """
    Calculates the shortest paths from a start_node to all other nodes
    in a weighted graph with non-negative edge weights.

    Args:
        graph: A dictionary representing the graph.
               Keys are node names (e.g., 'A', 'B').
               Values are dictionaries where keys are neighbor node names
               and values are the edge weights.
               Example: {'A': {'B': 1, 'C': 4}, 'B': {'A': 1, 'C': 2, 'D': 5}, ...}
        start_node: The starting node for calculating shortest paths.

    Returns:
        A dictionary where keys are node names and values are the
        shortest distances from the start_node.
        Returns None if the start_node is not in the graph or if graph is empty and start_node is present.
    """
    if not graph: # Handle empty graph
        return None 
        
    if start_node not in graph:
        return None

    distances = {node: float('infinity') for node in graph}
    distances[start_node] = 0
    
    # The following is a naive implementation, not using a priority queue effectively.
    # Evolution should improve this to use heapq for efficiency and correctness.
    unvisited_nodes = set(graph.keys())
    
    while unvisited_nodes:
        current_node = None
        # Find node with smallest distance among unvisited_nodes
        # This part is inefficient and a key area for improvement by evolution
        min_dist_val = float('infinity')
        for node in unvisited_nodes:
            if distances[node] < min_dist_val:
                min_dist_val = distances[node]
                current_node = node
        
        if current_node is None or distances[current_node] == float('infinity'):
            # All remaining unvisited nodes are inaccessible from start_node
            break 

        unvisited_nodes.remove(current_node)

        # Check if current_node actually exists as a key in graph,
        # which it should if it came from graph.keys()
        if current_node in graph:
            for neighbor, weight in graph[current_node].items():
                # Ensure neighbor is a valid node defined in the graph distances dict
                if neighbor in distances: 
                    new_distance = distances[current_node] + weight
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        # If this were a proper priority queue implementation,
                        # the neighbor might need to be re-added or updated in the queue.
                        # For this naive version, we just update distance.
    
    return distances
# EVOLVE-BLOCK-END


# This part remains fixed (not evolved) and is for local testing/convenience
def run_dijkstra_on_sample_graph_for_testing():
    """
    Runs the evolved Dijkstra's algorithm on a sample graph for local testing.
    """
    sample_graph = {
        'S': {'A': 1, 'B': 3},
        'A': {'S': 1, 'C': 2, 'D': 4},
        'B': {'S': 3, 'C': 2, 'E': 5},
        'C': {'A': 2, 'B': 2, 'E': 1, 'D': 7},
        'D': {'A': 4, 'E': 6, 'C': 7},
        'E': {'B': 5, 'C': 1, 'D': 6}
    }
    start_node = 'S'
    
    distances = dijkstra_algorithm(sample_graph, start_node)
    return distances

def get_test_graphs_and_solutions():
    """
    Provides a list of sample graphs and their correct Dijkstra solutions
    for local testing convenience.
    The official evaluator uses its own internally defined TEST_CASES.
    """
    # These are the same as in evaluator.py's TEST_CASES for consistency
    graphs_data = [
        (
            {'A': {'B': 1, 'C': 4}, 'B': {'A': 1, 'C': 2, 'D': 5}, 'C': {'A': 4, 'B': 2, 'D': 1}, 'D': {'B': 5, 'C': 1}},
            'A',
            {'A': 0, 'B': 1, 'C': 3, 'D': 4}
        ),
        (
            {'A': {'B': 1}, 'B': {'A': 1}, 'C': {'D': 2}, 'D': {'C': 2}},
            'A',
            {'A': 0, 'B': 1, 'C': float('infinity'), 'D': float('infinity')}
        ),
        (
            {'S': {'A': 1, 'B': 3}, 'A': {'S': 1, 'C': 2, 'D': 4}, 'B': {'S': 3, 'C': 2, 'E': 5}, 'C': {'A': 2, 'B': 2, 'E': 1, 'D': 7}, 'D': {'A': 4, 'E': 6, 'C': 7}, 'E': {'B': 5, 'C': 1, 'D': 6}},
            'S',
            {'S':0, 'A':1, 'B':3, 'C':3, 'D':5, 'E':4}
        )
    ]
    return graphs_data


if __name__ == "__main__":
    print("Testing initial Dijkstra implementation with a sample graph:")
    distances_sample = run_dijkstra_on_sample_graph_for_testing()
    print(f"  Distances from S: {distances_sample}")
    expected_distances_sample = {'S':0, 'A':1, 'B':3, 'C':3, 'D':5, 'E':4}
    print(f"  Expected for sample: {expected_distances_sample}")

    print("\nTesting against more cases from get_test_graphs_and_solutions():")
    test_suite = get_test_graphs_and_solutions()
    for i, (graph, start, solution) in enumerate(test_suite):
        print(f"\nTest Case {i+1} (start: {start}):")
        evolved_distances = dijkstra_algorithm(graph, start)
        print(f"  Evolved Output: {evolved_distances}")
        print(f"  Correct Output: {solution}")
        
        # Basic comparison for local test
        if evolved_distances == solution:
            print("  Result: MATCH")
        else:
            print("  Result: MISMATCH")