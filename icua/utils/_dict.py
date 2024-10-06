from collections.abc import Mapping

__all__ = ("dict_diff",)


def dict_diff(old: dict, new: dict) -> dict:
    """Compare two dictionaries and return a new dictionary containing the differences.

    For nested dictionaries, the function compares them recursively.
    For other collections, if any elements are different, the entire collection is returned.

    Args:
        old (dict): The first dictionary to compare.
        new (dict): The second dictionary to compare.

    Returns:
        dict: A dictionary containing values from `new` that differ from `old`.
    """
    diff = {}

    # Get the union of keys from both dictionaries
    all_keys = set(old.keys()).union(set(new.keys()))

    for key in all_keys:
        val1 = old.get(key)
        val2 = new.get(key)

        if isinstance(val1, Mapping) and isinstance(val2, Mapping):
            # If both values are dictionaries, recursively compare them
            nested_diff = dict_diff(val1, val2)
            if nested_diff:
                diff[key] = nested_diff
        elif val1 != val2:
            # If the values are different or if one of them is missing, record the difference
            diff[key] = val2
    return diff
