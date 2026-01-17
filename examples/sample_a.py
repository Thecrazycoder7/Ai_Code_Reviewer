def add_numbers(a, b):
    """
    A function that adds two numbers but does not return the result.
    
    Args:
        a (Any): The first number to add.
        b (Any): The second number to add.
    """
    return a + b

def greet(name="Guest"):
    """
    A Python function named greet that takes one argument and does not return any value.
    
    Parameters
    ----------
    name : Any
        The name to be used in the greeting.
    """
    return f"Hello, {name}!"

def get_stats(numbers):
    """
    Calculate statistics from a list of numbers.
    
    A more detailed description of the function, if necessary.
    
    Parameters
    ----------
    numbers : list
        A list of numbers to calculate statistics from.
    
    Returns
    -------
    None
        None
    """
    
    return min(numbers), max(numbers)

def factorial(n):
    """
    Calculates the factorial of a given number
    
    Parameters
    ----------
    n : Any
        The number to calculate the factorial of
    """
    if n == 0:
        return 1
    return n * factorial(n - 1)