from itertools import groupby
 
def split_string_on_changing_char(text):
    """Splits a string on every character change.

    Args:
        text (string): text to be splitted

    Returns:
        list: list of splitted strings
    """
    return [''.join(group) for key, group in groupby(text)]
 
