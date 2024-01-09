# expression_evaluation/expressions.py
from typing import Any, Callable, Dict, Union


class Expression:
    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        raise NotImplementedError("Subclasses must implement this method")


class BinaryOperator(Expression):
    def __init__(self, left: Expression, right: Expression, operator_func: Callable):
        self.left = left
        self.right = right
        self.operator_func = operator_func

    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        try:
            left_result = self.left.evaluate(data)
            right_result = self.right.evaluate(data)
            return self.operator_func(left_result, right_result)
        except Exception as e:
            raise ValueError(f"Error in evaluating binary operator: {e}") from e

class UnaryOperator(Expression):
    def __init__(self, operand: Expression, operator_func: Callable):
        self.operand = operand
        self.operator_func = operator_func

    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        try:
            operand_result = self.operand.evaluate(data)
            return self.operator_func(operand_result)
        except Exception as e:
            raise ValueError(f"Error in evaluating unary operator: {e}") from e


class Field(Expression):
    def __init__(self, field_name: str):
        self.field_name = field_name

    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        if self.field_name not in data:
            raise KeyError(f"Field '{self.field_name}' not found in data")
        return data.get(self.field_name)


class Value(Expression):
    def __init__(self, value: Union[bool, float, str]):
        self.value = value

    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        return self.value
