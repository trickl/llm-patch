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

int evaluate_expression(int (*get_token)()) {
    Token token = get_token(); // Fixed invalid initializer error by removing the asterisk and parentheses.
    if (token.type == TOKEN_NUMBER) {
      double result = token.value; // Changed 'int' to 'double' for numeric evaluation, assuming floating point operations are desired here as well. This change is made under the assumption that evaluating expressions may require handling of non-integer results and not just integer arithmetic based on context provided in `main()`.
        while (token.type != TOKEN_EOF) {
        while (token.type != TOKEN_EOF) {
            switch (token.type) {
                case TOKEN_PLUS:
                    result += evaluate_expression(get_token);
                    break;
                case TOKEN_MINUS:
                    result -= evaluate_expression(get_token);
                    break;
                default:
                    error("Unexpected token");
            }
            token = get_token();
        }
        return result;
    } else if (token.type == TOKEN_LPAREN) {
        int result = evaluate_expression(get_token);
        if (get_token().type != TOKEN_RPAREN) {
            error("Expected ')'");
        }
        return result;
    } else if (token.type == TOKEN_MINUS) {
        return -evaluate_expression(get_token);
    } else {
        error("Unexpected token");
    }
}

int main() {
    tokens[token_index++] = (Token){TOKEN_NUMBER, '1'};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, '2'};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("1 + 2 => %d\n", evaluate_expression(get_next_token));

    tokens[token_index++] = (Token){TOKEN_NUMBER, '2'};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, '3'};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, '4'};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("2 * 3 + 4 => %d\n", evaluate_expression(get_next_token));

    tokens[token_index++] = (Token){TOKEN_NUMBER, '2'};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index++] = (Token){TOKEN_LPAREN, '('};
    tokens[token_index++] = (Token){TOKEN_NUMBER, '3'};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, '4'};
    tokens[token_index++] = (Token){TOKEN_RPAREN, ')'};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("2 * (3 + 4) => %d\n", evaluate_expression(get_next_token));

    tokens[token_index++] = (Token){TOKEN_NUMBER, '8'};
    tokens[token_index++] = (Token){TOKEN_DIVIDE, '/'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, '2'};
    tokens[token_index++] = (Token){TOKEN_MULTIPLY, '*'};
    tokens[token_index++] = (Token){TOKEN_LPAREN, '('};
    tokens[token_index++] = (Token){TOKEN_NUMBER, '2'};
    tokens[token_index++] = (Token){TOKEN_PLUS, '+'};
    tokens[token_index++] = (Token){TOKEN_NUMBER, '2'};
    tokens[token_index++] = (Token){TOKEN_RPAREN, ')'};
    tokens[token_index++] = (Token){TOKEN_EOF, '\0'};

    printf("8 / 2 * (2 + 2) => %d\n", evaluate_expression(get_next_token));

    return 0;
}
