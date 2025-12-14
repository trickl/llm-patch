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
            if (token_count > 0 && (tokens[token_count - 1].type == TOKEN_LPAREN || tokens[token_count - 1].type == TOKEN_NUMBER)) {
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
        case TOKEN_DIVIDE: return 2;
        case TOKEN_PLUS:
        case TOKEN_MINUS: return 1;
        default: return 0;
    }
}

int evaluate(int a, int b, TokenType op) {
    switch (op) {
        case TOKEN_PLUS: return a + b;
        case TOKEN_MINUS: return a - b;
        case TOKEN_MULTIPLY: return a * b;
        case TOKEN_DIVIDE: return a / b;
        default: return 0;
    }
}

int parse_and_evaluate() {
    int values[MAX_TOKENS] = {0};
    TokenType ops[MAX_TOKENS] = {TOKEN_PLUS};
    int value_count = 1, op_count = 0;

    for (int i = 0; i < token_count; i++) {
        if (tokens[i].type == TOKEN_NUMBER) {
            values[value_count++] = tokens[i].value;
        } else if (tokens[i].type == TOKEN_PLUS || tokens[i].type == TOKEN_MINUS ||
                   tokens[i].type == TOKEN_MULTIPLY || tokens[i].type == TOKEN_DIVIDE) {
            while (op_count > 0 && precedence(ops[op_count - 1]) >= precedence(tokens[i].type)) {
                int b = values[value_count - 1];
                value_count--;
                int a = values[value_count - 1];
                value_count--;
                ops[op_count--] = tokens[i].type;
                values[value_count++] = evaluate(a, b, ops[op_count]);
            }
            ops[op_count++] = tokens[i].type;
        } else if (tokens[i].type == TOKEN_LPAREN) {
            ops[op_count++] = tokens[i].type;
        } else if (tokens[i].type == TOKEN_RPAREN) {
            while (ops[op_count - 1] != TOKEN_LPAREN) {
                int b = values[value_count - 1];
                value_count--;
                int a = values[value_count - 1];
                value_count--;
                ops[op_count--] = tokens[op_count];
                values[value_count++] = evaluate(a, b, ops[op_count]);
            }
            op_count--; // Pop the '('
        }
    }

    while (op_count > 0) {
        int b = values[value_count - 1];
        value_count--;
        int a = values[value_count - 1];
        value_count--;
        ops[op_count--] = tokens[op_count];
        values[value_count++] = evaluate(a, b, ops[op_count]);
    }

    return values[0];
}

int main() {
    tokenize("3 + 4 * (2 - 1)");
    printf("%d\n", parse_and_evaluate()); // Output: 7

    tokenize("2 * 3 + 4");
    printf("%d\n", parse_and_evaluate()); // Output: 10

    tokenize("2 * (3 + 4)");
    printf("%d\n", parse_and_evaluate()); // Output: 14

    tokenize("8 / 2 * (2 + 2)");
    printf("%d\n", parse_and_evaluate()); // Output: 16

    return 0;
}