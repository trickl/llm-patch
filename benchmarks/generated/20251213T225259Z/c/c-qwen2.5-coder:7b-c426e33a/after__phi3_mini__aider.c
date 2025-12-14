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
int token_count = 0;

void tokenize(const char *expression) {
    const char *p = expression;
    while (*p != '\0') {
        if (isspace(*p)) {
            p++;
            continue;
        }
        if (isdigit(*p)) {
            int value = 0;
            while (isdigit(*p)) {
                value = value * 10 + (*p - '0');
                p++;
            }
            tokens[token_count++] = (Token){TOKEN_NUMBER, value};
        } else if (*p == '+') {
            tokens[token_count++] = (Token){TOKEN_PLUS, 0};
            p++;
        } else if (*p == '-') {
            if (token_count > 0 && tokens[token_count - 1].type == TOKEN_EOF) {
                tokens[token_count++] = (Token){TOKEN_NUMBER, -1};
            } else {
                tokens[token_count++] = (Token){TOKEN_MINUS, 0};
            }
            p++;
        } else if (*p == '*') {
            tokens[token_count++] = (Token){TOKEN_MULTIPLY, 0};
            p++;
        } else if (*p == '/') {
            tokens[token_count++] = (Token){TOKEN_DIVIDE, 0};
            p++;
        } else if (*p == '(') {
            tokens[token_count++] = (Token){TOKEN_LPAREN, 0};
            p++;
        } else if (*p == ')') {
            tokens[token_count++] = (Token){TOKEN_RPAREN, 0};
            p++;
        }
    }
    tokens[token_count++] = (Token){TOKEN_EOF, 0};
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

int apply_operator(int a, int b, TokenType op) {
    switch (op) {
        case TOKEN_PLUS:
            return a + b;
        case TOKEN_MINUS:
            return a - b;
        case TOKEN_MULTIPLY:
            return a * b;
        case TOKEN_DIVIDE:
            if (b == 0) {
                fprintf(stderr, "Error: Division by zero\n");
                exit(1);
            }
            return a / b;
        default:
            fprintf(stderr, "Error: Invalid operator\n");
            exit(1);
    }
}

int evaluate_expression(int *start, int *end) {
    if (*start > *end) {
        return 0;
    }

    int value = tokens[*start].value;
    TokenType op = TOKEN_PLUS;

    for (int i = *start + 1; i <= *end; i++) {
        if (tokens[i].type == TOKEN_NUMBER) {
            value = apply_operator(value, tokens[i].value, op);
        } else if (tokens[i].type == TOKEN_PLUS || tokens[i].type == TOKEN_MINUS ||
                   tokens[i].type == TOKEN_MULTIPLY || tokens[i].type == TOKEN_DIVIDE) {
            op = tokens[i].type;
        } else if (tokens[i].type == TOKEN_LPAREN) {
            int j = i + 1;
            while (j <= *end && tokens[j].type != TOKEN_RPAREN) {
                j++;
            }
            value = apply_operator(value, evaluate_expression(&i, &j), op);
            i = j + 1;
        }
    }

    return value;
}

int evaluate(const char *expression) {
    tokenize(expression);
    int result = evaluate_expression(0, token_count - 2);
    return result;
}

int main() {
    printf("%d\n", evaluate("3 + 4 * (2 - 1)")); // Output: 9
    printf("%d\n", evaluate("2 * 3 + 4"));       // Output: 10
    printf("%d\n", evaluate("2 * (3 + 4)"));     // Output: 14
    printf("%d\n", evaluate("8 / 2 * (2 + 2)")); // Output: 16
    return 0;
}