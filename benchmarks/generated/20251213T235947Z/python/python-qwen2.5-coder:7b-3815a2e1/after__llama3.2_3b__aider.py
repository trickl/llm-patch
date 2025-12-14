import re

class Tokenizer:
    def __init__(self, input_string):
        self.input_string = input_string.replace(" ", "")
        self.position = 0
        self.current_token = None

    def next_token(self):
        while self.position < len(self.input_string) and self.input_string[self.position].isdigit():
            if self.current_token is not None:
                raise ValueError("Unexpected token")
            self.current_token = int(self.input_string[self.position])
            self.position += 1
    elif self.position  len(self.input_string) and (self.input_string[self.position] == '+' or 
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                        self.input_string[self.position] == '-' or 
                                                        self.input_string[self.position] == '*' or 
                                                        self.input_string[self.position] == '/' or 
                                                        self.input_string[self.position] == '(' or 
                                                        self.input_string[self.position] == ')'):
            if self.current_token is not None:
                raise ValueError("Unexpected token")
            self.current_token = self.input_string[self.position]
            self.position += 1
        else:
            if self.current_token is None:
                raise ValueError("Unexpected end of input")

class Parser:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.tokenizer.next_token()
    
    def parse(self):
        return self.expression()

    def expression(self):
        result = self.term()
        while self.tokenizer.current_token == '+' or self.tokenizer.current_token == '-':
            operator = self.tokenizer.current_token
            self.tokenizer.next_token()
            if operator == '+':
                result += self.term()
            elif operator == '-':
                result -= self.term()
        return result

    def term(self):
        result = self.factor()
        while self.tokenizer.current_token == '*' or self.tokenizer.current_token == '/':
            operator = self.tokenizer.current_token
            self.tokenizer.next_token()
            if operator == '*':
                result *= self.factor()
            elif operator == '/':
                divisor = self.factor()
                if divisor == 0:
                    raise ValueError("Division by zero")
                result /= divisor
        return result

    def factor(self):
        token = self.tokenizer.current_token
        self.tokenizer.next_token()
        if isinstance(token, int):
            return token
        elif token == '(':
            result = self.expression()
            if self.tokenizer.current_token != ')':
                raise ValueError("Expected closing parenthesis")
            self.tokenizer.next_token()
            return result
        elif token == '-':
            return -self.factor()
        else:
            raise ValueError(f"Unexpected token: {token}")

class Evaluator:
    def __init__(self, input_string):
        self.input_string = input_string

    def evaluate(self):
        tokenizer = Tokenizer(self.input_string)
        parser = Parser(tokenizer)
        return int(parser.parse())

if __name__ == '__main__':
    evaluator = Evaluator("1 + 2")
    print(evaluator.evaluate())  # Output: 3
    evaluator = Evaluator("2 * 3 + 4")
    print(evaluator.evaluate())  # Output: 10
    evaluator = Evaluator("2 * (3 + 4)")
    print(evaluator.evaluate())  # Output: 14
    evaluator = Evaluator("8 / 2 * (2 + 2)")
    print(evaluator.evaluate())  # Output: 16
