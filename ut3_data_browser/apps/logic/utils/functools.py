from functools import reduce
from typing import Callable

def compose(*functions: Callable) -> Callable:
    return reduce(lambda f, g: lambda x: g(f(x)), functions, lambda x: x)
