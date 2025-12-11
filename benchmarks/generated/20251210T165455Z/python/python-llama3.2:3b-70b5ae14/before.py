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
            elif not current_token or (current_token.type == 'OPERATOR' and char in '+-*/()'):
                tokens.append(current_token)
                current_token = Token(char, char)
            else:
                if current_token.value != '' and current_token.value != char:
                    raise ValueError("Invalid character in expression")
            
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
            elif token.type == 'OPERATOR':
                while (operator_stack and 
                       self.precedence[operator_stack[-1]] >= self.precedence[token.value]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token.value)
            elif token.type == 'LPAREN':
                operator_stack.append(token.value)
            elif token.type == 'RPAREN':
                while operator_stack[-1] != 'LPAREN':
                    output_queue.append(operator_stack.pop())
                if operator_stack[-1] == 'LPAREN':
                    operator_stack.pop()
        
        while operator_stack:
            output_queue.append(operator_stack.pop())
        
        return self.evaluate(output_queue)

    def evaluate(self, tokens):
        stack = []
        for token in tokens:
            if token.isdigit():
                stack.append(int(token))
            elif token == '-':
                if len(stack) < 1:
                    raise ValueError("Invalid expression")
                stack.append(-stack.pop())
            else:
                right_operand = stack.pop()
                left_operand = stack.pop()
                if token == '+':
                    stack.append(left_operand + right_operand)
                elif token == '*':
                    stack.append(left_operand * right_operand)
        return stack[0]

class Evaluator:
    def __init__(self):
        pass
    
    def evaluate(self, expression):
        tokens = Tokenizer().tokenize(expression)
        parser = Parser()
        parsed_expression = parser.parse(tokens)
        return parser.evaluate(parsed_expression)

if __name__ == '__main__':
    evaluator = Evaluator()
    
    print(evaluator.evaluate("1 + 2")) # Output: 3
    print(evaluator.evaluate("2 * 3 + 4")) # Output: 10
    print(evaluator.evaluate("2 * (3 + 4)")) # Output: 14
    print(evaluator.evaluate("8 / 2 * (2 + 2)")) # Output: 16