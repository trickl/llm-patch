#include "expression_tokenizer.h" // New include for the tokenization logic
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKENS 100

typedef enum { NUMBER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN } TokenType;
typedef struct {
    TokenType type;
    int value;
} Token;

Token tokens[MAX_TOKENS];
int token_count = 0;

Tokenizer::tokenize(const char *expression); // Use the new class method for tokenization
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
            if (token_count > 0 && tokens[token_count - 1].type == NUMBER) {
                tokens[token_count - 1].value *= -1;
            } else {
                tokens[token_count++] = (Token){MINUS, 0};
            }
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
        case PLUS:
        case MINUS: return 1;
        case MUL:
        case DIV: return 2;
        default: return -1;
    }
}

int apply_operator(int a, int b, TokenType op) {
    switch (op) {
        case PLUS: return a + b;
        case MINUS: return a - b;
        case MUL: return a * b;
        case DIV: return a / b;
        default: return 0;
    }
}

int evaluate() {
    int values[MAX_TOKENS] = {0};
    TokenType ops[MAX_TOKENS] = {0};
    int top_value = -1, top_op = -1;

    for (int i = 0; i < token_count; i++) {
        Token t = tokens[i];
        if (t.type == NUMBER) {
            values[++top_value] = t.value;
        } else if (t.type == LPAREN) {
            ops[++top_op] = t.type;
        } else if (t.type == RPAREN) {
            while (ops[top_op] != LPAREN) {
                int b = values[top_value--];
                int a = values[top_value--];
                values[top_value++] = apply_operator(a, b, ops[top_op--]);
            }
            top_op--;
        } else {
            while (top_op >= 0 && precedence(ops[top_op]) >= precedence(t.type)) {
                int b = values[top_value--];
                int a = values[top_value--];
                values[top_value++] = apply_operator(a, b, ops[top_op--]);
            }
            ops[++top_op] = t.type;
        }
    }

    while (top_op >= 0) {
        int b = values[top_value--];
        int a = values[top_value--];
        values[top_value++] = apply_operator(a, b, ops[top_op--]);
    }

    return values[0];
}

int main() {
    const char *expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (const char *expr : expressions) {
        tokenize(expr);
        printf("%s => %d\n", expr, evaluate());
    }
    return 0;
}
