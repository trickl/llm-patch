import re

class Tokenizer:
    def tokenize(self, expression):
        tokens = []
        for token in re.findall(r'\b\w+\b|[+\-*/()]", expression):            if token.isdigit():
                tokens.append(int(token))
            else:
                tokens.append(token)
        return tokens

class Parser:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.tokens = []
        self.pos = 0
    
    def parse(self, expression):
        self.tokens = self.tokenizer.tokenize(expression)
        return self.expression()
    
    def expression(self):
        result = self.term()
        while self.pos < len(self.tokens) and self.tokens[self.pos] in '+-':
            operator = self.tokens[self.pos]
            self.pos += 1
            right = self.term()
            if operator == '+':
                result += right
            else:
                result -= right
        return result
    
    def term(self):
        result = self.factor()
        while self.pos < len(self.tokens) and self.tokens[self.pos] in '*/':
            operator = self.tokens[self.pos]
            self.pos += 1
            right = self.factor()
            if operator == '*':
                result *= right
            else:
                result //= right
        return result
    
    def factor(self):
        token = self.tokens[self.pos]
        self.pos += 1
        if isinstance(token, int):
            return token
        elif token == '(':
            result = self.expression()
            if self.tokens[self.pos] != ')':
                raise ValueError("Expected closing parenthesis")
            self.pos += 1
            return result
        elif token == '-':
            return -self.factor()
        else:
            raise ValueError(f"Unexpected token: {token}")

class Evaluator:
    def evaluate(self, expression):
        parser = Parser(Tokenizer())
        return parser.parse(expression)

if __name__ == '__main__':
    evaluator = Evaluator()
    print(evaluator.evaluate("1 + 2"))  # Output: 3
    print(evaluator.evaluate("2 * 3 + 4"))  # Output: 10
    print(evaluator.evaluate("2 * (3 + 4)"))  # Output: 14
    print(evaluator.evaluate("8 / 2 * (2 + 2)"))  # Output: 16
    print(evaluator.evaluate("-3 + 5"))  # Output: 2