import re

class Tokenizer:
    def __init__(self, input_string):
        self.input_string = input_string.replace(' ', '')
        self.current_index = 0

    def get_next_token(self):
        if self.current_index >= len(self.input_string):
            return None
        
        token = ''
        start_char = self.input_string[self.current_index]
        
        if start_char.isdigit():
            while self.current_index < len(self.input_string) and self.input_string[self.current_index].isdigit():
                token += self.input_string[self.current_index]
                self.current_index += 1
        elif start_char == '-' and (self.current_index + 1 < len(self.input_string) and self.input_string[self.current_index + 1].isdigit()):
            token = '-'
            self.current_index += 1
            while self.current_index < len(self.input_string) and self.input_string[self.current_index].isdigit():
                token += self.input_string[self.current_index]
                self.current_index += 1
        elif start_char in '+-*/()':
            token = start_char
            self.current_index += 1
        else:
            raise ValueError(f"Unexpected character: {start_char}")
        
        return int(token) if token.isdigit() else token

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0

    def parse_expression(self):
        result = self.parse_term()
        while self.current_token_index < len(self.tokens) and self.tokens[self.current_token_index] in '+-':
            operator = self.tokens[self.current_token_index]
            self.current_token_index += 1
            right = self.parse_term()
            if operator == '+':
                result += right
            else:
                result -= right
        return result

    def parse_term(self):
        result = self.parse_factor()
        while self.current_token_index < len(self.tokens) and self.tokens[self.current_token_index] in '*/':
            operator = self.tokens[self.current_token_index]
            self.current_token_index += 1
            right = self.parse_factor()
            if operator == '*':
                result *= right
            else:
                result //= right
        return result

    def parse_factor(self):
        token = self.tokens[self.current_token_index]
        self.current_token_index += 1
        
        if isinstance(token, int):
            return token
        elif token == '(':
            result = self.parse_expression()
            if self.current_token_index < len(self.tokens) and self.tokens[self.current_token_index] == ')':
                self.current_token_index += 1
            else:
                raise ValueError("Expected )")
            return result
        elif token == '-':
            return -self.parse_factor()
        else:
            raise ValueError(f"Unexpected token: {token}")

class Evaluator:
    def evaluate(self, expression):
        tokenizer = Tokenizer(expression)
        tokens = [tokenizer.get_next_token() while True]
        
        parser = Parser(tokens)
        result = parser.parse_expression()
        
        return result

if __name__ == '__main__':
    evaluator = Evaluator()
    
    print(evaluator.evaluate('1 + 2')) # Output: 3
    print(evaluator.evaluate('2 * 3 + 4')) # Output: 10
    print(evaluator.evaluate('2 * (3 + 4)')) # Output: 14
    print(evaluator.evaluate('8 / 2 * (2 + 2)')) # Output: 16