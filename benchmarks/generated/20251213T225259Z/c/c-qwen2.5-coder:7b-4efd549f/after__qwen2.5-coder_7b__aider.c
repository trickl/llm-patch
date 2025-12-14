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

int evaluate_expression() {
    int result = evaluate_term();
    while (token_index < MAX_TOKENS && (tokens[token_index].type == TOKEN_PLUS || tokens[token_index].type == TOKEN_MINUS)) {
        TokenType operator = tokens[token_index++].type;
        int next_term = evaluate_factor(); // Corrected function call
        if (operator == TOKEN_PLUS) {
            result += next_term;
        } else {
            result -= next_term;
        }
    }
    return result;
}

int evaluate_term() {
    int result = evaluate_factor();
    while (token_index < MAX_TOKENS && (tokens[token_index].type == TOKEN_MULTIPLY || tokens[token_index].type == TOKEN_DIVIDE)) {
        TokenType operator = tokens[token_index++].type;
        int next_factor = evaluate_term(); // Corrected function call
        if (operator == TOKEN_MULTIPLY) {
            result *= next_factor;
        } else {
            if (next_factor == 0) {
                error("Division by zero");
            }
            result /= next_factor;
        }
    }
    return result;
}

int evaluate_factor() {
    Token current = get_next_token();
    switch (current.type) {
        case TOKEN_NUMBER:
            return current.value; // Added return statement
        case TOKEN_PLUS:
            return evaluate_expression();
        case TOKEN_MINUS:
            return -evaluate_expression();
        case TOKEN_LPAREN:
            int result = evaluate_expression();
            if (tokens[token_index].type != TOKEN_RPAREN) {
                error("Expected ')'");
            }
            token_index++;
            return result;
        default:
            error("Unexpected token");
    }
}

int main() {
    tokens[0] = (Token){TOKEN_NUMBER, 1};
    tokens[1] = (Token){TOKEN_PLUS, '+'};
    tokens[2] = (Token){TOKEN_NUMBER, 2};
    tokens[3] = (Token){TOKEN_EOF, '\0'};

    printf("1 + 2 => %d\n", evaluate_expression());

    tokens[0] = (Token){TOKEN_NUMBER, 2};
    tokens[1] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[2] = (Token){TOKEN_NUMBER, 3};
    tokens[3] = (Token){TOKEN_PLUS, '+'};
    tokens[4] = (Token){TOKEN_NUMBER, 4};
    tokens[5] = (Token){TOKEN_EOF, '\0'};

    printf("2 * 3 + 4 => %d\n", evaluate_expression());

    tokens[0] = (Token){TOKEN_NUMBER, 2};
    tokens[1] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[2] = (Token){TOKEN_LPAREN, '('};
    tokens[3] = (Token){TOKEN_NUMBER, 3};
    tokens[4] = (Token){TOKEN_PLUS, '+'};
    tokens[5] = (Token){TOKEN_NUMBER, 4};
    tokens[6] = (Token){TOKEN_RPAREN, ')'};
    tokens[7] = (Token){TOKEN_EOF, '\0'};

    printf("2 * (3 + 4) => %d\n", evaluate_expression());

    tokens[0] = (Token){TOKEN_NUMBER, 8};
    tokens[1] = (Token){TOKEN_DIVIDE, '/'};
    tokens[2] = (Token){TOKEN_NUMBER, 2};
    tokens[3] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[4] = (Token){TOKEN_LPAREN, '('};
    tokens[5] = (Token){TOKEN_NUMBER, 2};
    tokens[6] = (Token){TOKEN_PLUS, '+'};
    tokens[7] = (Token){TOKEN_NUMBER, 2};
    tokens[8] = (Token){TOKEN_RPAREN, ')'};
    tokens[9] = (Token){TOKEN_EOF, '\0'};

    printf("8 / 2 * (2 + 2) => %d\n", evaluate_expression());

    return 0;
}
