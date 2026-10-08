"""Editable candidate algorithms. Integer arithmetic keeps feasibility exact."""
import random

NAMES = ('first_fit', 'first_fit_decreasing', 'best_fit_decreasing', 'randomized_best_fit')


def solve(instance, name, seed=0):
    if name not in NAMES:
        raise ValueError('unknown solver')
    items, cap = instance['items'], instance['capacity']
    order = list(range(len(items)))
    weight = lambda i: (max(v / c for v, c in zip(items[i], cap)),
                        sum(v / c for v, c in zip(items[i], cap)))
    if name != 'first_fit':
        order.sort(key=weight, reverse=True)
    if name == 'randomized_best_fit':
        random.Random(seed).shuffle(order)
    loads, assignment = [], [None] * len(items)
    for i in order:
        fits = [b for b, load in enumerate(loads)
                if all(x + y <= c for x, y, c in zip(load, items[i], cap))]
        if not fits:
            b = len(loads)
            loads.append([0] * len(cap))
        elif name in ('best_fit_decreasing', 'randomized_best_fit'):
            b = min(fits, key=lambda b: sum((c-loads[b][d]-items[i][d])/c
                                           for d, c in enumerate(cap)))
        else:
            b = fits[0]
        for d, value in enumerate(items[i]):
            loads[b][d] += value
        assignment[i] = b
    return assignment
