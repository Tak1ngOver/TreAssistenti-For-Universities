from functools import reduce
from typing import Callable, Any, Tuple, TypeVar, Iterable

def compose(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    if not funcs:
        return lambda x: x
    def composed(*args, **kwargs):
        result = funcs[-1](*args, **kwargs)
        for f in reversed(funcs[:-1]):
            result = f(result)
        return result

    return composed

def pipe(x, *funcs: Callable[..., Any]) -> Any:
    result = x
    for f in funcs:
        result = f(result)
    return result
