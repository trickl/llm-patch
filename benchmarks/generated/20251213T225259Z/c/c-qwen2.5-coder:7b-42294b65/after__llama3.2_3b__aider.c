#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKEN_LENGTH 64

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

Token tokenize(const char **input) {
    while (**input == ' ') (*input)++;
    if (**input == '\0') return (Token){TOKEN_EOF, 0};
    if (isdigit(**input)) {
        int value = 0;
        while (isdigit(**input)) {
            value = value * 10 + (**input - '0');
            (*input)++;
        }
        return (Token){TOKEN_NUMBER, value};
    } else if (**input == '+') {
        (*input)++;
        return (Token){TOKEN_PLUS, 0};
    } else if (**input == '-') {
        (*input)++;
        return (Token){TOKEN_MINUS, 0};
    } else if (**input == '*') {
        (*input)++;
        return (Token){TOKEN_MULTIPLY, 0};
    } else if (**input == '/') {
        (*input)++;
        return (Token){TOKEN_DIVIDE, 0};
    } else if (**input == '(') {
        (*input)++;
        return (Token){TOKEN_LPAREN, 0};
    } else if (**input == ')') {
        (*input)++;
        return (Token){TOKEN_RPAREN, 0};
    }
    return (Token){TOKEN_EOF, 0};
}

int precedence(TokenType type) {
    switch (type) {
        case TOKEN_PLUS:
        case TOKEN_MINUS: return 1;
        case TOKEN_MULTIPLY:
        case TOKEN_DIVIDE: return 2;
        default: return -1;
    }
}

int apply_operator(int a, int b, TokenType operator) {
    switch (operator) {
        case TOKEN_PLUS: return a + b;
        case TOKEN_MINUS: return a - b;
        case TOKEN_MULTIPLY: return a * b;
        case TOKEN_DIVIDE: if (b != 0) return a / b; else return 0;
        default: return 0;
    }
}

int evaluate(const char *expression) {
    Token tokens[MAX_TOKEN_LENGTH];
    int token_count = 0;

    const char *input = expression;
    while (**input != '\0') {
        tokens[token_count++] = tokenize(input);
    }

    int values[token_count];
    TokenType operators[token_count];

    int value_index = 0, operator_index = -1;

    for (int i = 0; i < token_count; i++) {
        Token token = tokens[i];
        if (token.type == TOKEN_NUMBER) {
            values[value_index++] = token.value;
        } else if (token.type == TOKEN_LPAREN) {
            operators[++operator_index] = token.type;
        } else if (token.type == TOKEN_RPAREN) {
            while (operators[operator_index] != TOKEN_LPAREN) {
                int b = values[--value_index];
                int a = values[--value_index];
                TokenType operator = operators[operator_index--];
                values[value_index++] = apply_operator(a, b, operator);
            }
            operator_index--;
        } else if (token.type == TOKEN_PLUS || token.type == TOKEN_MINUS ||
                   token.type == TOKEN_MULTIPLY || token.type == TOKEN_DIVIDE) {
            while (operator_index >= 0 && precedence(operators[operator_index]) >= precedence(token.type)) {
                int b = values[--value_index];
                int a = values[--value_index];
                TokenType operator = operators[operator_index--];
                values[value_index++] = apply_operator(a, b, operator);
            }
            operators[++operator_index] = token.type;
        }
    }

    while (operator_index >= 0) {
        int b = values[--value_index];
        int a = values[--value_index];
        TokenType operator = operators[operator_index--];
        values[value_index++] = apply_operator(a, b, operator);
    }

    return values[0];
}

int main() {
    printf("%d\n", evaluate("1 + 2")); // Output: 3
    printf("%d\n", evaluate("2 * 3 + 4")); // Output: 10
    printf("%d\n", evaluate("2 * (3 + 4)")); // Output: 14
    printf("%d\n", evaluate("8 / 2 * (2 + 2)")); // Output: 16
    return 0;
}
