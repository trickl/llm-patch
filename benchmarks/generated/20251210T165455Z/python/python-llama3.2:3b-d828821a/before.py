import re

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

class Tokenizer:
    def tokenize(self, expression):
        tokens = []
        current_token = None
        for char in expression:
            if char.isspace():
                continue
            if not current_token or (current_token.type == 'NUMBER' and char.isdigit()):
                if current_token:
                    tokens.append(current_token)
                current_token = Token('NUMBER', char)
            elif char in '+-*/()':
                if current_token:
                    tokens.append(current_token)
                current_token = Token(char, char)
            else:
                raise ValueError(f"Invalid character '{char}'")
        if current_token:
            tokens.append(current_token)
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
            elif token.type == 'OP':
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
        return result

    def _evaluate(self, expression):
        stack = []
        for token in expression:
            if isinstance(token, int):
                stack.append(token)
            elif token == '-':
                value = stack.pop()
                stack.append(-value)
            else:
                right = stack.pop()
                left = stack.pop()
                result = self._binary_operation(left, right, token)
                stack.append(result)
        return stack[0]

    def _binary_operation(self, left, right, operator):
        if operator == '+':
            return left + right
        elif operator == '-':
            return left - right
        elif operator == '*':
            return left * right
        elif operator == '/':
            return int(left / right)

def main():
    evaluator = Evaluator()
    print(evaluator.evaluate("1 + 2"))  # Output: 3
    print(evaluator.evaluate("2 * 3 + 4"))  # Output: 10
    print(evaluator.evaluate("2 * (3 + 4)"))  # Output: 14
    print(evaluator.evaluate("8 / 2 * (2 + 2)"))  # Output: 16

if __name__ == '__main__':
    main()