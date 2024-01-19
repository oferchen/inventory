# expression_evaluation/factories.py
import operator
import re

from .expressions import BinaryOperator, UnaryOperator


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


class FunctionFactory:
    functions = {
        "round": round,
        "ceiling": lambda x: int(x) if x == int(x) else int(x) + 1,
        "floor": lambda x: int(x),
        "startswith": str.startswith,
        "endswith": str.endswith,
        "glob": re.search,
        "member": lambda x, y: x in y,
        "size": len,
        "conjunction": set.intersection,
        "keys": lambda x, y, z: {item.split(z)[0] for item in x.split(y)},
        "list": lambda x, y=None: x.split(y) if y else x.split(","),
        "equals": lambda x, y: x == y,
    }

    @classmethod
    def create_function(cls, function_name: str, *args: Expression) -> UnaryOperator:
        if function := cls.functions.get(function_name):
            return UnaryOperator(args[0], function)
        raise ValueError(f"Function {function_name} not supported")
