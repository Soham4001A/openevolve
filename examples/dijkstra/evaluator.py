"""
Evaluator for Dijkstra's algorithm evolution.
"""

import importlib.util
import time
import os
import subprocess
import tempfile
import traceback
import sys
import pickle
# heapq can be used for a reference implementation if needed, but test cases are pre-defined.

class TimeoutError(Exception):
    pass

# Define test cases directly in the evaluator for clarity and to avoid import issues in subprocesses.
# Each tuple: (graph_dict, start_node, expected_distances_dict or None)
TEST_CASES = [
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
    ),
    (
        {'X': {'Y': 10}, 'Y': {'X': 10, 'Z': 20}, 'Z': {'Y': 20, 'W': 5}, 'W': {'Z': 5}},
        'X',
        {'X': 0, 'Y': 10, 'Z': 30, 'W': 35}
    ),
    (
        {'N1': {'N2': 1}, 'N2': {'N1': 1, 'N3': 1}, 'N3': {'N2': 1}, 'N4': {'N5': 1}, 'N5': {'N4': 1}},
        'N1',
        {'N1': 0, 'N2': 1, 'N3': 2, 'N4': float('infinity'), 'N5': float('infinity')}
    ),
    ( # Single node graph
        {'Z': {}}, 'Z', {'Z': 0}
    ),
    ( # Empty graph
        {}, 'A', None
    ),
    ( # Start node not in graph
        {'A': {'B':1}}, 'X', None
    )
]

def run_evolved_dijkstra(program_path, graph, start_node, timeout_seconds=10):
    input_data = pickle.dumps({'graph': graph, 'start_node': start_node})
    temp_file_prefix = tempfile.NamedTemporaryFile(delete=False).name
    input_temp_file_path = f"{temp_file_prefix}_input.pkl"
    results_path = f"{temp_file_prefix}_results.pkl"
    exec_temp_file_path = f"{temp_file_prefix}_exec.py"

    with open(input_temp_file_path, "wb") as input_temp_file:
        input_temp_file.write(input_data)
    
    script_content = f"""
import sys
import pickle
import os
import traceback
import importlib.util

sys.path.insert(0, os.path.dirname('{program_path}'))

try:
    with open('{input_temp_file_path}', 'rb') as f:
        data = pickle.load(f)
    graph = data['graph']
    start_node = data['start_node']

    spec = importlib.util.spec_from_file_location("evolved_module", '{program_path}')
    evolved_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evolved_module)
    
    if hasattr(evolved_module, 'dijkstra_algorithm'):
        distances = evolved_module.dijkstra_algorithm(graph, start_node)
        result_data = {{'distances': distances}}
    else:
        raise AttributeError("Evolved program does not have 'dijkstra_algorithm' function.")

    with open('{results_path}', 'wb') as f_out:
        pickle.dump(result_data, f_out)

except Exception as e:
    with open('{results_path}', 'wb') as f_out:
        pickle.dump({{'error': str(e), 'traceback': traceback.format_exc()}}, f_out)
"""
    with open(exec_temp_file_path, "w") as exec_temp_file:
        exec_temp_file.write(script_content)

    try:
        process = subprocess.Popen(
            [sys.executable, exec_temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        
        # process.returncode check can be added if specific exit codes are meaningful
        
        if os.path.exists(results_path):
            with open(results_path, "rb") as f:
                results = pickle.load(f)
            if "error" in results:
                # print(f"Error in evolved Dijkstra: {results['error']}\n{results.get('traceback','')}")
                return {"error": results['error']}
            return results.get('distances')
        else:
            # print(f"Results file not found. Stdout: {stdout.decode(errors='ignore')} Stderr: {stderr.decode(errors='ignore')}")
            return {"error": "Results file not found"}

    except subprocess.TimeoutExpired:
        if process:
            process.kill()
            process.wait()
        # print(f"Timeout running evolved Dijkstra after {timeout_seconds}s")
        return {"error": f"Timeout after {timeout_seconds} seconds"}
    except Exception as e:
        # print(f"Exception running evolved Dijkstra: {e}")
        return {"error": f"Failed to run evolved Dijkstra: {str(e)}"}
    finally:
        for p in [input_temp_file_path, results_path, exec_temp_file_path]:
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError: # For potential race conditions or file lock issues on some OS
                    pass


def compare_distances(calculated_distances, expected_distances, graph_nodes_set):
    if calculated_distances is None and expected_distances is None:
        return 1.0
    if not isinstance(calculated_distances, dict) or not isinstance(expected_distances, dict):
        if isinstance(calculated_distances, dict) and expected_distances is None: return 0.0
        if calculated_distances is None and isinstance(expected_distances, dict): return 0.0
        # print(f"Type mismatch or one is None when other is not: calc={type(calculated_distances)}, exp={type(expected_distances)}")
        return 0.0

    correct_nodes = 0
    
    # Consider all nodes present in the graph, the expected solution, or the calculated solution
    # This ensures penalties for missing nodes or extra nodes with incorrect values.
    all_relevant_nodes = graph_nodes_set | set(expected_distances.keys()) | set(calculated_distances.keys())
    if not all_relevant_nodes: # Both expected and calculated are empty, and graph itself was empty.
        return 1.0


    for node in all_relevant_nodes:
        calc_dist = calculated_distances.get(node, float('infinity'))
        exp_dist = expected_distances.get(node, float('infinity'))
        
        # Normalize potential string "inf" from LLM outputs
        if isinstance(calc_dist, str) and 'inf' in calc_dist.lower():
            calc_dist = float('infinity')

        if abs(calc_dist - exp_dist) < 1e-6:
            correct_nodes += 1
        # else:
            # print(f"Mismatch for node {node}: calc={calc_dist}, exp={exp_dist}")
            
    return correct_nodes / len(all_relevant_nodes) if len(all_relevant_nodes) > 0 else 1.0


def evaluate(program_path):
    total_correctness = 0
    num_test_cases = len(TEST_CASES)
    if num_test_cases == 0: # Should not happen with TEST_CASES defined above
        return {"correctness_ratio": 0.0, "validity": 0.0, "eval_time": 0.0, "combined_score": 0.0, "error_count": 1}

    start_eval_time = time.time()
    error_count = 0
    any_successful_run = False

    for i, (graph, start_node, expected_solution) in enumerate(TEST_CASES):
        graph_nodes_set = set(graph.keys()) # Nodes present in the input graph definition
        evolved_distances = run_evolved_dijkstra(program_path, graph, start_node)

        current_correctness_score = 0.0
        if isinstance(evolved_distances, dict) and "error" in evolved_distances:
            error_count += 1
            # print(f"Test case {i+1} error: {evolved_distances['error']}")
        elif evolved_distances is None and expected_solution is None: # Correctly returned None
            current_correctness_score = 1.0
            any_successful_run = True
        elif isinstance(evolved_distances, dict) and isinstance(expected_solution, dict):
            current_correctness_score = compare_distances(evolved_distances, expected_solution, graph_nodes_set)
            any_successful_run = True
        elif isinstance(evolved_distances, dict) and expected_solution is None: # Produced dict when None expected
            error_count +=1 # Or count as 0 correctness
        elif evolved_distances is None and isinstance(expected_solution, dict): # Produced None when dict expected
            error_count +=1 # Or count as 0 correctness
        else: # Other type mismatches
            error_count +=1
            # print(f"Test case {i+1} output type error: {type(evolved_distances)}")
            
        total_correctness += current_correctness_score

    eval_time = time.time() - start_eval_time
    
    average_correctness = total_correctness / num_test_cases if num_test_cases > 0 else 0.0
    # Validity: program runs on at least one case without error and produces some sort of comparable output
    validity = 1.0 if any_successful_run and error_count < num_test_cases else 0.0
    if error_count == num_test_cases and num_test_cases > 0 : # All tests errored
        validity = 0.0


    combined_score = average_correctness * validity
    # print(f"Eval: avg_correctness={average_correctness:.3f}, validity={validity:.1f}, errors={error_count}, combined={combined_score:.3f}, time={eval_time:.2f}s")

    return {
        "correctness_ratio": float(average_correctness),
        "validity": float(validity),
        "eval_time": float(eval_time),
        "combined_score": float(combined_score),
        "error_count": int(error_count)
    }

def evaluate_stage1(program_path):
    stage1_test_cases = TEST_CASES[:3] # Use first 3 simple cases for stage 1
    if not stage1_test_cases:
         return {"validity": 0.0, "combined_score": 0.0, "error": "No stage 1 test cases"}

    total_correctness_s1 = 0
    error_count_s1 = 0
    any_successful_run_s1 = False

    for graph, start_node, expected_solution in stage1_test_cases:
        graph_nodes_set = set(graph.keys())
        evolved_distances = run_evolved_dijkstra(program_path, graph, start_node, timeout_seconds=5) 

        current_correctness_score = 0.0
        if isinstance(evolved_distances, dict) and "error" in evolved_distances:
            error_count_s1 += 1
        elif evolved_distances is None and expected_solution is None:
            current_correctness_score = 1.0
            any_successful_run_s1 = True
        elif isinstance(evolved_distances, dict) and isinstance(expected_solution, dict):
            current_correctness_score = compare_distances(evolved_distances, expected_solution, graph_nodes_set)
            any_successful_run_s1 = True
        else:
            error_count_s1 +=1
        total_correctness_s1 += current_correctness_score
    
    num_s1_cases = len(stage1_test_cases)
    avg_correctness_s1 = total_correctness_s1 / num_s1_cases if num_s1_cases > 0 else 0.0
    validity_s1 = 1.0 if any_successful_run_s1 and error_count_s1 < num_s1_cases else 0.0
    if error_count_s1 == num_s1_cases and num_s1_cases > 0:
        validity_s1 = 0.0
        
    # print(f"Stage1: avg_corr={avg_correctness_s1:.3f}, valid={validity_s1:.1f}, errors={error_count_s1}, combined={avg_correctness_s1 * validity_s1:.3f}")
    return {
        "validity": float(validity_s1),
        "combined_score": float(avg_correctness_s1 * validity_s1),
        "error": "" if validity_s1 > 0 else "Failed stage 1 criteria (all errored or no successful run)"
    }

def evaluate_stage2(program_path):
    return evaluate(program_path)