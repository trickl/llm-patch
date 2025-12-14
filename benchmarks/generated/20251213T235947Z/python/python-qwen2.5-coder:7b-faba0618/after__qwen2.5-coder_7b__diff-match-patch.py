import re

class Tokenizer:
    def tokenize(self, expression):
        return list(filter(None, re.split(r'(\d+|\+|-|\*|/|\(|\))', expression.strip()))


class Parser:
    def __init__(self):        self.operators = {'+': 1, '-': 1, '*': 2, '/': 2}
        self.functions = []

    def parse(self, tokens):
        output = []
        operators_stack = []
        for token in tokens:
            if token.isdigit():
                output.append(int(token))
            elif token == '(':
                operators_stack.append(token)
            elif token == ')':
                while operators_stack and operators_stack[-1] != '(':
                    output.append(operators_stack.pop())
                operators_stack.pop()
            else:
                while (operators_stack and
                       operators_stack[-1] != '(' and
                       self.operators[token] <= self.operators[operators_stack[-1]]):
                    output.append(operators_stack.pop())
                operators_stack.append(token)
        while operators_stack:
            output.append(operators_stack.pop())
        return output


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
    print(evaluator.evaluate_expression("1 + 2"))  # => 3
    print(evaluator.evaluate_expression("2 * 3 + 4"))  # => 10
    print(evaluator.evaluate_expression("2 * (3 + 4)"))  # => 14
    print(evaluator.evaluate_expression("8 / 2 * (2 + 2)"))  # => 16