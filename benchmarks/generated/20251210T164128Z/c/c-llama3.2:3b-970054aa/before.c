#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Token type enum
typedef enum {
    NUMBER,
    PLUS,
    MINUS,
    MUL,
    DIV,
    LPAREN,
    RPAREN,
    UMINUS
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
            i++;
        } else if (expression[i] == '-') {
            tokens[i].type = MINUS;
            i++;
        } else if (expression[i] == '*') {
            tokens[i].type = MUL;
            i++;
        } else if (expression[i] == '/') {
            tokens[i].type = DIV;
            i++;
        } else if (expression[i] == '(') {
            tokens[i].type = LPAREN;
            i++;
        } else if (expression[i] == ')') {
            tokens[i].type = RPAREN;
            i++;
        } else if (expression[i] == '-') {
            tokens[i].type = UMINUS;
            i++;
        }
    }
    tokens[length].type = NUMBER;
    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* stack = malloc((tokens[0].value + 1) * sizeof(Token));
    int top = 0;

    for (int i = 0; i < tokens[top].value; ++i) {
        if (tokens[i].type == LPAREN) {
            stack[++top] = tokens[i];
        } else if (tokens[i].type == RPAREN) {
            while (stack[top].type != LPAREN) {
                Token* temp = stack[top--].value;
                if (temp->type == NUMBER) {
                    stack[top].value += temp->value;
                } else if (temp->type == PLUS || temp->type == MINUS ||
                           temp->type == MUL || temp->type == DIV) {
                    Token* operand1 = stack[top--].value;
                    Token* operand2 = stack[top--].value;
                    Token* result = malloc(sizeof(Token));
                    result->type = NUMBER;
                    if (temp->type == PLUS) {
                        result->value = operand1.value + operand2.value;
                    } else if (temp->type == MINUS) {
                        result->value = operand1.value - operand2.value;
                    } else if (temp->type == MUL) {
                        result->value = operand1.value * operand2.value;
                    } else if (temp->type == DIV) {
                        result->value = operand1.value / operand2.value;
                    }
                    stack[++top] = result;
                }
            }
            stack[top--].type = RPAREN;
        }
    }

    return stack[0];
}

// Evaluator function to evaluate the parsed expression
double evaluator(Token* token) {
    if (token->type == NUMBER) {
        return token->value;
    } else if (token->type == PLUS || token->type == MINUS ||
               token->type == MUL || token->type == DIV) {
        Token* operand1 = token->value;
        Token* operand2 = stack[0].value;
        double result;
        if (operand1->type == NUMBER) {
            result = operand1.value + operand2.value;
        } else if (operand1->type == MINUS) {
            result = operand1.value - operand2.value;
        } else if (operand1->type == MUL) {
            result = operand1.value * operand2.value;
        } else if (operand1->type == DIV) {
            result = operand1.value / operand2.value;
        }
        return result;
    } else {
        return -stack[0].value;
    }
}

int main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int num_expressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < num_expressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        Token* parsed_token = parser(tokens);
        double result = evaluator(parsed_token);
        printf("%s => %f\n", expressions[i], result);
        free(tokens);
        free(parsed_token);
    }

    return 0;
}