# app.py
from flask import Flask, render_template, request, jsonify
import numpy as np
from scipy.optimize import minimize

app = Flask(__name__)

def northwest_corner(supply, demand):
    supply = supply.copy()
    demand = demand.copy()
    m, n = len(supply), len(demand)
    allocation = np.zeros((m, n))
    
    i, j = 0, 0
    while i < m and j < n:
        quantity = min(supply[i], demand[j])
        allocation[i, j] = quantity
        supply[i] -= quantity
        demand[j] -= quantity
        
        if supply[i] == 0:
            i += 1
        if demand[j] == 0:
            j += 1
            
    return allocation

def minimum_cost_method(costs, supply, demand):
    supply = supply.copy()
    demand = demand.copy()
    m, n = len(supply), len(demand)
    allocation = np.zeros((m, n))
    
    while True:
        if np.all(supply == 0) or np.all(demand == 0):
            break
            
        valid_positions = [(i, j) for i in range(m) for j in range(n) 
                          if supply[i] > 0 and demand[j] > 0]
        if not valid_positions:
            break
            
        costs_valid = [costs[i][j] for i, j in valid_positions]
        min_cost_idx = np.argmin(costs_valid)
        i, j = valid_positions[min_cost_idx]
        
        quantity = min(supply[i], demand[j])
        allocation[i][j] = quantity
        supply[i] -= quantity
        demand[j] -= quantity
        
    return allocation

def vogel_approximation(costs, supply, demand):
    supply = supply.copy()
    demand = demand.copy()
    m, n = len(supply), len(demand)
    allocation = np.zeros((m, n))
    
    while True:
        if np.all(supply == 0) or np.all(demand == 0):
            break
            
        row_penalties = []
        col_penalties = []
        
        for i in range(m):
            if supply[i] > 0:
                valid_costs = [c for j, c in enumerate(costs[i]) if demand[j] > 0]
                if len(valid_costs) >= 2:
                    sorted_costs = sorted(valid_costs)
                    row_penalties.append((i, sorted_costs[1] - sorted_costs[0]))
                elif len(valid_costs) == 1:
                    row_penalties.append((i, valid_costs[0]))
                    
        for j in range(n):
            if demand[j] > 0:
                valid_costs = [costs[i][j] for i in range(m) if supply[i] > 0]
                if len(valid_costs) >= 2:
                    sorted_costs = sorted(valid_costs)
                    col_penalties.append((j, sorted_costs[1] - sorted_costs[0]))
                elif len(valid_costs) == 1:
                    col_penalties.append((j, valid_costs[0]))
        
        if not row_penalties and not col_penalties:
            break
            
        max_row_penalty = max(row_penalties, key=lambda x: x[1]) if row_penalties else (None, -1)
        max_col_penalty = max(col_penalties, key=lambda x: x[1]) if col_penalties else (None, -1)
        
        if max_row_penalty[1] >= max_col_penalty[1]:
            i = max_row_penalty[0]
            valid_costs = [(j, costs[i][j]) for j in range(n) if demand[j] > 0]
            j = min(valid_costs, key=lambda x: x[1])[0]
        else:
            j = max_col_penalty[0]
            valid_costs = [(i, costs[i][j]) for i in range(m) if supply[i] > 0]
            i = min(valid_costs, key=lambda x: x[1])[0]
        
        quantity = min(supply[i], demand[j])
        allocation[i][j] = quantity
        supply[i] -= quantity
        demand[j] -= quantity
        
    return allocation

def optimize_transport(costs, supply, demand, method='minimum_cost'):
    m, n = len(supply), len(demand)
    
    # Seleccionar método inicial
    if method == 'minimum_cost':
        initial_solution = minimum_cost_method(costs, supply, demand)
    elif method == 'vogel':
        initial_solution = vogel_approximation(costs, supply, demand)
    else:  # northwest_corner por defecto
        initial_solution = northwest_corner(supply, demand)
    
    def objective(x):
        return np.sum(x.reshape(m, n) * costs)
    
    constraints = []
    for i in range(m):
        def supply_constraint(x, i=i):
            return np.sum(x.reshape(m, n)[i, :]) - supply[i]
        constraints.append({'type': 'eq', 'fun': supply_constraint})
    
    for j in range(n):
        def demand_constraint(x, j=j):
            return np.sum(x.reshape(m, n)[:, j]) - demand[j]
        constraints.append({'type': 'eq', 'fun': demand_constraint})
    
    bounds = [(0, None) for _ in range(m*n)]
    
    result = minimize(
        objective,
        initial_solution.flatten(),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    
    solution = result.x.reshape(m, n)
    solution = np.where(np.abs(solution) < 1e-10, 0, solution)
    
    return solution, result.fun


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.get_json()
    costs = np.array(data['costs'])
    supply = np.array(data['supply'])
    demand = np.array(data['demand'])
    method = data.get('method', 'minimum_cost')  # Método por defecto
    
    solution, total_cost = optimize_transport(costs, supply, demand, method)
    
    return jsonify({
        'solution': solution.tolist(),
        'total_cost': float(total_cost)
    })

if __name__ == '__main__':
    app.run(debug=True)