from ortools.linear_solver import pywraplp
from libta import *
Constants = UTAP.Constants


# Checks if given path exists
def path_exists(path):
    if len(path) == 0:
        return False

    if len(path) == 1:
        return True # TODO: Check if the state exists

    path = path[1:]
    curr_dst = path[0].dst
    for edge in path[1:]:
        if not (curr_dst.uid == edge.src.uid):
            return False

        curr_dst = edge.dst

    return True


# Returns a path from state labels
# Its first element is the source state and others are edge objects.
def construct_path_from_labels(states, template):
    path = []
    if len(states) == 1:
        for state in template.states:
            if state.uid.getName() == states[0]:
                return [state]

    for i in range(0, len(states) - 1):
        src = states[i]
        dst = states[i + 1]

        edge_found = False
        for edge in template.edges:
            if edge.src.uid.getName() == src and edge.dst.uid.getName() == dst:
                edge_found = True
                path.append(edge)
                break

        if not edge_found:
            return []

    return [path[0].src] + path


# Returns the set of clocks used in the given path
def find_used_clocks(edge_list):
    res = set()
    for edge in edge_list:
        if edge.src.invariant.usesClock():
            res = res.union(get_symbols(edge.src.invariant))
        if edge.dst.invariant.usesClock():
            res = res.union(get_symbols(edge.dst.invariant))
        if edge.guard.usesClock():
            res = res.union(get_symbols(edge.guard))
        if edge.sync.usesClock():
            res = res.union(get_symbols(edge.sync))
        if edge.assign.usesClock():
            res = res.union(get_symbols(edge.assign))
        if edge.src.invariant.usesClock(): # TODO: Check if symbols are not clocks
            res = res.union(get_symbols(edge.src.invariant))

    return res


# Returns the parameters in a given expression
def find_params_in_exp(exp):
    params = set()
    if exp[0].getKind() == Constants.IDENTIFIER or exp[0].getKind() == Constants.MINUS:
        if exp.usesClock() and exp[1].getKind() == Constants.IDENTIFIER:
            params.add(exp[1].toString())
    else:
        if exp[0].usesClock() and (exp[0][0][1].getKind() == Constants.IDENTIFIER or exp[0][0][1].getKind() == Constants.MINUS):
            # TODO: May have errors, check further with tests
            params.add(exp[0][1][1].toString())

        if exp[1].usesClock() and (exp[0][1][1].getKind() == Constants.IDENTIFIER or exp[0][1][1].getKind() == Constants.MINUS):
            params.add(exp[0][1][1].toString())

    return params


# Returns the parameters in a path
def find_parameters(edge_list):
    params = set()
    for edge in edge_list:
        src_exp_list = get_expression_list(edge.src.invariant)
        for exp in src_exp_list:
            params = params.union(find_params_in_exp(exp))

        guard_exp_list = get_expression_list(edge.guard)
        for exp in guard_exp_list:
            params = params.union(find_params_in_exp(exp))

    return params


# Constructs the rows for a location or transition, depending on the type of the expression the location has
def calculate_subrow(exp, i, cumul_var, var_count, v, params, epsilon):
    sub_A = []
    sub_B = []
    if exp.getKind() == Constants.LE or exp.getKind() == Constants.LT:
        a = [0 for _ in range(var_count)]
        a[cumul_var:i+1] = [1 for _ in range(i - cumul_var + 1)]
        exp_params = list(find_params_in_exp(exp))
        for param in exp_params:
            a[var_count - len(params) + params.index(param)] = -1
        sub_A.append(a)

        if exp.getKind() == Constants.LT:
            sub_B.append(v + epsilon)
        else:
            sub_B.append(v)
    elif exp.getKind() == Constants.GE or exp.getKind() == Constants.GT:
        a = [0 for _ in range(var_count)]
        a[cumul_var:i+1] = [-1 for _ in range(i - cumul_var + 1)]
        exp_params = list(find_params_in_exp(exp))
        for param in exp_params:
            a[var_count - len(params) + params.index(param)] = 1
        sub_A.append(a)

        if exp.getKind() == Constants.GT:
            sub_B.append(-(v + epsilon))
        else:
            sub_B.append(-v)
    elif exp.getKind() == Constants.EQ:
        a = [0 for _ in range(var_count)]
        a[cumul_var:i+1] = [1 for _ in range(i - cumul_var + 1)]
        exp_params = list(find_params_in_exp(exp))
        for param in exp_params:
            a[var_count - len(params) + params.index(param)] = -1 
        sub_A.append(a)
        sub_B.append(v)

        a = [0 for _ in range(var_count)]
        a[cumul_var:i+1] = [-1 for _ in range(i - cumul_var + 1)]
        exp_params = list(find_params_in_exp(exp))
        for param in exp_params:
            a[var_count - len(params) + params.index(param)] = 1
        sub_A.append(a)
        sub_B.append(-v)

    return sub_A, sub_B


# Handle the construction of a row for a location or expression if its expression has more than one subexpressions
def calculate_rows(exp, i, clocks, cumul_vars, cumul_vals, var_count, params, A, B, epsilon):
    if exp[0].getKind() == Constants.IDENTIFIER:
        cumul_var = cumul_vars[clocks.index(exp[0].toString())]
        cumul_val = cumul_vals[str(exp[0].toString())]
        v = exp[1].getValue() - cumul_val
        sub_A, sub_B = calculate_subrow(exp, i, cumul_var, var_count, v, params, epsilon)
        A += sub_A
        B += sub_B
    else: # If the expression consists of more than two clocks, consider them seperately
        cumul_var1 = cumul_vars[clocks.index(exp[0][0].toString())]
        cumul_val1 = cumul_vals[str(exp[0][0].toString())]
        v1 = exp[1].getValue() - cumul_val1
        sub_A1, sub_B1 = calculate_subrow(exp, i, cumul_var1, var_count, v1, params, epsilon)

        cumul_var2 = cumul_vars[clocks.index(exp[0][1].toString())]
        cumul_val2 = cumul_vals[str(exp[0][1].toString())]
        v2 = -cumul_val2
        sub_A2, sub_B2 = calculate_subrow(exp, i, cumul_var2, var_count, v2, params, epsilon)

        if exp[0].getKind() == Constants.MINUS:
            for i in range(len(sub_A1)):
                temp_A = []
                temp_B = 0
                for j in range(len(sub_A1[i])):
                    temp_A.append(sub_A1[i][j] - sub_A2[i][j])
                    temp_B = sub_B1[i] - sub_B2[i]

                A.append(temp_A)
                B.append(temp_B)


# Constructs the A and B matrices for a location or transition
def calculate_constraint_matrices(path, initial_clock_values=None, epsilon=0):
    init_state = path[0]
    path = path[1:]
    
    A = []
    B = []

    if path == []: # If the path does not have any edges, use the initial state
        src_exp_list = get_expression_list(init_state.invariant)
        clocks = set()
        params = set()
        for exp in src_exp_list:
            if exp.usesClock():
                clocks = clocks.union(get_symbols(exp))
                params = params.union(find_params_in_exp(exp))

        clocks = list(clocks)
        num_clocks = len(clocks)
        cumul_vars = [0] * num_clocks
        cumul_vals = {}
        params = list(params)
        if initial_clock_values is not None:
            cumul_vals = initial_clock_values
        else:
            cumul_vals = {clock: 0 for clock in clocks}

        for exp in src_exp_list:
            if exp.usesClock():
                calculate_rows(exp, 0, clocks, cumul_vars, cumul_vals, 1, params, A, B, epsilon)

        return A, B, 1

    params = list(find_parameters(path))
    var_count = len(path) + len(params)
    clocks = list(find_used_clocks(path))
    num_clocks = len(clocks)

    cumul_vars = [0] * num_clocks
    cumul_vals = {}
    if initial_clock_values is not None:
        cumul_vals = initial_clock_values
    else:
        cumul_vals = {clock: 0 for clock in clocks}

    for i, edge in enumerate(path):
        src_exp_list = get_expression_list(edge.src.invariant) # Get the expressions in the invariant of the source state
        for exp in src_exp_list:
            if exp.usesClock():
                calculate_rows(exp, i, clocks, cumul_vars, cumul_vals, var_count, params, A, B, epsilon) # Calculate the rows of the coefficient and the constraint matrices

        guard_exp_list = get_expression_list(edge.guard)
        for exp in guard_exp_list:
            if exp.usesClock():
                calculate_rows(exp, i, clocks, cumul_vars, cumul_vals, var_count, params, A, B, epsilon)

        assign_exp_list = get_expression_list(edge.assign)
        for exp in assign_exp_list:
            if exp.usesClock():
                cumul_vars[clocks.index(exp[0].toString())] = i + 1
                cumul_vals[str(exp[0].toString())] = exp[1].getValue()

    # No need for looking to the destination, since it will be considered in the next iteration anyways. So just look at for the last edge.
    dst_exp_list = get_expression_list(path[-1].dst.invariant)
    for exp in dst_exp_list:
        if exp.usesClock():
            calculate_rows(exp, i, clocks, cumul_vars, cumul_vals, var_count, params, A, B, epsilon)

    return A, B, var_count


def is_path_realizable(path, initial_clock_vals=None, print_matrices=False, print_solver=False, epsilon=0):
    if not path_exists(path):
        if print_matrices or print_solver:
            print("Path does not exist")
        return False, []

    A, B, var_count = calculate_constraint_matrices(path, initial_clock_vals, epsilon)
    if print_matrices:
        for i in range(len(A)):
            print(A[i], "<=", B[i])

    solver = pywraplp.Solver("", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    c = {}
    for j in range(var_count):
        c[j] = solver.IntVar(0, solver.infinity(), "x[%s]" % j)

    for i in range(len(A)):
        constraint = solver.RowConstraint(-solver.infinity(), B[i], "")
        for j in range(var_count):
            constraint.SetCoefficient(c[j], A[i][j])

    if print_solver:
        print(solver.ExportModelAsLpFormat(False))

    status = solver.Solve()
    delays = []
    if status == solver.OPTIMAL:
        for i in range(var_count):
            delays.append(c[i].solution_value())

        return True, delays

    if status == solver.INFEASIBLE:
        return False, []
