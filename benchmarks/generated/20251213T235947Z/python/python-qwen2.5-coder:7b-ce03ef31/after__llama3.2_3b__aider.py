import re

class Tokenizer:
    def tokenize(self, expression):
    return list(filter(None, re.split(r'(\d+|\+|-|\*|/|\(|\))', expression.strip()))
^

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):
        return self.parse_expression()

    def parse_expression(self):
        result = self.parse_term()
        while self.pos < len(self.tokens) and (self.tokens[self.pos] == '+' or self.tokens[self.pos] == '-'):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.parse_term()
            if op == '+':
                result += right
            else:
                result -= right
        return result

    def parse_term(self):
        result = self.parse_factor()
        while self.pos < len(self.tokens) and (self.tokens[self.pos] == '*' or self.tokens[self.pos] == '/'):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.parse_factor()
            if op == '*':
                result *= right
            else:
                result //= right
        return result

    def parse_factor(self):
        token = self.tokens[self.pos]
        if isinstance(token, int):
            self.pos += 1
            return token
        elif token == '-':
            self.pos += 1
            return -self.parse_factor()
        elif token == '(':
            self.pos += 1
            result = self.parse_expression()
            if self.tokens[self.pos] != ')':
                raise ValueError("Expected closing parenthesis")
            self.pos += 1
            return result
        else:
            raise ValueError(f"Unexpected token: {token}")


class Evaluator:
    def evaluate(self, expression):
        tokens = Tokenizer().tokenize(expression)
        parser = Parser(tokens)
        return parser.parse()


if __name__ == '__main__':
    evaluator = Evaluator()
    print(evaluator.evaluate("1 + 2"))  # Output: 3
    print(evaluator.evaluate("2 * 3 + 4"))  # Output: 10
    print(evaluator.evaluate("2 * (3 + 4)"))  # Output: 14
    print(evaluator.evaluate("8 / 2 * (2 + 2)"))  # Output: 16
