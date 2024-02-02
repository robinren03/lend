import logging
import numpy as np

def find_path_km(i, edges, match, visited_l, visited_r, l_val, r_val, slack):
    n, m = len(edges), len(edges[0])
    visited_l[i] = True
    for j in range(m):
        if (visited_r[j]):
            continue
        if (l_val[i] + r_val[j] == edges[i][j]):
            visited_r[j] = True
            if (match[j] == -1 or find_path_km(match[j], edges, match, visited_l, visited_r, l_val, r_val, slack)):
                match[j] = i
                return True
        else:
            slack[j] = min(slack[j], l_val[i] + r_val[j] - edges[i][j])
    return False

def best_match_km(edges): 
    '''
    KM algorithm for finding the best matching in a bipartite graph
    edges: a list of lists, where edges[i][j] is the weight of the edge from i to j. The first dimension is text(left), the second dimension is devices(right).
    '''
    n = len(edges)
    if n == 0: return []
    m = len(edges[0]) # n = number of rows, m = number of columns
    if n > m:
        logging.error("The number of rows cannot be greater than the number of columns.")
        edges = np.transpose(edges)
        n, m = m, n
        transposed = True
    else:
        transposed = False

    match = [-1] * m
    r_val = [0] * m
    l_val = [0] * n
    for i in range(n):
        l_val[i] = max(edges[i])
    
    for i in range(n):
        slack = [float("inf")] * m
        round = 0
        while (round < n * m):
            visited_l = [False] * n
            visited_r = [False] * m
            if (find_path_km(i, edges, match, visited_l, visited_r, l_val, r_val, slack)):
                break
            delta = float("inf")
            for j in range(m):
                if (not visited_r[j]):
                    delta = min(delta, slack[j])
            for j in range(n):
                if (visited_l[j]):
                    l_val[j] -= delta
            for j in range(m):
                if (visited_r[j]):
                    r_val[j] += delta
                else: slack[j] -= delta
            round += 1
    if transposed:
        return match
        
    text_device = [-1] * n
    for i in range(m):
        if (match[i] != -1):
            text_device[match[i]] = i
            
    return text_device

if __name__ == "__main__":
    edges = [[-float("inf"),-float("inf"), -float("inf"), -float("inf")],[-float("inf"), 3, 1, 0]]
    print(best_match_km(edges))