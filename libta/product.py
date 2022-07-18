from libta.nta import *
from libta.path_analysis import *
from collections import deque


# Unpacks expression to be used in NTAHelper's createTemplate function
# Returns a list of (clock, op, rval) tuple
def unpack_expr(expr):
    ret = []
    expr_list = get_expression_list(expr)
    for exp in expr_list:
        ret.append((str(exp[0].toString()), exp.getKind(), exp[1].getValue()))
    return ret


# Computes product of two TA
# Takes templates from same NTA as arguments, such as product(nta.templates[0], nta.templates[1])
# TODO: Tests to be written. An example automata for to be used with product computation can be found in tests/product_example.xml
def product(template1, template2, name="product"):
    clocks = list(find_used_clocks(template1.edges).union(
        find_used_clocks(template2.edges)))
    product_states = [(  # List of locations of new TA
        f"{str(template1.initial_location.uid.getName())}_{str(template2.initial_location.uid.getName())}",
        unpack_expr(template1.initial_location.invariant) +
        unpack_expr(template2.initial_location.invariant),
        False
    )]
    product_edges = []  # List of edges of new TA
    state_queue = deque()  # Initialize the queue of locations to be visited
    state_queue.append((template1.initial_location,
                       template2.initial_location))
    while len(state_queue):
        l1, l2 = state_queue.pop()
        for e1 in template1.selist[l1]:
            for e2 in template2.selist[l2]:
                # TODO: Intersection A1^A2
                l1_ = e1.dst
                l2_ = e2.dst
                if e1.sync.getSize() == e2.sync.getSize() == 0:
                    s1 = (
                        f"{str(l1.uid.getName())}_{str(l2_.uid.getName())}",
                        unpack_expr(l1.invariant) +
                        unpack_expr(l2_.invariant),
                        False
                    )
                    product_edges.append((
                        f"{str(l1.uid.getName())}_{str(l2.uid.getName())}",
                        f"{str(l1.uid.getName())}_{str(l2_.uid.getName())}",
                        "",  # TODO: Actions
                        unpack_expr(e2.guard),
                        unpack_expr(e2.assign),
                        []  # TODO: Sync
                    ))
                    if s1 not in product_states:
                        product_states.append(s1)
                        state_queue.append((l1, l2_))

                    s2 = (
                        f"{str(l1_.uid.getName())}_{str(l2.uid.getName())}",
                        unpack_expr(l1_.invariant) +
                        unpack_expr(l2.invariant),
                        False
                    )
                    product_edges.append((
                        f"{str(l1.uid.getName())}_{str(l2.uid.getName())}",
                        f"{str(l1_.uid.getName())}_{str(l2.uid.getName())}",
                        "",  # TODO: Actions
                        unpack_expr(e1.guard),
                        unpack_expr(e1.assign),
                        []  # TODO: Sync
                    ))
                    if s2 not in product_states:
                        product_states.append(s2)
                        state_queue.append((l1_, l2))
                elif ((e1.sync.getSize() == 0 or e2.sync.getSize() == 0)
                        or (not e1.sync[0].equal(e2.sync[0]))
                        or (e1.sync.getSync() == e2.sync.getSync())):
                    continue

                s = (
                    f"{str(l1_.uid.getName())}_{str(l2_.uid.getName())}",
                    unpack_expr(l1_.invariant) +
                    unpack_expr(l2_.invariant),
                    False
                )
                product_edges.append((
                    f"{str(l1.uid.getName())}_{str(l2.uid.getName())}",
                    f"{str(l1_.uid.getName())}_{str(l2_.uid.getName())}",
                    "",  # TODO: Actions
                    unpack_expr(e1.guard) + unpack_expr(e2.guard),
                    unpack_expr(e1.assign) + unpack_expr(e2.assign),
                    []  # TODO: Sync
                ))
                if s not in product_states:
                    product_states.append(s)
                    state_queue.append((l1_, l2_))

    nta_product = NTAHelper(name=name)
    nta_product.addClocks(clocks)
    product_states[0] = (product_states[0][0], product_states[0][1], True)
    nta_product.createTemplate("product", product_states, product_edges)
    return nta_product
