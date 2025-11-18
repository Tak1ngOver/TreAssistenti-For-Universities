# core/compose.py
from functools import reduce
from typing import Callable, Any, Tuple, TypeVar, Iterable

T = TypeVar("T")
R = TypeVar("R")

def compose(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """
    Возвращает композицию функций, применяемую справа налево.
    compose(f, g, h)(x) == f(g(h(x)))

    Если передано 0 функций -> возвращается identity.
    Если передана 1 функция -> она возвращается как есть.
    """
    if not funcs:
        return lambda x: x

    # reduce справа налево: start = last func, then wrap
    def composed(*args, **kwargs):
        # применяем последнюю функцию с исходными аргументами
        result = funcs[-1](*args, **kwargs)
        # затем применяем остальные справа-налево
        for f in reversed(funcs[:-1]):
            result = f(result)
        return result

    return composed

def pipe(x: T, *funcs: Callable[..., Any]) -> Any:
    """
    Пропускает значение x через последовательность функций слева направо.
    pipe(x, f, g, h) == h(g(f(x)))

    Если funcs пуст - возвращает x.
    """
    result = x
    for f in funcs:
        result = f(result)
    return result
