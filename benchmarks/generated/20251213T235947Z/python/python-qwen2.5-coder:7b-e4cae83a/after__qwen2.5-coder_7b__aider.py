import re

class Tokenizer:
    def tokenize(self, expression):
    return list(filter(None, re.split(r'(\d+|\s*[-+\*/()]\s*)', expression.strip())))

class Parser:
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}

    def parse(self, tokens):
        output = []
        operators = []
        
        for token in tokens:
            if token.isdigit():
                output.append(int(token))
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    self.apply_operator(operators, output)
                operators.pop()  # Remove the '('
            else:  # Operator
                while (operators and operators[-1] != '(' and
                       self.precedence[operators[-1]] >= self.precedence[token]):
                    self.apply_operator(operators, output)
                operators.append(token)
        
        while operators:
            self.apply_operator(operators, output)
        
        return output
    
    def apply_operator(self, operators, output):
        operator = operators.pop()
        right = output.pop()
        left = output.pop()
        if operator == '+':
            output.append(left + right)
        elif operator == '-':
            output.append(left - right)
        elif operator == '*':
            output.append(left * right)
        elif operator == '/':
            output.append(int(left / right))


class Evaluator:
    def evaluate(self, postfix):
        stack = []
        for token in postfix:
            if isinstance(token, int):
                stack.append(token)
            else:
                b = stack.pop()
                a = stack.pop()
                if token == '+':
                    stack.append(a + b)
                elif token == '-':
                    stack.append(a - b)
                elif token == '*':
                    stack.append(a * b)
                elif token == '/':
                    stack.append(int(a / b))
        return stack[0]


class ExpressionEvaluator:
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.parser = Parser()
        self.evaluator = Evaluator()

    def evaluate_expression(self, expression):
        tokens = self.tokenizer.tokenize(expression)
        postfix = self.parser.parse(tokens)
        return self.evaluator.evaluate(postfix)


if __name__ == '__main__':
    evaluator = ExpressionEvaluator()
    
    test_cases = [
        ("1 + 2", 3),
        ("2 * 3 + 4", 10),
        ("2 * (3 + 4)", 14),
        ("8 / 2 * (2 + 2)", 16)
    ]
    
    for expression, expected in test_cases:
        result = evaluator.evaluate_expression(expression)
        print(f"{expression} => {result}, Expected: {expected}")
