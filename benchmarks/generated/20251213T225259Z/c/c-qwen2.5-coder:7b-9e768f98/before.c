#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKEN_LENGTH 64

typedef enum {
    TOKEN_TYPE_NUMBER,
    TOKEN_TYPE_PLUS,
    TOKEN_TYPE_MINUS,
    TOKEN_TYPE_MULTIPLY,
    TOKEN_TYPE_DIVIDE,
    TOKEN_TYPE_LPAREN,
    TOKEN_TYPE_RPAREN,
    TOKEN_TYPE_EOF
} TokenType;

typedef struct {
    TokenType type;
    int value;
} Token;

Token tokenize(const char **input) {
    while (**input && isspace(**input)) (*input)++;
    if (!**input) return (Token){TOKEN_TYPE_EOF, 0};

    if (isdigit(**input)) {
        int value = 0;
        while (**input && isdigit(**input)) {
            value = value * 10 + (**input - '0');
            (*input)++;
        }
        return (Token){TOKEN_TYPE_NUMBER, value};
    }

    switch (**input) {
        case '+': (*input)++; return (Token){TOKEN_TYPE_PLUS, 0};
        case '-': (*input)++; return (Token){TOKEN_TYPE_MINUS, 0};
        case '*': (*input)++; return (Token){TOKEN_TYPE_MULTIPLY, 0};
        case '/': (*input)++; return (Token){TOKEN_TYPE_DIVIDE, 0};
        case '(': (*input)++; return (Token){TOKEN_TYPE_LPAREN, 0};
        case ')': (*input)++; return (Token){TOKEN_TYPE_RPAREN, 0};
    }

    return (Token){TOKEN_TYPE_EOF, 0};
}

int precedence(TokenType type) {
    switch (type) {
        case TOKEN_TYPE_MULTIPLY:
        case TOKEN_TYPE_DIVIDE: return 2;
        case TOKEN_TYPE_PLUS:
        case TOKEN_TYPE_MINUS: return 1;
        default: return 0;
    }
}

int evaluate(int a, int b, TokenType op) {
    switch (op) {
        case TOKEN_TYPE_PLUS: return a + b;
        case TOKEN_TYPE_MINUS: return a - b;
        case TOKEN_TYPE_MULTIPLY: return a * b;
        case TOKEN_TYPE_DIVIDE: return a / b;
        default: return 0;
    }
}

int parse_and_evaluate(const char *expression) {
    Token tokens[MAX_TOKEN_LENGTH];
    int token_count = 0;

    const char *input = expression;
    while (**input != '\0') {
        tokens[token_count++] = tokenize(&input);
    }

    int values[MAX_TOKEN_LENGTH] = {0};
    TokenType ops[MAX_TOKEN_LENGTH] = {TOKEN_TYPE_PLUS}; // Default to addition for initial value
    int top = 0;

    for (int i = 0; i < token_count; i++) {
        Token token = tokens[i];
        switch (token.type) {
            case TOKEN_TYPE_NUMBER:
                values[top++] = token.value;
                break;
            case TOKEN_TYPE_LPAREN:
                ops[top++] = token.type;
                break;
            case TOKEN_TYPE_RPAREN:
                while (ops[top - 1] != TOKEN_TYPE_LPAREN) {
                    int b = values[--top];
                    int a = values[--top];
                    TokenType op = ops[--top];
                    values[top++] = evaluate(a, b, op);
                }
                top--; // Pop the '('
                break;
            case TOKEN_TYPE_PLUS:
            case TOKEN_TYPE_MINUS:
            case TOKEN_TYPE_MULTIPLY:
            case TOKEN_TYPE_DIVIDE:
                while (top > 0 && precedence(ops[top - 1]) >= precedence(token.type)) {
                    int b = values[--top];
                    int a = values[--top];
                    TokenType op = ops[--top];
                    values[top++] = evaluate(a, b, op);
                }
                ops[top++] = token.type;
                break;
        }
    }

    while (top > 1) {
        int b = values[--top];
        int a = values[--top];
        TokenType op = ops[--top];
        values[top++] = evaluate(a, b, op);
    }

    return values[0];
}

int main() {
    printf("3 + 4 * (2 - 1) => %d\n", parse_and_evaluate("3 + 4 * (2 - 1)"));
    printf("2 * 3 + 4 => %d\n", parse_and_evaluate("2 * 3 + 4"));
    printf("2 * (3 + 4) => %d\n", parse_and_evaluate("2 * (3 + 4)"));
    printf("8 / 2 * (2 + 2) => %d\n", parse_and_evaluate("8 / 2 * (2 + 2)"));

    return 0;
}