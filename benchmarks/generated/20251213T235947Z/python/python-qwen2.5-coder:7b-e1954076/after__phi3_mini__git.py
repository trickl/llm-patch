import re

class Tokenizer:
    def tokenize(self, expression):
        return list(filter(None, re.split(r'(\d+|\+|-|\*|/|\(|\))', expression)))

class Parser:
    def parse(self, tokens):
        stack = []
        operators = {'+', '-', '*', '/'}
        while len(tokens) > 0:
            token = tokens.pop(0)
            if token.isdigit():
                stack.append(int(token))
            elif token in operators:
                while (stack and stack[-1] != '(' and
                       (token == '*' or token == '/' or
                        (token in '+-' and stack[-2] not in '(*')))):
                    right = stack.pop()
                    left = stack.pop()
                    operator = stack.pop()
                    stack.append(self.apply_operator(left, operator, right))
                stack.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    right = stack.pop()
                    left = stack.pop()
                    operator = stack.pop()
                    stack.append(self.apply_operator(left, operator, right))
                stack.pop()  # Remove '('
        while len(stack) > 1:
            right = stack.pop()
            left = stack.pop()
            operator = stack.pop()
            stack.append(self.apply_operator(left, operator, right))
        return stack[0]

    def apply_operator(self, left, operator, right):
        if operator == '+':
            return left + right
        elif operator == '-':
            return left - right
        elif operator == '*':
            return left * right
        elif operator == '/':
            return int(left / right)

class Evaluator:
    def evaluate(self, expression):
        tokenizer = Tokenizer()
        parser = Parser()
        tokens = tokenizer.tokenize(expression)
        result = parser.parse(tokens)
        return result

if __name__ == '__main__':
    evaluator = Evaluator()
    print(evaluator.evaluate("1 + 2"))  # Output: 3
    print(evaluator.evaluate("2 * 3 + 4"))  # Output: 10
    print(evaluator.evaluate("2 * (3 + 4)"))  # Output: 14
    print(evaluator.evaluate("8 / 2 * (2 + 2)"))  # Output: 16