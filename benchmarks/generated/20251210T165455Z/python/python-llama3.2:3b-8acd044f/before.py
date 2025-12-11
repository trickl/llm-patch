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
            elif char == '(':
                if current_token:
                    tokens.append(current_token)
                    current_token = None
                tokens.append(Token('LPAREN', char))
            elif char == ')':
                if current_token:
                    tokens.append(current_token)
                    current_token = None
                tokens.append(Token('RPAREN', char))
            elif char in '+-*/':
                if current_token:
                    tokens.append(current_token)
                    current_token = None
                tokens.append(Token(char, char))
            else:
                if not current_token or current_token.type != 'NUMBER':
                    if current_token:
                        tokens.append(current_token)
                    current_token = Token('NUMBER', char)

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
            if token.type == 'LPAREN':
                operator_stack.append(token)
            elif token.type == 'RPAREN':
                while operator_stack[-1].type != 'LPAREN':
                    output_queue.append(operator_stack.pop())
                operator_stack.pop()
            elif token.type == 'NUMBER':
                output_queue.append(token.value)
            else:
                while (operator_stack and 
                       operator_stack[-1].type in self.precedence and 
                       self.precedence[operator_stack[-1].type] >= self.precedence[token.type]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)

        while operator_stack:
            output_queue.append(operator_stack.pop())

        return output_queue

class Evaluator:
    def __init__(self):
        pass

    def evaluate(self, tokens):
        stack = []
        for token in tokens:
            if isinstance(token, Token) and token.type == 'NUMBER':
                stack.append(int(token.value))
            elif token.type == 'PLUS' or token.type == 'MINUS':
                b = stack.pop()
                a = stack.pop()
                if token.type == 'PLUS':
                    result = a + b
                else:
                    result = -a + b
                stack.append(result)
            elif token.type == 'MULTIPLY' or token.type == 'DIVIDE':
                b = stack.pop()
                a = stack.pop()
                if token.type == 'MULTIPLY':
                    result = a * b
                else:
                    result = int(a / b)
                stack.append(result)

        return stack[0]

def main():
    tokenizer = Tokenizer()
    parser = Parser()
    evaluator = Evaluator()

    expressions = [
        "1 + 2",
        "2 * 3 + 4",
        "2 * (3 + 4)",
        "8 / 2 * (2 + 2)"
    ]

    for expression in expressions:
        tokens = tokenizer.tokenize(expression)
        parsed_tokens = parser.parse(tokens)
        result = evaluator.evaluate(parsed_tokens)

        print(f"{expression} => {result}")

if __name__ == '__main__':
    main()