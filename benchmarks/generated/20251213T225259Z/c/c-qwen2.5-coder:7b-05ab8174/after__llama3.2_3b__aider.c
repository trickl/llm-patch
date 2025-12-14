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
    exit(1);
}

Token get_next_token() {
    while (isspace(tokens[token_index].value)) {
        token_index++;
    }

    Token token = tokens[token_index];
    token_index++;

    switch (token.value) {
        case '+':
            return (Token){TOKEN_PLUS, 0};
        case '-':
            return (Token){TOKEN_MINUS, 0};
        case '*':
            return (Token){TOKEN_MULTIPLY, 0};
        case '/':
            return (Token){TOKEN_DIVIDE, 0};
        case '(':
            return (Token){TOKEN_LPAREN, 0};
        case ')':
            return (Token){TOKEN_RPAREN, 0};
        default:
            if (isdigit(token.value)) {
                int value = token.value - '0';
                while (token_index < MAX_TOKENS && isdigit(tokens[token_index].value)) {
                    value = value * 10 + tokens[token_index++].value - '0';
                }
                return (Token){TOKEN_NUMBER, value};
            } else if (token.value == '\0') {
                return (Token){TOKEN_EOF, 0};
            } else {
                error("Unexpected character");
            }
    }
}

int precedence(TokenType type) {
    switch (type) {
        case TOKEN_MULTIPLY:
        case TOKEN_DIVIDE:
            return 2;
        case TOKEN_PLUS:
        case TOKEN_MINUS:
            return 1;
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
            error("Invalid operator");
  operators[--top_operator] = token.type;
}

int evaluate_expression() {
    int values[MAX_TOKENS] = {0, 0}; // Initialize with a default value for the first element
    TokenType operators[MAX_TOKENS] = {TOKEN_PLUS}; // Default to addition for the first value
    int top_value = 0, top_operator = 0;
    while (tokens[token_index].type != TOKEN_EOF) {
        Token token = get_next_token(); // Fix: Use get_next_token() instead of accessing tokens[token_index]

        switch (token.type) {
            case TOKEN_NUMBER:
                values[top_value] = token.value;
                break;
            case TOKEN_PLUS:
            case TOKEN_MINUS:
            case TOKEN_MULTIPLY:
            case TOKEN_DIVIDE:
                while (top_operator > 0 && precedence(operators[top_operator - 1]) >= precedence(token.type)) {
                    int b = values[top_value--];
                    int a = values[top_value--];
                    operators[--top_operator] = token.type;
                    values[top_value++] = apply_operator(a, b, operators[top_operator]);
                }
                operators[top_operator++] = token.type;
                break;
            case TOKEN_LPAREN:
                values[top_value] = evaluate_expression();
                break;
            case TOKEN_RPAREN:
                return values[top_value];
        }
    }

    while (top_operator > 0) {
        int b = values[top_value--];
        int a = values[top_value--];
        operators[--top_operator] = token.type;
        values[top_value++] = apply_operator(a, b, operators[top_operator]);
    }

    return values[0];
}

int main() {
    tokens[token_index++] = (Token){TOKEN_NUMBER, 1};
    tokens[token_index++] = (Token){TOKEN_PLUS, 0};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    printf("1 + 2 => %d\n", evaluate_expression());

    token_index = 0;
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, 0};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 3};
    tokens[token_index++] = (Token){TOKEN_PLUS, 0};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 4};
    printf("2 * 3 + 4 => %d\n", evaluate_expression());

    token_index = 0;
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, 0};
    tokens[token_index++] = (Token){TOKEN_LPAREN, 0};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 3};
    tokens[token_index++] = (Token){TOKEN_PLUS, 0};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 4};
    tokens[token_index++] = (Token){TOKEN_RPAREN, 0};
    printf("2 * (3 + 4) => %d\n", evaluate_expression());

    token_index = 0;
    tokens[token_index++] = (Token){TOKEN_NUMBER, 8};
    tokens[token_index++] = (Token){TOKEN_DIVIDE, 0};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, 0};
    tokens[token_index++] = (Token){TOKEN_LPAREN, 0};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_PLUS, 0};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_RPAREN, 0};
    printf("8 / 2 * (2 + 2) => %d\n", evaluate_expression());

    return 0;
}
