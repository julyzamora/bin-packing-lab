
def check_instance(instance):
    cap = instance['capacity']
    if not cap or any(type(c) is not int or c <= 0 for c in cap):
        raise ValueError('capacities must be positive integers')
    for item in instance['items']:
        if len(item) != len(cap) or any(type(v) is not int or v < 0 or v > c
                                      for v, c in zip(item, cap)) or not any(item):
            raise ValueError('invalid or individually infeasible item')


def validate(instance, assignment, initial=None, max_moves=None):
    """Authoritative feasibility; candidate scores are never accepted."""
    check_instance(instance)
    if not isinstance(assignment, list) or len(assignment) != len(instance['items']):
        raise ValueError('exactly one bin per item required')
    loads = {}
    for item, b in zip(instance['items'], assignment):
        if type(b) is not int or b < 0:
            raise ValueError('bin IDs must be nonnegative integers')
        load = loads.setdefault(b, [0] * len(item))
        for d, value in enumerate(item):
            load[d] += value
            if load[d] > instance['capacity'][d]:
                raise ValueError('capacity exceeded')
    moved = None
    if initial is not None:
        validate(instance, initial)
        moved = sum(a != b for a, b in zip(initial, assignment))
        if max_moves is not None and moved > max_moves:
            raise ValueError('movement budget exceeded')
    elif max_moves is not None:
        raise ValueError('movement budget requires initial assignment')
    return {'bins': len(loads), 'moves': moved}


def lower_bound(instance):
    check_instance(instance)
    return max((sum(x[d] for x in instance['items']) + c - 1) // c
               for d, c in enumerate(instance['capacity']))
