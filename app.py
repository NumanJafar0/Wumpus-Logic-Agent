from flask import Flask, jsonify, request, render_template
import random

app = Flask(__name__)

# =======================================================================
# PYTHON BACKEND STATE
# =======================================================================
class WumpusWorld:
    def __init__(self):
        self.M = 4
        self.N = 4
        self.true_grid = []
        self.agent_pos = (0, 0)
        self.visited = set()
        self.safe_cells = set()
        self.danger_cells = set()
        self.path_stack = []
        self.KB = []
        self.total_steps = 0
        self.current_percepts = {"breeze": False, "stench": False}
        self.done = False

world = WumpusWorld()

def get_neighbors(r, c, M, N):
    neighbors = []
    if r > 0: neighbors.append((r - 1, c))
    if r < M - 1: neighbors.append((r + 1, c))
    if c > 0: neighbors.append((r, c - 1))
    if c < N - 1: neighbors.append((r, c + 1))
    return neighbors

def generate_hazards(M, N):
    grid = [['EMPTY' for _ in range(N)] for _ in range(M)]
    
    # Place Wumpus (Not at 0,0)
    while True:
        wr, wc = random.randint(0, M-1), random.randint(0, N-1)
        if (wr, wc) != (0, 0):
            grid[wr][wc] = 'WUMPUS'
            break
            
    # Place Pits (approx 15%, not at 0,0)
    num_pits = max(1, int((M * N) * 0.15))
    for _ in range(num_pits):
        while True:
            pr, pc = random.randint(0, M-1), random.randint(0, N-1)
            if (pr, pc) != (0, 0) and grid[pr][pc] == 'EMPTY':
                grid[pr][pc] = 'PIT'
                break
    return grid

# =======================================================================
# PROPOSITIONAL LOGIC INFERENCE ENGINE
# =======================================================================
def tell_kb(r, c, breeze, stench):
    world.KB.append([f"B_{r}_{c}"] if breeze else [f"~B_{r}_{c}"])
    world.KB.append([f"S_{r}_{c}"] if stench else [f"~S_{r}_{c}"])
    
    neighbors = get_neighbors(r, c, world.M, world.N)
    p_lits = [f"P_{nr}_{nc}" for nr, nc in neighbors]
    w_lits = [f"W_{nr}_{nc}" for nr, nc in neighbors]
    
    # Rule: B_r_c <=> (P_n1 v P_n2 ...)
    world.KB.append([f"~B_{r}_{c}"] + p_lits)
    for pl in p_lits:
        world.KB.append([f"B_{r}_{c}", f"~{pl}"])
        
    # Rule: S_r_c <=> (W_n1 v W_n2 ...)
    world.KB.append([f"~S_{r}_{c}"] + w_lits)
    for wl in w_lits:
        world.KB.append([f"S_{r}_{c}", f"~{wl}"])

def resolve(c1, c2):
    complement = None
    for lit in c1:
        neg = lit[1:] if lit.startswith("~") else "~" + lit
        if neg in c2:
            if complement is None:
                complement = lit
            else:
                return None 
    if not complement:
        return None
        
    neg_comp = complement[1:] if complement.startswith("~") else "~" + complement
    res_set = set(c1) | set(c2)
    res_set.discard(complement)
    res_set.discard(neg_comp)
    return list(res_set)

def resolution_refutation(kb, query_clause):
    clauses = [list(c) for c in kb]
    clauses.append(query_clause)
    
    def sort_clause(c): return tuple(sorted(list(set(c))))
    
    seen = set([sort_clause(c) for c in clauses])
    queue = [query_clause] 
    local_steps = 0
    max_loops = 2000
    
    while queue and local_steps < max_loops:
        c1 = queue.pop(0)
        for c2 in clauses:
            local_steps += 1
            resolvent = resolve(c1, c2)
            if resolvent is not None:
                if len(resolvent) == 0:
                    return True, local_steps 
                
                c_tuple = sort_clause(resolvent)
                if c_tuple not in seen:
                    seen.add(c_tuple)
                    clauses.append(resolvent)
                    queue.append(resolvent)
    return False, local_steps

# =======================================================================
# API ENDPOINTS & AGENT CONTROLLER
# =======================================================================
@app.route('/api/init', methods=['POST'])
def init_game():
    data = request.json
    world.M = int(data.get('rows', 4))
    world.N = int(data.get('cols', 4))
    world.true_grid = generate_hazards(world.M, world.N)
    world.agent_pos = (0, 0)
    world.visited = set()
    world.safe_cells = set()
    world.danger_cells = set()
    world.path_stack = []
    world.KB = [["~P_0_0"], ["~W_0_0"]] 
    world.total_steps = 0
    world.done = False
    return build_state_response()

@app.route('/api/step', methods=['POST'])
def step_agent():
    if world.done: return build_state_response()

    r, c = world.agent_pos
    cell_key = f"{r}_{c}"
    
    if cell_key not in world.visited:
        world.visited.add(cell_key)
        world.safe_cells.add(cell_key)
        
        # 1. SENSE
        neighbors = get_neighbors(r, c, world.M, world.N)
        breeze = any(world.true_grid[nr][nc] == 'PIT' for nr, nc in neighbors)
        stench = any(world.true_grid[nr][nc] == 'WUMPUS' for nr, nc in neighbors)
        world.current_percepts = {"breeze": breeze, "stench": stench}

        # 2. TELL
        tell_kb(r, c, breeze, stench)

        # 3. ASK 
        for nr, nc in neighbors:
            n_key = f"{nr}_{nc}"
            if n_key not in world.visited and n_key not in world.safe_cells and n_key not in world.danger_cells:
                chk_pit, p_steps = resolution_refutation(world.KB, [f"P_{nr}_{nc}"])
                chk_wumpus, w_steps = resolution_refutation(world.KB, [f"W_{nr}_{nc}"])
                world.total_steps += (p_steps + w_steps)
                
                if chk_pit and chk_wumpus:
                    world.safe_cells.add(n_key)
                else:
                    is_pit, ip_steps = resolution_refutation(world.KB, [f"~P_{nr}_{nc}"])
                    is_wumpus, iw_steps = resolution_refutation(world.KB, [f"~W_{nr}_{nc}"])
                    world.total_steps += (ip_steps + iw_steps)
                    if is_pit or is_wumpus:
                        world.danger_cells.add(n_key)

    # 4. MOVE 
    neighbors = get_neighbors(r, c, world.M, world.N)
    unvisited_safe = [n for n in neighbors if f"{n[0]}_{n[1]}" in world.safe_cells and f"{n[0]}_{n[1]}" not in world.visited]

    if unvisited_safe:
        world.path_stack.append(world.agent_pos)
        world.agent_pos = unvisited_safe[0]
    elif world.path_stack:
        world.agent_pos = world.path_stack.pop()
    else:
        world.done = True

    return build_state_response()

def build_state_response():
    return jsonify({
        "agent_pos": {"r": world.agent_pos[0], "c": world.agent_pos[1]},
        "visited": list(world.visited),
        "safe_cells": list(world.safe_cells),
        "danger_cells": list(world.danger_cells),
        "inference_steps": world.total_steps,
        "percepts": world.current_percepts,
        "done": world.done
    })

@app.route('/')
def serve_ui():
    # Flask will look for this file inside the 'templates' folder
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)