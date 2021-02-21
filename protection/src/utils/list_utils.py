from itertools import chain

def list_intersperse(list, item):
    """Intersperses an item between every element of a list.

    Args:
        list (list): list to be interspersed
        item (any): item to intersperse into the list

    Returns:
        list: interspersed list
    """

    result = [item] * (len(list) * 2 - 1)
    result[0::2] = list
    return result

def list_flatten(l):
    if l == []:
        return l
    if isinstance(l[0], list):
        return list_flatten(l[0]) + list_flatten(l[1:])
    return l[:1] + list_flatten(l[1:])