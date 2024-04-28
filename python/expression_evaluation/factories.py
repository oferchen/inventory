# expression_evaluation/factories.py
import operator
import re
from typing import Any, Callable, Dict, List, Union

from .expressions import BinaryOperator, Expression, UnaryOperator


class FunctionFactory:
    functions: Dict[str, Callable[..., Union[Any, str]]] = {}

    @classmethod
    def register(cls, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to register a new function in the factory. It ensures that the function
        does not overwrite an existing function with the same name.
        """
        if func.__name__ in cls.functions:
            raise ValueError(f"Function {func.__name__} is already registered.")
        cls.functions[func.__name__] = func
        return func

    @classmethod
    def create_function(cls, function_name: str, *args: Expression) -> UnaryOperator:
        """
        Creates a UnaryOperator for the specified function name with provided arguments.
        Raises an error if the function is not registered.
        """
        if function := cls.functions.get(function_name):
            return UnaryOperator(args[0], function)
        raise ValueError(f"Function {function_name} not supported")

@FunctionFactory.register
def round(x: float) -> float:
    return round(x)

@FunctionFactory.register
def ceiling(x: float) -> int:
    return int(x) if x == int(x) else int(x) + 1

@FunctionFactory.register
def floor(x: float) -> int:
    return int(x)

@FunctionFactory.register
def startswith(x: str, y: str) -> bool:
    return x.startswith(y)

@FunctionFactory.register
def endswith(x: str, y: str) -> bool:
    return x.endswith(y)

@FunctionFactory.register
def glob(x: str, y: str) -> bool:
    """
    Searches for the regex pattern 'y' in the string 'x' and returns True if the pattern is found, otherwise False.
    """
    return re.search(y, x) is not None

@FunctionFactory.register
def member(x: Any, y: List) -> bool:
    return x in y

@FunctionFactory.register
def size(x: List) -> int:
    return len(x)

@FunctionFactory.register
def conjunction(x: set, y: set) -> set:
    return x.intersection(y)

@FunctionFactory.register
def keys(x: str, y: str, z: str) -> set:
    return {item.split(z)[0] for item in x.split(y)}

@FunctionFactory.register
def list_split(x: str, y: str = ',') -> List:
    return x.split(y)

@FunctionFactory.register
def equals(x: Any, y: Any) -> bool:
    return x == y

@FunctionFactory.register
def extract_keys(x: str, y: str, z: str) -> set:
    return {item.split(z)[0] for item in x.split(y)}


@FunctionFactory.register
def list(x: str, y: str = "") -> List:
    return x.split(y) if y else x.split(",")


class OperatorFactory:
    operators = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "%": operator.mod,
        "&&": operator.and_,
        "||": operator.or_,
        "!": operator.not_,
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
        "=~": re.match,
        "is": operator.is_,
        "&": operator.and_,
        "|": operator.or_,
        "~": operator.xor,
        "^": operator.pow,
        "<<": operator.lshift,
        ">>": operator.rshift,
        ">>>": operator.rshift,
    }

    @classmethod
    def create_operator(cls, operator_symbol, left, right):
        if operator_func := cls.operators.get(operator_symbol):
            return BinaryOperator(left, right, operator_func)
        raise ValueError(f"Operator {operator_symbol} not supported")
