#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

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
            tokens[token_count++] = (Token){TOKEN_MINUS, 0};
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
            fprintf(stderr, "Error: Invalid operator\n");
            exit(1);
    }
}

int evaluate(int *start, int *end) {
    if (*start > *end) {
        return 0;
    }

    int i = *start;
    while (i <= *end && tokens[i].type != TOKEN_LPAREN) {
        i++;
    }

    int left = evaluate(start, &i);
    while (i <= *end) {
        TokenType operator = tokens[i++].type;
        int right = evaluate(&i, end);

        if (operator == TOKEN_MINUS && i > *end) {
            return apply_operator(left, -right, operator);
        }

        left = apply_operator(left, right, operator);
    }

    return left;
}

int parse_and_evaluate(const char *expression) {
    tokenize(expression);
    return evaluate(0, token_count - 1);
}

int main() {
    printf("%d\n", parse_and_evaluate("1 + 2")); // Output: 3
    printf("%d\n", parse_and_evaluate("2 * 3 + 4")); // Output: 10
    printf("%d\n", parse_and_evaluate("2 * (3 + 4)")); // Output: 14
    printf("%d\n", parse_and_evaluate("8 / 2 * (2 + 2)")); // Output: 16

    return 0;
}