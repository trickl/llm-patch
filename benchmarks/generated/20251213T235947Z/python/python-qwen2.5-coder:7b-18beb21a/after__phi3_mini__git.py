import re

class Tokenizer:
    def tokenize(self, expression):
        tokens = re.findall(r'\d+|\+|-|\*|/|\(|\)', expression)
        return tokens

class Evaluator:
    def evaluate(self, tokens):
        stack = []
        operators = {'+': self.add, '-': self.subtract, '*': self.multiply, '/': self.divide}
        
        for token in tokens:
            if token.isdigit():
                stack.append(int(token))
            elif token in operators:
                while (stack and stack[-1] != '(' and
                       operators[token]['precedence'] <= operators[stack[-1]]['precedence']):
                    right = stack.pop()
                    left = stack.pop()
                    op = stack.pop()
                    stack.append(op(left, right))
                stack.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    right = stack.pop()
                    left = stack.pop()
                    op = stack.pop()
                    stack.append(op(left, right))
                stack.pop()  # Remove the '('
        
        while len(stack) > 1:
            right = stack.pop()
            left = stack.pop()
            op = stack.pop()
            stack.append(op(left, right))
        
        return stack[0]

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Division by zero")
        return a // b

class Parser:
    def parse(self, tokens):
        for i in range(len(tokens)):
            if tokens[i] == '-' and (i == 0 or tokens[i-1] in '(*(')):
                tokens[i] = '+'
                tokens.insert(i+1, -int(tokens[i+1]))
        return tokens

class ExpressionEvaluator:
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.parser = Parser()
        self.evaluator = Evaluator()

    def evaluate(self, expression):
        tokens = self.tokenizer.tokenize(expression)
        parsed_tokens = self.parser.parse(tokens)
        result = self.evaluator.evaluate(parsed_tokens)
        return result

if __name__ == '__main__':
    evaluator = ExpressionEvaluator()
    
    expressions = [
        "1 + 2",
        "2 * 3 + 4",
        "2 * (3 + 4)",
        "8 / 2 * (2 + 2)"
    ]
    
    for expr in expressions:
        result = evaluator.evaluate(expr)
        print(f"{expr} => {result}")