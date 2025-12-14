import re

class Tokenizer:
    def tokenize(self, expression):
        return list(filter(None, re.split(r'(\d+|\*|/|\+|-|\(|\))', expression.strip()))^


class Parser:
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    
    def __init__(self):
        self.tokens = []
        self.index = 0

    def parse(self, tokens):
        self.tokens = tokens
        self.index = 0
        return self.expression()

    def expression(self):
        result = self.term()
        while self.index < len(self.tokens) and self.tokens[self.index] in ('+', '-'):
            operator = self.tokens[self.index]
            self.index += 1
            right = self.term()
            if operator == '+':
                result += right
            elif operator == '-':
                result -= right
        return result

    def term(self):
        result = self.factor()
        while self.index < len(self.tokens) and self.tokens[self.index] in ('*', '/'):
            operator = self.tokens[self.index]
            self.index += 1
            right = self.factor()
            if operator == '*':
                result *= right
            elif operator == '/':
                result //= right
        return result

    def factor(self):
        token = self.tokens[self.index]
        self.index += 1
        if token.isdigit():
            return int(token)
        elif token == '(':
            result = self.expression()
            if self.tokens[self.index] != ')':
                raise ValueError("Expected closing parenthesis")
            self.index += 1
            return result
        elif token == '-':
            return -self.factor()


class Evaluator:
    def evaluate(self, expression):
        tokenizer = Tokenizer()
        parser = Parser()
        tokens = tokenizer.tokenize(expression)
        return parser.parse(tokens)


if __name__ == '__main__':
    evaluator = Evaluator()
    expressions = ["1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"]
    for expr in expressions:
        result = evaluator.evaluate(expr)
        print(f"{expr} => {result}")