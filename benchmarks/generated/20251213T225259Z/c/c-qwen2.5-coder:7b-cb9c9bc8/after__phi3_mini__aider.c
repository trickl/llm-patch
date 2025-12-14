#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_TOKENS 100

typedef enum { TOKEN_NUMBER, TOKEN_PLUS, TOKEN_MINUS, TOKEN_MULTIPLY, TOKEN_DIVIDE, TOKEN_LPAREN, TOKEN_RPAREN } TokenType;
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
            if (token_count > 0 && tokens[token_count - 1].type == TOKEN_LPAREN) {
                tokens[token_count++] = (Token){TOKEN_MINUS, 0};
            } else {
                int value = 0;
                while (isdigit(*p)) {
                    value = value * 10 + (*p - '0');
                    p++;
                }
                tokens[token_count++] = (Token){TOKEN_NUMBER, -value};
            }
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
            if (b == 0) {
                fprintf(stderr, "Error: Division by zero\n");
                exit(1);
            }
            return a / b;
        default:
            fprintf(stderr, "Error: Unknown operator\n");
            exit(1);
    }
}

int evaluate(int *start, int *end) {
    if (*start > *end) {
        fprintf(stderr, "Error: Invalid expression\n");
        exit(1);
    }

    int value = tokens[*start].value;
    TokenType operator = TOKEN_PLUS;

    for (int i = *start + 1; i <= *end; i++) {
        if (tokens[i].type == TOKEN_NUMBER) {
            value = apply_operator(value, tokens[i].value, operator);
        } else if (tokens[i].type == TOKEN_PLUS || tokens[i].type == TOKEN_MINUS ||
                   tokens[i].type == TOKEN_MULTIPLY || tokens[i].type == TOKEN_DIVIDE) {
            operator = tokens[i].type;
        } else if (tokens[i].type == TOKEN_LPAREN) {
            int j = i + 1;
            while (j <= *end && tokens[j].type != TOKEN_RPAREN) {
                j++;
            }
            value = apply_operator(value, evaluate(&i, &j), operator);
            i = j + 1;
        }
    }

    return value;
}

int main() {
    tokenize("3 + 4 * (2 - 1)");
    printf("%d\n", evaluate(0, token_count - 1)); // Output: 9

    tokenize("2 * 3 + 4");
    printf("%d\n", evaluate(0, token_count - 1)); // Output: 10

    tokenize("2 * (3 + 4)");
    printf("%d\n", evaluate(0, token_count - 1)); // Output: 14

    tokenize("8 / 2 * (2 + 2)");
    printf("%d\n", evaluate(0, token_count - 1)); // Output: 16

    return 0;
}