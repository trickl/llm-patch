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
while (token_index  MAX_TOKENS && tokens[token_index].type == TOKEN_PLUS || tokens[token_index].type == TOKEN_MINUS) {
     Token op = get_next_token(); // Added parentheses around '&&'
      if (op.type == TOKEN_PLUS) {
        result += evaluate_term();
        } else if (op.type == TOKEN_MINUS) {
            result -= evaluate_term();
        }
    }
    return result;
}

int evaluate_term() {
    int result = evaluate_factor();
    while (token_index < MAX_TOKENS && tokens[token_index].type == TOKEN_MULTIPLY || tokens[token_index].type == TOKEN_DIVIDE) {
        Token op = get_next_token();
        if (op.type == TOKEN_MULTIPLY) {
            result *= evaluate_factor();
        } else if (op.type == TOKEN_DIVIDE) {
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
    Token token = get_next_token();
    switch (token.type) {
        case TOKEN_NUMBER:
            return token.value;
        case TOKEN_LPAREN:
            int result = evaluate_expression();
            if (get_next_token().type != TOKEN_RPAREN) {
                error("Expected ')'");
            }
            return result;
        case TOKEN_MINUS:
            return -evaluate_factor();
        default:
            error("Unexpected token");
    }
}

int main() {
    tokens[token_index++] = (Token){TOKEN_NUMBER, 1};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("1 + 2 => %d\n", evaluate_expression());

    tokens[token_index] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index + 1] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index + 2] = (Token){TOKEN_NUMBER, 3};
    tokens[token_index + 3] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index + 4] = (Token){TOKEN_NUMBER, 4};
    tokens[token_index + 5] = (Token){TOKEN_EOF, '\0'};

    printf("2 * 3 + 4 => %d\n", evaluate_expression());

    tokens[token_index] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index + 1] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index + 2] = (Token){TOKEN_LPAREN, '('};
    tokens[token_index + 3] = (Token){TOKEN_NUMBER, 3};
    tokens[token_index + 4] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index + 5] = (Token){TOKEN_NUMBER, 4};
    tokens[token_index + 6] = (Token){TOKEN_RPAREN, ')'};
    tokens[token_index + 7] = (Token){TOKEN_EOF, '\0'};

    printf("2 * (3 + 4) => %d\n", evaluate_expression());

    tokens[token_index] = (Token){TOKEN_NUMBER, 8};
    tokens[token_index + 1] = (Token){TOKEN_DIVIDE, '/'};
    tokens[token_index + 2] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index + 3] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index + 4] = (Token){TOKEN_LPAREN, '('};
    tokens[token_index + 5] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index + 6] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index + 7] = (Token){TOKEN_NUMBER, 2};
    tokens[token_index + 8] = (Token){TOKEN_RPAREN, ')'};
    tokens[token_index + 9] = (Token){TOKEN_EOF, '\0'};

    printf("8 / 2 * (2 + 2) => %d\n", evaluate_expression());

    return 0;
}
