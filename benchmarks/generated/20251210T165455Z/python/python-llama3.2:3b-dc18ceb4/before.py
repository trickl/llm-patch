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
                current_token = Token('NUMBER', char)
            elif not current_token or (current_token.type != 'OPERATOR' and char in '+-*/()'):
                if current_token:
                    tokens.append(current_token)
                current_token = Token(char, None)
            else:
                current_token.value += char
        if current_token:
            tokens.append(current_token)
        return tokens

class Parser:
    def __init__(self):
        self precedence = {'*': 1, '/': 1, '+': 2, '-': 2}

    def parse(self, tokens):
        output_queue = []
        operator_stack = []

        for token in tokens:
            if isinstance(token, Token) and token.type == 'NUMBER':
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
        stack = []
        for token in expression:
            if isinstance(token, Token) and token.type == 'NUMBER':
                stack.append(int(token.value))
            elif token.type == 'OPERATOR':
                operand2 = stack.pop()
                operand1 = stack.pop()
                if token.value == '+':
                    result = operand1 + operand2
                elif token.value == '-':
                    result = operand1 - operand2
                elif token.value == '*':
                    result = operand1 * operand2
                elif token.value == '/':
                    result = int(operand1 / operand2)
                stack.append(result)

        return stack[0]

def main():
    tokenizer = Tokenizer()
    parser = Parser()
    evaluator = Evaluator()

    expressions = [
        ["3", "+", "4", "*", "(", "2", "-", "1")],
        ["1", "+", "2"],
        ["2", "*", "3", "+", "4"],
        ["8", "/", "2", "*", "(", "2", "+", "2")],
    ]

    for expression in expressions:
        tokens = tokenizer.tokenize(" ".join(expression))
        output_queue = parser.parse(tokens)
        result = evaluator.evaluate(output_queue)

        print(f"{expression} => {result}")

if __name__ == '__main__':
    main()