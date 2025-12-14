import re
from enum import Enum

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Tokenizer:
    def tokenize(self, expression):
        tokens = re.findall(r'\d+|[+\-*/()]", expression)
        tokens = [Token('NUMBER', int(token)) if token.isdigit() else Token(token, token) for token in tokens]
        return tokens

class OperatorPrecedence(Enum):
    LOWEST = 1
    MUL_DIV = 2
    ADD_SUB = 3
    UNARY = 4

precedence = {
    '+': OperatorPrecedence.ADD_SUB,
    '-': OperatorPrecedence.ADD_SUB,
    '*': OperatorPrecedence.MUL_DIV,
    '/': OperatorPrecedence.MUL_DIV,
}

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def consume(self):
        token = self.peek()
        self.pos += 1
        return token

    def parse(self):
        return self.expression()

    def expression(self):
        left = self.parse_term()
        while self.peek().type in ('+', '-'):
            operator = self.consume()
            right = self.parse_term()
            left = Node(operator.type, left, right)
        return left

    def term(self):
        if self.peek().type == 'NUMBER':
            token = self.consume()
            return Node('NUMBER', None, Token('NUMBER', token.value))
        elif self.peek().value == '(':
            self.consume()
            result = self.expression()
            if self.peek().value != ')':
                raise SyntaxError("Expected ')'")
            self.consume()
            return result
        else:
            raise SyntaxError(f"Unexpected token: {self.peek()}")

    def parse_term(self):
        left = self.factor()
        while self.peek().type == '*':
            operator = self.consume()
            right = self.parse_factor()
            left = Node(operator.type, left, right)
        return left

    def factor(self):
        if self.peek().value == '-':
            operator = self.consume()
            result = self.parse_term()
            return Node('UNARY', operator, result)
        else:
            return self.term()

class Node:
    def __init__(self, type, left=None, right=None):
        self.type = type
        self.left = left
        self.right = right

    def evaluate(self):
        if self.type == 'NUMBER':
            return self.left.value
        elif self.type == '+':
            return self.left.evaluate() + self.right.evaluate()
        elif self.type == '-':
            return self.left.evaluate() - self.right.evaluate()
        elif self.type == '*':
            return self.left.evaluate() * self.right.evaluate()
        elif self.type == '/':
            right_val = self.right.evaluate()
            if right_val == 0:
                raise ZeroDivisionError("division by zero")
            return self.left.evaluate() / right_val
        elif self.type == 'UNARY':
            return -self.right.evaluate()

class Evaluator:
    def evaluate(self, expression):
        tokens = Tokenizer().tokenize(expression)
        tree = Parser(tokens).parse()
        return tree.evaluate()

if __name__ == '__main__':
    evaluator = Evaluator()
    print(evaluator.evaluate("1 + 2"))  # 3
    print(evaluator.evaluate("2 * 3 + 4"))  # 10
    print(evaluator.evaluate("2 * (3 + 4)"))  # 14
    print(evaluator.evaluate("8 / 2 * (2 + 2)"))  # 16
