import re

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

class EvaluatorError(Exception):
    pass

class Tokenizer:
    def tokenize(self, expression):
        tokens = []
        current_token = None
        
        for char in expression:
            if char.isspace():
                continue
            
            if not current_token or (current_token.type != 'NUMBER' and current_token.type != '(' and current_token.type != ')'):
                if re.match(r'^\d+$', char):
                    current_token = Token('NUMBER', int(char))
                elif char == '+':
                    current_token = Token('PLUS', '+')
                elif char == '-':
                    current_token = Token('MINUS', '-')
                elif char == '*':
                    current_token = Token('MULTIPLY', '*')
                elif char == '/':
                    current_token = Token('DIVIDE', '/')
                elif char == '(':
                    current_token = Token('LPAREN', '(')
                elif char == ')':
                    current_token = Token('RPAREN', ')'
            tokens.append(current_token)
            
        if current_token and current_token.type != 'NUMBER' and current_token.type != '(' and current_token.type != ')':
            raise EvaluatorError("Invalid character in expression")
        
        return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        
    def parse(self):
        result = self.parse_expression()
        if self.index < len(self.tokens):
            raise EvaluatorError("Unexpected token after parsing expression")
        return result
    
    def parse_expression(self):
        left = self.parse_term()
        
        while self.index < len(self.tokens) and (self.tokens[self.index].type == 'PLUS' or self.tokens[self.index].type == 'MINUS'):
            operator = self.tokens[self.index]
            self.index += 1
            right = self.parse_term()
            
            if operator.type == 'PLUS':
                left = left + right
            elif operator.type == 'MINUS':
                left = left - right
        
        return left
    
    def parse_term(self):
        left = self.parse_factor()
        
        while self.index < len(self.tokens) and (self.tokens[self.index].type == 'MULTIPLY' or self.tokens[self.index].type == 'DIVIDE'):
            operator = self.tokens[self.index]
            self.index += 1
            right = self.parse_factor()
            
            if operator.type == 'MULTIPLY':
                left = left * right
            elif operator.type == 'DIVIDE':
                left = left / right
        
        return left
    
    def parse_factor(self):
        if self.index < len(self.tokens) and self.tokens[self.index].type == 'LPAREN':
            self.index += 1
            result = self.parse_expression()
            self.index += 1
            return result
        elif self.index < len(self.tokens) and self.tokens[self.index].type == 'NUMBER':
            self.index += 1
            return self.tokens[self.index - 1].value
        else:
            raise EvaluatorError("Invalid token in expression")

class Evaluator:
    def __init__(self, result):
        self.result = result
    
    def evaluate(self):
        if isinstance(self.result, Token):
            if self.result.type == 'NUMBER':
                return self.result.value
            elif self.result.type == 'LPAREN':
                return self.evaluate()
            else:
                raise EvaluatorError("Invalid token in expression")
        else:
            raise EvaluatorError("Result is not a Token")

def main():
    tokenizer = Tokenizer()
    parser = Parser(tokenizer.tokenize("3 + 4 * (2 - 1)"))
    evaluator = Evaluator(parser.parse())
    
    print(evaluator.evaluate())

if __name__ == "__main__":
    main()