#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKENS 100

typedef enum {
    TOKEN_NUMBER,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_MULTIPLY,
    TOKEN_DIVIDE,
    TOKEN_LPAREN,
    TOKEN_RPAREN,
    TOKEN_EOF
} TokenType;

typedef struct {
    TokenType type;
    int value;
} Token;

Token tokens[MAX_TOKENS];
int token_count = 0;

void tokenize(const char *expression) {
    const char *p = expression;
    while (*p != '\0') {
        if (isspace(*p)) {
            p++;
            continue;
        }
        if (isdigit(*p)) {
            int value = 0;
            while (isdigit(*p)) {
                value = value * 10 + (*p - '0');
                p++;
            }
            tokens[token_count++] = (Token){TOKEN_NUMBER, value};
        } else if (*p == '+') {
            tokens[token_count++] = (Token){TOKEN_PLUS, 0};
            p++;
        } else if (*p == '-') {
            if (token_count > 0 && tokens[token_count - 1].type == TOKEN_EOF) {
                tokens[token_count++] = (Token){TOKEN_NUMBER, -1};
            } else {
                tokens[token_count++] = (Token){TOKEN_MINUS, 0};
            }
            p++;
        } else if (*p == '*') {
            tokens[token_count++] = (Token){TOKEN_MULTIPLY, 0};
            p++;
        } else if (*p == '/') {
            tokens[token_count++] = (Token){TOKEN_DIVIDE, 0};
            p++;
        } else if (*p == '(') {
            tokens[token_count++] = (Token){TOKEN_LPAREN, 0};
            p++;
        } else if (*p == ')') {
            tokens[token_count++] = (Token){TOKEN_RPAREN, 0};
            p++;
        }
    }
    tokens[token_count++] = (Token){TOKEN_EOF, 0};
}

int precedence(TokenType type) {
    switch (type) {
        case TOKEN_PLUS:
        case TOKEN_MINUS: return 1;
        case TOKEN_MULTIPLY:
        case TOKEN_DIVIDE: return 2;
        default: return 0;
    }
}

int apply_operator(int a, int b, TokenType operator) {
    switch (operator) {
        case TOKEN_PLUS: return a + b;
        case TOKEN_MINUS: return a - b;
        case TOKEN_MULTIPLY: return a * b;
        case TOKEN_DIVIDE: return a / b;
        default: return 0;
    }
}

int evaluate_expression() {
    int values[MAX_TOKENS] = {0};
    TokenType operators[MAX_TOKENS] = {TOKEN_EOF};
    int value_count = 0, operator_count = 0;

    for (int i = 0; i < token_count; i++) {
        Token token = tokens[i];
        switch (token.type) {
            case TOKEN_NUMBER:
                values[value_count++] = token.value;
                break;
            case TOKEN_PLUS:
            case TOKEN_MINUS:
            case TOKEN_MULTIPLY:
            case TOKEN_DIVIDE:
                while (operator_count > 0 && precedence(operators[operator_count - 1]) >= precedence(token.type)) {
                    int b = values[--value_count];
                    int a = values[--value_count];
                    operators[--operator_count] = token.type;
                    values[value_count++] = apply_operator(a, b, operators[operator_count]);
                }
                operators[operator_count++] = token.type;
                break;
            case TOKEN_LPAREN:
                operators[operator_count++] = token.type;
                break;
            case TOKEN_RPAREN:
                while (operators[operator_count - 1] != TOKEN_LPAREN) {
                    int b = values[--value_count];
                    int a = values[--value_count];
                    operators[--operator_count] = token.type;
                    values[value_count++] = apply_operator(a, b, operators[operator_count]);
                }
                operator_count--;
                break;
        }
    }

    while (operator_count > 0) {
        int b = values[--value_count];
        int a = values[--value_count];
        operators[--operator_count] = operators[operator_count];
        values[value_count++] = apply_operator(a, b, operators[operator_count]);
    }

    return values[0];
}

int main() {
    tokenize("3 + 4 * (2 - 1)");
    printf("%d\n", evaluate_expression()); // Output: 9

    tokenize("2 * 3 + 4");
    printf("%d\n", evaluate_expression()); // Output: 10

    tokenize("2 * (3 + 4)");
    printf("%d\n", evaluate_expression()); // Output: 14

    tokenize("8 / 2 * (2 + 2)");
    printf("%d\n", evaluate_expression()); // Output: 16

    return 0;
}

#include "expression_evaluator.c"
