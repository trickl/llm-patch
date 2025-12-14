import re

class Tokenizer:
    def tokenize(self, expression):
    return list(filter(None, re.split(r'(\d+|\+|-|\*|/|\(|\))', expression.strip())))

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):
        return self.expression()

    def expression(self):
        result = self.term()
        while self.pos < len(self.tokens) and (self.tokens[self.pos] == '+' or self.tokens[self.pos] == '-'):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.term()
            if op == '+':
                result += right
            else:
                result -= right
        return result

    def term(self):
        result = self.factor()
        while self.pos < len(self.tokens) and (self.tokens[self.pos] == '*' or self.tokens[self.pos] == '/'):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.factor()
            if op == '*':
                result *= right
            else:
                result //= right
        return result

    def factor(self):
        if self.tokens[self.pos].isdigit():
            value = int(self.tokens[self.pos])
            self.pos += 1
            return value
        elif self.tokens[self.pos] == '(':
            self.pos += 1
            value = self.expression()
            if self.tokens[self.pos] != ')':
                raise ValueError("Expected )")
            self.pos += 1
            return value
        elif self.tokens[self.pos] == '-':
            self.pos += 1
            return -self.factor()


class Evaluator:
    def evaluate(self, expression):
        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize(expression)
        parser = Parser(tokens)
        return parser.parse()


if __name__ == '__main__':
    evaluator = Evaluator()
    print(evaluator.evaluate("1 + 2"))  # Output: 3
    print(evaluator.evaluate("2 * 3 + 4"))  # Output: 10
    print(evaluator.evaluate("2 * (3 + 4)"))  # Output: 14
    print(evaluator.evaluate("8 / 2 * (2 + 2)"))  # Output: 16
