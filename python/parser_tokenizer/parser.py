# parser_tokenizer/parser.py
import re
from typing import Optional

from expression_evaluation.expressions import Expression, Field, Value
from expression_evaluation.factories import OperatorFactory


class Parser:
    def __init__(self, specification):
        self.specification = specification
        self.tokenizer = Tokenizer(specification)

    def parse(self):
        expression = self.parse_expression()
        if self.tokenizer.has_tokens():
            raise ValueError("Invalid expression")
        return expression

    def parse_expression(self, precedence=0):
        left = self.parse_operand()
        while self.tokenizer.has_tokens():
            token = self.tokenizer.peek()
            token_precedence = self.get_precedence(token)
            if token_precedence < precedence:
                return left
            self.tokenizer.next()
            right = self.parse_expression(token_precedence + 1)
            left = OperatorFactory.create_operator(token, left, right)
        return left

    def parse_operand(self) -> Expression:
        token = self.tokenizer.peek()
        if token == "(":
            self.tokenizer.next()
            expression = self.parse_expression()
            if self.tokenizer.peek() != ")":
                raise ValueError("Missing closing parenthesis")
            self.tokenizer.next()
            return expression
        elif token.startswith('"') or token.startswith("'"):
            return Value(token.strip("\"'"))
        elif token.isnumeric():
            return Value(float(token))
        elif re.match(r"^[a-zA-Z_][a-zA-Z_0-9]*$", token):
            return Field(token)
        elif token.isalnum():
            return Value(token)
        else:
            raise ValueError(f"Invalid token: {token}")

    def get_precedence(self, operator_symbol):
        precedence = {
            "&&": 1,
            "||": 1,
            "!": 2,
            "<": 3,
            "<=": 3,
            ">": 3,
            ">=": 3,
            "==": 3,
            "!=": 3,
            "=~": 3,
            "is": 3,
            "isnt": 3,
            "&": 4,
            "|": 4,
            "~": 4,
            "^": 4,
            "<<": 5,
            ">>": 5,
            ">>>": 5,
            "?": 6,
            ":": 6,
        }
        return precedence.get(operator_symbol, 0)


class Tokenizer:
    def __init__(self, specification):
        self.tokens = re.findall(
            r"\b(?:[+\-*/%]|\w+|>=?|<=?|!=|==|&&|\|\||[()])\b", specification
        )
        self.current = 0

    def peek(self) -> Optional[str]:
        if self.has_tokens():
            return self.tokens[self.current]
        return None

    def next(self):
        if self.has_tokens():
            self.current += 1

    def has_tokens(self):
        return self.current < len(self.tokens)
