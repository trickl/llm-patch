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

int parse_number() {
    int value = 0;
    while (isdigit(tokens[token_index].value)) {
        value = value * 10 + tokens[token_index++].value - '0';
    }
    return value;
}

int evaluate_expression(int (*get_token)());

int evaluate_term() {
    Token token = get_next_token();
    int result = token.value;

    while (token.type == TOKEN_MULTIPLY || token.type == TOKEN_DIVIDE) {
        if (token.type == TOKEN_MULTIPLY) {
            result *= parse_number();
        } else {
            int divisor = parse_number();
            if (divisor == 0) {
                error("Division by zero");
            }
            result /= divisor;
        }
        token = get_next_token();
    }

    return result;
}

int evaluate_expression(int (*get_token)()) {
    Token token = get_next_token();
    int result = evaluate_term();

    while (token.type == TOKEN_PLUS || token.type == TOKEN_MINUS) {
        if (token.type == TOKEN_PLUS) {
            result += evaluate_term();
        } else {
            result -= evaluate_term();
        }
        token = get_next_token();
    }

    return result;
}

int main() {
    tokens[token_index++] = (Token){TOKEN_NUMBER, 1};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("1 + 2 => %d\n", evaluate_expression(get_next_token));

    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 3};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 4};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("2 * 3 + 4 => %d\n", evaluate_expression(get_next_token));

    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index++] = (Token){TOKEN_LPAREN, '('};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 3};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 4};
    tokens[token_index++] = (Token){TOKEN_RPAREN, ')'};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("2 * (3 + 4) => %d\n", evaluate_expression(get_next_token));

    tokens[token_index++] = (Token){TOKEN_NUMBER, 8};
    tokens[token_index++] = (Token){TOKEN_DIVIDE, '/'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index++] = (Token){TOKEN_LPAREN, '('};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_RPAREN, ')'};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("8 / 2 * (2 + 2) => %d\n", evaluate_expression(get_next_token));

int evaluate_expression(int (*get_token)(Token *)) {
    Token token = get_token();
    int result = evaluate_term();

    while (token.type == TOKEN_PLUS || token.type == TOKEN_MINUS) {
        if (token.type == TOKEN_PLUS) {
            result += evaluate_term();
        } else {
            result -= evaluate_term();
        }
        token = get_token();
    }

    return result;

    return 0;
}
