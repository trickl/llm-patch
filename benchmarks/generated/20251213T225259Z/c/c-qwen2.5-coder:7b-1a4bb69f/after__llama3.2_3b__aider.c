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

void skip_whitespace(const char **input) {
    while (**input && isspace(**input)) {
        (*input)++;
    }
}

Token get_next_token(const char **input) {
    skip_whitespace(input);

    if (**input == '\0') {
        return (Token){TOKEN_EOF, 0};
    }

    Token token;
    switch (**input) {
        case '+':
            token.type = TOKEN_PLUS;
            (*input)++;
            break;
        case '-':
            token.type = TOKEN_MINUS;
            (*input)++;
            break;
        case '*':
            token.type = TOKEN_MULTIPLY;
            (*input)++;
            break;
        case '/':
            token.type = TOKEN_DIVIDE;
            (*input)++;
            break;
        case '(':
            token.type = TOKEN_LPAREN;
            (*input)++;
            break;
        case ')':
            token.type = TOKEN_RPAREN;
            (*input)++;
            break;
        default:
            if (isdigit(**input)) {
                int value = 0;
                while (**input && isdigit(**input)) {
                    value = value * 10 + (**input - '0');
                    (*input)++;
                }
                token.type = TOKEN_NUMBER;
                token.value = value;
            } else {
                error("Unexpected character");
            }
    }

    return token;
}

int parse_number() {
    if (tokens[token_index].type != TOKEN_NUMBER) {
        error("Expected a number");
    }
    int value = tokens[token_index++].value;
    return value;
}

int parse_factor() {
    Token current_token = tokens[token_index];
    switch (current_token.type) {
        case TOKEN_NUMBER:
            return parse_number();
        case TOKEN_MINUS:
            token_index++;
            return -parse_factor();
        case TOKEN_LPAREN:
            token_index++;
            int result = parse_expression();
            if (tokens[token_index].type != TOKEN_RPAREN) {
                error("Expected ')'");
            }
            token_index++;
            return result;
        default:
            error("Unexpected token in factor");
    }
}

int parse_term() {
    int result = parse_factor();
    while (token_index < MAX_TOKENS && (tokens[token_index].type == TOKEN_MULTIPLY || tokens[token_index].type == TOKEN_DIVIDE)) {
        Token current_token = tokens[token_index++];
        if (current_token.type == TOKEN_MULTIPLY) {
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
  int result = parse_expression();
    while (token_index  MAX_TOKENS && (tokens[token_index].type == TOKEN_PLUS || tokens[token_index].type == TOKEN_MINUS)) {
      Token current_token = get_next_token(&input);
      if (current_token.type == TOKEN_PLUS) {
        result += parse_term();
      } else {
        result -= parse_term();
      }
    }
  return result;
    return result;
}

int evaluate(const char *expression) {
    token_index = 0;
    const char *input = expression;
    while (*input) {
        tokens[token_index++] = get_next_token(&input);
    }

    if (tokens[0].type == TOKEN_EOF) {
        error("Empty expression");
    }

    int result = parse_expression();
    if (tokens[token_index].type != TOKEN_EOF) {
        error("Unexpected token at end of expression");
    }

    return result;
}

int main() {
    printf("%d\n", evaluate("1 + 2")); // Output: 3
    printf("%d\n", evaluate("2 * 3 + 4")); // Output: 10
    printf("%d\n", evaluate("2 * (3 + 4)")); // Output: 14
    printf("%d\n", evaluate("8 / 2 * (2 + 2)")); // Output: 16

    return 0;
}
