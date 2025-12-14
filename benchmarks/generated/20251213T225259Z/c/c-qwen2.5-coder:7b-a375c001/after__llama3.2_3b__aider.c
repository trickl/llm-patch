#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_TOKENS 100

typedef enum { NUMBER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN } TokenType;
typedef struct {
    TokenType type;
    int value;
} Token;

Token tokens[MAX_TOKENS];
int token_count = 0;

void tokenize(const char *expression) {
    const char *p = expression;
    while (*p) {
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
            tokens[token_count++] = (Token){NUMBER, value};
        } else if (*p == '+') {
            tokens[token_count++] = (Token){PLUS, 0};
            p++;
        } else if (*p == '-') {
            tokens[token_count++] = (Token){MINUS, 0};
            p++;
        } else if (*p == '*') {
            tokens[token_count++] = (Token){MUL, 0};
            p++;
        } else if (*p == '/') {
            tokens[token_count++] = (Token){DIV, 0};
            p++;
        } else if (*p == '(') {
            tokens[token_count++] = (Token){LPAREN, 0};
            p++;
        } else if (*p == ')') {
            tokens[token_count++] = (Token){RPAREN, 0};
            p++;
        }
    }
}

int precedence(TokenType type) {
    switch (type) {
        case MUL:
        case DIV: return 2;
        case PLUS:
        case MINUS: return 1;
        default: return 0;
    }
}

int evaluate(int a, int b, TokenType op) {
    switch (op) {
        case PLUS: return a + b;
        case MINUS: return a - b;
        case MUL: return a * b;
        case DIV: return a / b;
        default: return 0;
    }
}

int parse_and_evaluate() {
    int values[MAX_TOKENS];
    TokenType ops[MAX_TOKENS];
    int value_count = 0, op_count = 0;

    for (int i = 0; i < token_count; i++) {
        Token t = tokens[i];
        if (t.type == NUMBER) {
            values[value_count++] = t.value;
        } else if (t.type == LPAREN) {
            int j = i + 1;
            while (j < token_count && tokens[j].type != RPAREN) {
                j++;
            }
            if (j >= token_count) return -1; // Unmatched parenthesis
            values[value_count++] = parse_and_evaluate();
            i = j;
        } else {
            while (op_count > 0 && precedence(ops[op_count - 1]) >= precedence(t.type)) {
                int b = values[--value_count];
                int a = values[--value_count];
                ops[--op_count] = t.type;
                values[value_count++] = evaluate(a, b, t.type);
            }
            ops[op_count++] = t.type;
        }
    }

    while (op_count > 0) {
        int b = values[--value_count];
        int a = values[--value_count];
        ops[--op_count] = tokens[token_count - 1].type;
        values[value_count++] = evaluate(a, b, tokens[token_count - 1].type);
    }

    return values[0];
}

int main() {
    const char *expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (const char *expr : expressions) {
        tokenize(expr);
        int result = parse_and_evaluate();
        printf("%s => %d\n", expr, result);
    }
    return 0;
}
