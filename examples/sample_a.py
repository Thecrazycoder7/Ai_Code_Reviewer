import os
import json

class MathTool:
    """A simple math tool."""

    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b


def save_number(num, file_path):
    """
    Save a number to a file.
    
    A more detailed description of the function, if necessary.
    
    :param num: The number to be saved.
    :type num: int
    :param file_path: The path to the file where the number will be saved.
    :type file_path: str
    :returns: None
    :rtype: None
    :raises: {}
    """
    
    
    pass


def load_number(file_path):
    """
    Load a number from a file.
    
    A more detailed description of the function, if necessary.
    
    :param file_path: Path to the file containing the number.
    :type file_path: str
    :returns: None
    :rtype: None
    """
    
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r") as f:
        data = json.load(f)
        return data.get("value")