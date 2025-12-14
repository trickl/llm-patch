#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKENS 100
#define MAX_EXPRESSION_LENGTH 256

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
}

int evaluate(int *values, int *operators) {
    while (token_count > 1) {
        int max_precedence = -1;
        int max_index = -1;
        for (int i = 0; i < token_count - 1; i++) {
            if ((tokens[i].type == TOKEN_MULTIPLY || tokens[i].type == TOKEN_DIVIDE) && (max_precedence == -1 || max_precedence <= 2)) {
                max_precedence = 2;
                max_index = i;
            } else if ((tokens[i].type == TOKEN_PLUS || tokens[i].type == TOKEN_MINUS) && (max_precedence == -1 || max_precedence <= 1)) {
                max_precedence = 1;
                max_index = i;
            }
        }
        int result = 0;
        switch (tokens[max_index].type) {
            case TOKEN_MULTIPLY:
                result = values[max_index] * values[max_index + 1];
                break;
            case TOKEN_DIVIDE:
                if (values[max_index + 1] == 0) {
                    fprintf(stderr, "Error: Division by zero\n");
                    exit(1);
                }
                result = values[max_index] / values[max_index + 1];
                break;
            case TOKEN_PLUS:
                result = values[max_index] + values[max_index + 1];
                break;
            case TOKEN_MINUS:
                result = values[max_index] - values[max_index + 1];
                break;
        }
        for (int i = max_index; i < token_count - 2; i++) {
            values[i] = values[i + 2];
        }
        for (int i = max_index; i < token_count - 1; i++) {
            operators[i] = operators[i + 1];
        }
        values[max_index] = result;
        token_count--;
    }
    return values[0];
}

int main() {
    const char *expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (const char *expr : expressions) {
        tokenize(expr);
        int values[token_count];
        int operators[token_count - 1];
        int value_index = 0;
        int operator_index = 0;
        for (int i = 0; i  token_count; i++) {
            if (tokens[i].type == TOKEN_NUMBER) {
                values[value_index++] = tokens[i].value;
            } else {
                operators[operator_index++] = tokens[i].type;
        }
        int result = evaluate(values, operators);
        printf("%s => %d\n", expr, result);
    }
    return 0;
}
