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
    char* text;
} Token;

// Lexer function
Token* lexer(char* expression) {
    int len = strlen(expression);
    Token* tokens = malloc((len + 1) * sizeof(Token));
    int index = 0;
    while (index < len) {
        if (isdigit(expression[index])) {
            double value = 0.0;
            int start = index;
            while (index < len && isdigit(expression[index])) {
                value = value * 10 + expression[index++] - '0';
            }
            tokens[index].type = NUMBER;
            tokens[index].value = value;
            tokens[index].text = malloc(5);
            strcpy(tokens[index].text, "0");
            index++;
        } else if (expression[index] == '+') {
            tokens[index].type = PLUS;
            index++;
        } else if (expression[index] == '-') {
            tokens[index].type = MINUS;
            index++;
        } else if (expression[index] == '*') {
            tokens[index].type = MUL;
            index++;
        } else if (expression[index] == '/') {
            tokens[index].type = DIV;
            index++;
        } else if (expression[index] == '(') {
            tokens[index].type = LPAREN;
            index++;
        } else if (expression[index] == ')') {
            tokens[index].type = RPAREN;
            index++;
        } else {
            break;
        }
    }
    tokens[len].type = EOF;
    return tokens;
}

// Parser function
Token* parse(Token* tokens) {
    Token* stack = malloc(100 * sizeof(Token));
    int top = -1;
    for (int i = 0; i < strlen(tokens[0].text); i++) {
        if (tokens[i].type == LPAREN) {
            stack[++top] = tokens[i];
        } else if (tokens[i].type == RPAREN) {
            while (stack[top].type != LPAREN) {
                Token* token = stack[top--].value;
                if (token->type == NUMBER) {
                    stack[top].value = stack[top].value + token->value;
                } else if (token->type == PLUS || token->type == MINUS ||
                           token->type == MUL || token->type == DIV) {
                    Token* operand1 = stack[top--].value;
                    Token* operand2 = stack[top--].value;
                    if (operand1->type == NUMBER && operand2->type == NUMBER) {
                        double result = 0.0;
                        if (operand1->type == MINUS) {
                            result = -operand1->value + operand2->value;
                        } else if (operand1->type == PLUS) {
                            result = operand1->value + operand2->value;
                        } else if (operand1->type == MUL) {
                            result = operand1->value * operand2->value;
                        } else if (operand1->type == DIV) {
                            result = operand1->value / operand2->value;
                        }
                        stack[top].value = result;
                    }
                }
            }
            stack[top--].type = LPAREN;
        }
    }
    return stack[0];
}

// Evaluator function
double evaluate(Token* token) {
    if (token->type == NUMBER) {
        return token->value;
    } else if (token->type == PLUS || token->type == MINUS ||
               token->type == MUL || token->type == DIV) {
        Token* operand1 = parse(stack);
        Token* operand2 = parse(stack);
        double result = 0.0;
        if (operand1->type == NUMBER && operand2->type == NUMBER) {
            if (token->type == PLUS) {
                result = operand1->value + operand2->value;
            } else if (token->type == MINUS) {
                result = -operand1->value + operand2->value;
            } else if (token->type == MUL) {
                result = operand1->value * operand2->value;
            } else if (token->type == DIV) {
                result = operand1->value / operand2->value;
            }
        }
        return result;
    } else {
        return 0.0;
    }
}

int main() {
    char* expressions[] = {"3 + 4 * (2 - 1)", "1 + 2", "2 * 3 + 4", "8 / 2 * (2 + 2)"};
    for (char* expression : expressions) {
        Token* tokens = lexer(expression);
        Token* token = parse(tokens);
        double result = evaluate(token);
        printf("%s => %f\n", expression, result);
        free(tokens->text);
        free(tokens);
        free(stack);
    }
    return 0;
}