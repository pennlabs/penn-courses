from collections import deque


def aggregate_rule_leaves(rules, f):
    bfs_queue = deque()
    bfs_queue.extend(rules)
    while bfs_queue:
        for child in bfs_queue.pop().children.all():
            if child.q:  # i.e., if this child is a leaf
                f(child)
            else:
                bfs_queue.append(child)
