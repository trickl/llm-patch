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
int token_index = 0;

void error(const char *message) {
    fprintf(stderr, "Error: %s\n", message);
    exit(EXIT_FAILURE);
}

void skip_whitespace(char **input) {
    while (**input && isspace(**input)) (*input)++;
}

Token get_next_token(char **input) {
    skip_whitespace(input);

    if (**input == '\0') return (Token){TOKEN_EOF, 0};

    if (isdigit(**input)) {
        int value = 0;
        while (**input && isdigit(**input)) {
            value = value * 10 + (**input - '0');
            (*input)++;
        }
        return (Token){TOKEN_NUMBER, value};
    }

    switch (**input) {
        case '+': (*input)++; return (Token){TOKEN_PLUS, 0};
        case '-': (*input)++; return (Token){TOKEN_MINUS, 0};
        case '*': (*input)++; return (Token){TOKEN_MULTIPLY, 0};
        case '/': (*input)++; return (Token){TOKEN_DIVIDE, 0};
        case '(': (*input)++; return (Token){TOKEN_LPAREN, 0};
        case ')': (*input)++; return (Token){TOKEN_RPAREN, 0};
        default: error("Unexpected character");
    }

    return (Token){TOKEN_EOF, 0};
}

int evaluate_expression(char *expression) {
    token_index = 0;
    char *input = expression;

    tokens[token_index++] = get_next_token(&input);

    int result = evaluate_addition(&input);
    if (tokens[token_index].type != TOKEN_EOF) error("Unexpected token");

    return result;
}

int evaluate_multiplication(char **input) {
    int result = evaluate_unary(input);

    while (**input == '*' || **input == '/') {
        Token op = get_next_token(input);
        int right = evaluate_unary(input);

        switch (op.type) {
            case TOKEN_MULTIPLY: result *= right; break;
            case TOKEN_DIVIDE: if (right != 0) result /= right; else error("Division by zero"); break;
            default: error("Unexpected operator");
        }
    }

    return result;
}

int evaluate_unary(char **input) {
    skip_whitespace(input);

    if (**input == '-') {
        (*input)++;
        int value = evaluate_unary(input);
        return -value;
    }

    return evaluate_multiplication(input);
}

int evaluate_addition(char **input) {
    int result = evaluate_unary(input);

    while (**input == '+' || **input == '-') {
        Token op = get_next_token(input);
        int right = evaluate_unary(input);

        switch (op.type) {
            case TOKEN_PLUS: result += right; break;
            case TOKEN_MINUS: result -= right; break;
            default: error("Unexpected operator");
        }
    }

    return result;
}

int main() {
    char expression[256];
    printf("Enter an arithmetic expression: ");
    fgets(expression, sizeof(expression), stdin);

    int result = evaluate_expression(expression);
    printf("Result: %d\n", result);

    return 0;
}