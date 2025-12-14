#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

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

void error(const char *msg) {
    fprintf(stderr, "Error: %s\n", msg);
    exit(EXIT_FAILURE);
}

void skip_whitespace(char **input) {
    while (**input && isspace(**input)) (*input)++;
}

Token next_token(char **input) {
    skip_whitespace(input);

    if (**input == '\0') return (Token){TOKEN_EOF, 0};

    Token token;
    switch (**input) {
        case '+':
            token.type = TOKEN_PLUS;
            break;
        case '-':
            token.type = TOKEN_MINUS;
            break;
        case '*':
            token.type = TOKEN_MULTIPLY;
            break;
        case '/':
            token.type = TOKEN_DIVIDE;
            break;
        case '(':
            token.type = TOKEN_LPAREN;
            break;
        case ')':
            token.type = TOKEN_RPAREN;
            break;
        default:
            if (isdigit(**input)) {
                int value = 0;
                while (**input && isdigit(**input)) {
                    value = value * 10 + (**input - '0');
                    (*input)++;
                }
                return (Token){TOKEN_NUMBER, value};
            } else {
                error("Unexpected character");
            }
    }

    (*input)++;
    return token;
}

int precedence(TokenType type) {
    switch (type) {
        case TOKEN_PLUS:
        case TOKEN_MINUS:
            return 1;
        case TOKEN_MULTIPLY:
        case TOKEN_DIVIDE:
            return 2;
        default:
            return 0;
    }
}

int apply_operator(int a, int b, TokenType operator) {
    switch (operator) {
        case TOKEN_PLUS:
            return a + b;
        case TOKEN_MINUS:
            return a - b;
        case TOKEN_MULTIPLY:
            return a * b;
        case TOKEN_DIVIDE:
            if (b == 0) error("Division by zero");
            return a / b;
        default:
            error("Unknown operator");
    }
}

int evaluate_expression(char **input) {
    int values[MAX_TOKENS] = {0};
    TokenType operators[MAX_TOKENS] = {TOKEN_EOF};
    int value_index = 0, operator_index = 0;

    while (1) {
        Token token = next_token(input);
        if (token.type == TOKEN_NUMBER) {
            values[value_index++] = token.value;
        } else if (token.type == TOKEN_LPAREN) {
            operators[operator_index++] = token.type;
        } else if (token.type == TOKEN_RPAREN) {
            while (operators[operator_index - 1] != TOKEN_LPAREN) {
                int b = values[--value_index];
                int a = values[--value_index];
                TokenType operator = operators[--operator_index];
                values[value_index++] = apply_operator(a, b, operator);
            }
            operator_index--;
        } else if (token.type == TOKEN_EOF) {
            break;
        } else {
            while (operator_index > 0 && precedence(operators[operator_index - 1]) >= precedence(token.type)) {
                int b = values[--value_index];
                int a = values[--value_index];
                TokenType operator = operators[--operator_index];
                values[value_index++] = apply_operator(a, b, operator);
            }
            operators[operator_index++] = token.type;
        }
    }

    while (operator_index > 0) {
        int b = values[--value_index];
        int a = values[--value_index];
        TokenType operator = operators[--operator_index];
        values[value_index++] = apply_operator(a, b, operator);
    }

    return values[0];
}

int main() {
    char input[1024];

    printf("Enter an expression: ");
    fgets(input, sizeof(input), stdin);

    int result = evaluate_expression(&input);
    printf("Result: %d\n", result);
    return 0;
    printf("Result: %d\n", result);

    return 0;
}
