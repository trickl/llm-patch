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

Token get_next_token() {
    while (isspace(tokens[token_index].value)) {
        token_index++;
    }

    if (tokens[token_index].type == TOKEN_EOF) {
        return tokens[token_index];
    }

    Token current = tokens[token_index++];
    switch (current.type) {
        case TOKEN_NUMBER:
            break;
        default:
            token_index++;
            break;
    }
    return current;
}

int parse_number() {
    int value = 0;
    while (isdigit(tokens[token_index].value)) {
        value = value * 10 + tokens[token_index++].value - '0';
    }
    return value;
}

int parse_factor() {
    Token token = get_next_token();
    switch (token.type) {
        extern int parse_expression(); // Declare the function here
        case TOKEN_NUMBER:
            return token.value;
        case TOKEN_LPAREN:
            int result = parse_expression();
            if (get_next_token().type != TOKEN_RPAREN) {
                error("Expected ')'");
            }
            return result;
        case TOKEN_MINUS:
            return -parse_factor();
        default:
            error("Unexpected token");
            return 0;
    }
}

int parse_term() {
    int result = parse_factor();
    while (tokens[token_index].type == TOKEN_MULTIPLY || tokens[token_index].type == TOKEN_DIVIDE) {
        Token operator_token = get_next_token();
        if (operator_token.type == TOKEN_MULTIPLY) {
            result *= parse_factor();
        } else {
            int divisor = parse_factor();
            if (divisor == 0) {
                error("Division by zero");
            }
            result /= divisor;
        }
    }
    return result;
}

int parse_expression() {
    int result = parse_term();
    while (tokens[token_index].type == TOKEN_PLUS || tokens[token_index].type == TOKEN_MINUS) {
        Token operator_token = get_next_token();
        if (operator_token.type == TOKEN_PLUS) {
            result += parse_term();
        } else {
            result -= parse_term();
        }
    }
    return result;
}

int evaluate(const char *expression) {
    token_index = 0;
    for (int i = 0; expression[i]; i++) {
        if (isdigit(expression[i])) {
            tokens[token_index].type = TOKEN_NUMBER;
            tokens[token_index++].value = expression[i] - '0';
        } else if (isspace(expression[i])) {
            continue;
        } else {
            switch (expression[i]) {
                case '+':
                    tokens[token_index].type = TOKEN_PLUS;
                    break;
                case '-':
                    tokens[token_index].type = TOKEN_MINUS;
                    break;
                case '*':
                    tokens[token_index].type = TOKEN_MULTIPLY;
                    break;
                case '/':
                    tokens[token_index].type = TOKEN_DIVIDE;
                    break;
                case '(':
                    tokens[token_index].type = TOKEN_LPAREN;
                    break;
                case ')':
                    tokens[token_index].type = TOKEN_RPAREN;
                    break;
                default:
                    error("Unexpected character");
            }
            token_index++;
        }
    }
    tokens[token_index].type = TOKEN_EOF;

    return parse_expression();
}

int main() {
    printf("%d\n", evaluate("1 + 2")); // Output: 3
    printf("%d\n", evaluate("2 * 3 + 4")); // Output: 10
    printf("%d\n", evaluate("2 * (3 + 4)")); // Output: 14
    printf("%d\n", evaluate("8 / 2 * (2 + 2)")); // Output: 16

    return 0;
}
