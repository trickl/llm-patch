#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Token types
typedef enum {
    NUMBER,
    PLUS,
    MINUS,
    MUL,
    DIV,
    LPAREN,
    RPAREN,
    EOF
} TokenType;

// Token structure
typedef struct {
    TokenType type;
    double value;
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    for (int i = 0; i < length; ++i) {
        if (isdigit(expression[i])) {
            double value = 0;
            while (i < length && isdigit(expression[i])) {
                value = value * 10 + expression[i++] - '0';
            }
            tokens[i].type = NUMBER;
            tokens[i].value = value;
        } else if (expression[i] == '+') {
            tokens[i].type = PLUS;
            tokens[i].value = 1.0;
        } else if (expression[i] == '-') {
            tokens[i].type = MINUS;
            tokens[i].value = -1.0;
        } else if (expression[i] == '*') {
            tokens[i].type = MUL;
            tokens[i].value = 1.0;
        } else if (expression[i] == '/') {
            tokens[i].type = DIV;
            tokens[i].value = 1.0;
        } else if (expression[i] == '(') {
            tokens[i].type = LPAREN;
            tokens[i].value = 0.0;
        } else if (expression[i] == ')') {
            tokens[i].type = RPAREN;
            tokens[i].value = 0.0;
        }
    }
    tokens[length].type = EOF;
    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* stack = malloc((tokens[0].length + 1) * sizeof(Token));
    int top = -1;
    for (int i = 0; i < tokens[0].length; ++i) {
        if (tokens[i].type == LPAREN) {
            stack[++top] = tokens[i];
        } else if (tokens[i].type == RPAREN) {
            while (stack[top].type != LPAREN) {
                Token* token = stack[top--].value;
                if (token->type == NUMBER) {
                    stack[top].value = token->value + stack[top - 1].value;
                } else if (token->type == PLUS || token->type == MINUS) {
                    double operand2 = stack[top - 1].value;
                    double operand1 = stack[top--].value;
                    if (token->type == PLUS) {
                        stack[top] = (Token){.type = NUMBER, .value = operand1 + operand2};
                    } else {
                        stack[top] = (Token){.type = NUMBER, .value = operand1 - operand2};
                    }
                } else if (token->type == MUL || token->type == DIV) {
                    double operand2 = stack[top - 1].value;
                    double operand1 = stack[top--].value;
                    if (token->type == MUL) {
                        stack[top] = (Token){.type = NUMBER, .value = operand1 * operand2};
                    } else {
                        stack[top] = (Token){.type = NUMBER, .value = operand1 / operand2};
                    }
                }
            }
            stack[--top].value = 0.0;
        }
    }
    return stack[0];
}

// Evaluator function to evaluate the parsed expression
double evaluator(Token* token) {
    if (token->type == NUMBER) {
        return token->value;
    } else if (token->type == PLUS || token->type == MINUS) {
        double operand2 = evaluator(token);
        double operand1 = evaluator(stack[top--].value);
        if (token->type == PLUS) {
            return operand1 + operand2;
        } else {
            return operand1 - operand2;
        }
    } else if (token->type == MUL || token->type == DIV) {
        double operand2 = evaluator(token);
        double operand1 = evaluator(stack[top--].value);
        if (token->type == MUL) {
            return operand1 * operand2;
        } else {
            return operand1 / operand2;
        }
    } else {
        printf("Error: Invalid token type\n");
        exit(1);
    }
}

int main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (const char* expression : expressions) {
        Token* tokens = lexer(expression);
        Token* parsed_token = parser(tokens);
        double result = evaluator(parsed_token);
        printf("%s => %f\n", expression, result);
        free(tokens);
        free(parsed_token);
    }
    return 0;
}