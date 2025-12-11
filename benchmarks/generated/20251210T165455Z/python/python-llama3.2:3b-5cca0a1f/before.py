import re

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

class Tokenizer:
    def tokenize(self, expression):
        tokens = []
        i = 0
        while i < len(expression):
            if expression[i].isdigit():
                j = i
                while j < len(expression) and expression[j].isdigit():
                    j += 1
                token_value = int(expression[i:j])
                token_type = 'NUMBER'
                tokens.append(Token(token_type, token_value))
                i = j
            elif expression[i] in '+-*/()':
                token_type = 'OPERATOR'
                token_value = expression[i]
                tokens.append(Token(token_type, token_value))
                i += 1
            else:
                raise ValueError(f"Invalid character '{expression[i]}' at position {i}")
        return tokens

class Parser:
    def __init__(self):
        self precedence = {'+': 1, '-': 1, '*': 2, '/': 2}

    def parse(self, tokens):
        output_queue = []
        operator_stack = []

        for token in tokens:
            if token.type == 'NUMBER':
                output_queue.append(token.value)
            elif token.type == 'OPERATOR':
                while (operator_stack and 
                       self.precedence[operator_stack[-1]] >= self.precedence[token.value]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token.value)

        while operator_stack:
            output_queue.append(operator_stack.pop())

        return output_queue

class Evaluator:
    def __init__(self):
        pass

    def evaluate(self, expression):
        tokens = Tokenizer().tokenize(expression)
        parsed_expression = Parser().parse(tokens)
        result = self._evaluate(parsed_expression)
        if isinstance(result, str):
            raise ValueError(f"Invalid expression: {expression}")
        return result

    def _evaluate(self, expression):
        stack = []
        for token in expression:
            if token == '+':
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
            elif token == '-':
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)
            elif token == '*':
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
            elif token == '/':
                b = stack.pop()
                a = stack.pop()
                if b != 0:
                    stack.append(int(a / b))
                else:
                    raise ZeroDivisionError("Cannot divide by zero")
            else:
                stack.append(token)
        return stack[0]

if __name__ == '__main__':
    evaluator = Evaluator()

    print(evaluator.evaluate('1 + 2'))  # Output: 3
    print(evaluator.evaluate('2 * 3 + 4'))  # Output: 10
    print(evaluator.evaluate('2 * (3 + 4)'))  # Output: 14
    print(evaluator.evaluate('8 / 2 * (2 + 2)'))  # Output: 16

    try:
        print(evaluator.evaluate('-3 + 5'))  # Output: Invalid expression: -3 + 5
    except ValueError as e:
        print(e)

    try:
        print(evaluator.evaluate('1 / 0'))  # Output: Cannot divide by zero
    except ZeroDivisionError as e:
        print(e)