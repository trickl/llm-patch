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

int evaluate_expression() {
  int result = evaluate_term();
    while (tokens[token_index].type == TOKEN_PLUS || tokens[token_index].type == TOKEN_MINUS) {
    Token op = get_next_token(); // Added parentheses around this line
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
    while (tokens[token_index].type == TOKEN_MULTIPLY || tokens[token_index].type == TOKEN_DIVIDE) {
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
        case TOKEN_PLUS:
            return evaluate_expression();
        case TOKEN_MINUS:
            return -evaluate_expression();
        case TOKEN_LPAREN:
            int result = evaluate_expression();
            if (tokens[token_index].type != TOKEN_RPAREN) {
                error("Expected ')'");
            }
            get_next_token();
            return result;
        default:
            error("Unexpected token");
    }
}

void tokenize(const char *expression) {
    token_index = 0;
    int i = 0;
    while (expression[i] != '\0') {
        if (isspace(expression[i])) {
            i++;
            continue;
        }

        Token token;
        switch (expression[i]) {
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
                if (isdigit(expression[i])) {
                    int value = 0;
                    while (i < strlen(expression) && isdigit(expression[i])) {
                        value = value * 10 + (expression[i] - '0');
                        i++;
                    }
                    token.type = TOKEN_NUMBER;
                    token.value = value;
                } else {
                    error("Unexpected character");
                }
        }
        tokens[token_index++] = token;
    }
    tokens[token_index].type = TOKEN_EOF;
}

int main() {
    tokenize("3 + 4 * (2 - 1)");
    printf("%d\n", evaluate_expression()); // Output: 7

    tokenize("2 * 3 + 4");
    printf("%d\n", evaluate_expression()); // Output: 10

    tokenize("2 * (3 + 4)");
    printf("%d\n", evaluate_expression()); // Output: 14

    tokenize("8 / 2 * (2 + 2)");
    printf("%d\n", evaluate_expression()); // Output: 16

    return 0;
}
