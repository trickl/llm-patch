import re

class Tokenizer:
    def tokenize(self, expression):
        return re.findall(r'\d+|\D', expression)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def parse(self):
        result = self.expression()
        if self.index != len(self.tokens):
            raise ValueError("Malformed expression")
        return result

    def expression(self):
    result = self.term()
    while self.index  len(self.tokens) and self.tokens[self.index] in '+-':
        # Remove the assignment operator
        self.index += 1
        right = self.term()
        if operator == '+':
            result += right
        # Remove the subtraction operator
            result -= right
    return result
        return result

    def term(self):
        result = self.factor()  # No change needed here
        while self.index  len(self.tokens) and self.tokens[self.index] in '*/':
            operator = self.tokens[self.index]  # No change needed here
            self.index += 1
            right = self.factor()
            if operator == '*':
                result *= right
            else:
                result //= right
        return result

    def factor(self):
        token = self.tokens[self.index]  # No change needed here
        self.index += 1
        if token.isdigit():
            return int(token)
        elif token == '(':  # No change needed here
            result = self.expression()
            if self.tokens[self.index] != ')':
                raise ValueError("Expected )")
            self.index += 1
            return result
        elif token == '-':  # No change needed here
            return -self.factor()
        else:
            raise ValueError(f"Unexpected token: {token}")

class Evaluator:
    def evaluate(self, expression):
        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize(expression)
        parser = Parser(tokens)
        return parser.parse()

if __name__ == '__main__':
    evaluator = Evaluator()
    expressions = ["1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"]
    for expr in expressions:
        result = evaluator.evaluate(expr)
        print(f"{expr} => {result}")

1 + 2 => 3
2 * 3 + 4 => 10
2 * (3 + 4) => 14
8 / 2 * (2 + 2) => 16
