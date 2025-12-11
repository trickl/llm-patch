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
        case TOKEN_PLUS:
        case TOKEN_MINUS:
        case TOKEN_MULTIPLY:
        case TOKEN_DIVIDE:
        case TOKEN_LPAREN:
        case TOKEN_RPAREN:
            break;
        default:
            error("Unexpected token");
    }

    return current;
}

int evaluate_expression() {
    int result = evaluate_term();
    while (tokens[token_index].type == TOKEN_PLUS || tokens[token_index].type == TOKEN_MINUS) {
        TokenType operator = tokens[token_index++].type;
        if (operator == TOKEN_PLUS) {
            result += evaluate_term();
        } else {
            result -= evaluate_term();
        }
    }
    return result;
}

int evaluate_term() {
    int result = evaluate_factor();
    while (tokens[token_index].type == TOKEN_MULTIPLY || tokens[token_index].type == TOKEN_DIVIDE) {
        TokenType operator = tokens[token_index++].type;
        if (operator == TOKEN_MULTIPLY) {
            result *= evaluate_factor();
        } else {
            int divisor = evaluate_factor();
            if (divisor == 0) {
                error("Division by zero");
            }
            result /= divisor;
        }
    }
    return result;
}

int evaluate_factor() {
    Token current = get_next_token();
    switch (current.type) {
        case TOKEN_NUMBER:
            return current.value;
        case TOKEN_LPAREN:
            int result = evaluate_expression();
            if (tokens[token_index++].type != TOKEN_RPAREN) {
                error("Expected ')'");
            }
            return result;
        case TOKEN_MINUS:
            return -evaluate_factor();
        default:
            error("Unexpected token");
    }
}

void tokenize(const char *expression) {
    int i = 0, j = 0;
    while (expression[i]) {
        if (isdigit(expression[i])) {
            tokens[j].type = TOKEN_NUMBER;
            tokens[j++].value = expression[i] - '0';
        } else if (isspace(expression[i])) {
            i++;
        } else {
            switch (expression[i]) {
                case '+':
                    tokens[j].type = TOKEN_PLUS;
                    break;
                case '-':
                    tokens[j].type = TOKEN_MINUS;
                    break;
                case '*':
                    tokens[j].type = TOKEN_MULTIPLY;
                    break;
                case '/':
                    tokens[j].type = TOKEN_DIVIDE;
                    break;
                case '(':
                    tokens[j].type = TOKEN_LPAREN;
                    break;
                case ')':
                    tokens[j].type = TOKEN_RPAREN;
                    break;
                default:
                    error("Unexpected character");
            }
            i++;
            j++;
        }
    }
    tokens[j].type = TOKEN_EOF;
}

int main() {
    tokenize("1 + 2");
    printf("%d\n", evaluate_expression()); // Output: 3

    tokenize("2 * 3 + 4");
    printf("%d\n", evaluate_expression()); // Output: 10

    tokenize("2 * (3 + 4)");
    printf("%d\n", evaluate_expression()); // Output: 14

    tokenize("8 / 2 * (2 + 2)");
    printf("%d\n", evaluate_expression()); // Output: 16

    return 0;
}