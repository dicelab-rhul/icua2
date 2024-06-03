def bounding_rectangle(rectangles):
    """
    Computes the bounding rectangle given a list of rectangles represented as dictionaries.

    Args:
        rectangles (list[dict]): A list of dictionaries representing rectangles.
            Each dictionary should have keys 'x', 'y', 'width', and 'height' representing
            the x and y coordinates of the top-left corner, and the width and height of
            each rectangle, respectively.

    Returns:
        dict: A dictionary representing the bounding rectangle.
            The dictionary contains keys 'x', 'y', 'width', and 'height' representing
            the x and y coordinates of the top-left corner, and the width and height of
            the bounding rectangle, respectively.

    Example:
        >>> rectangles = [{'x': 0, 'y': 0, 'width': 320, 'height': 320},
        ...               {'x': 100, 'y': 100, 'width': 200, 'height': 200},
        ...               {'x': 150, 'y': 150, 'width': 50, 'height': 50}]
        >>> compute_bounding_rectangle(rectangles)
        {'x': 0, 'y': 0, 'width': 420, 'height': 420}
    """

    # Initialize min and max values
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    # Iterate over the rectangles to find min and max values
    for rect in rectangles:
        min_x = min(min_x, rect["x"])
        min_y = min(min_y, rect["y"])
        max_x = max(max_x, rect["x"] + rect["width"])
        max_y = max(max_y, rect["y"] + rect["height"])

    # Compute width and height of bounding rectangle
    width = max_x - min_x
    height = max_y - min_y

    # Construct the bounding rectangle
    bounding_rect = {"x": min_x, "y": min_y, "width": width, "height": height}

    return bounding_rect
