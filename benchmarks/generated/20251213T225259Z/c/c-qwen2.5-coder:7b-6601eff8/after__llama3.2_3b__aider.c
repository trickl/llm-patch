#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_TOKENS 100

typedef enum {
    TOKEN_TYPE_NUMBER,
    TOKEN_TYPE_OPERATOR,
    TOKEN_TYPE_LPAREN,
    TOKEN_TYPE_RPAREN,
    TOKEN_TYPE_EOF
} TokenType;

typedef struct {
    TokenType type;
    int value;
    char operator = '\0';
} Token;

Token tokens[MAX_TOKENS];
int token_index = 0;

void error(const char *msg) {
    fprintf(stderr, "Error: %s\n", msg);
    exit(1);
}

Token next_token() {
    if (token_index >= MAX_TOKENS) {
        return (Token){TOKEN_TYPE_EOF};
    }
    Token token = tokens[token_index++];
    return token;
}

int is_operator(char c) {
    return c == '+' || c == '-' || c == '*' || c == '/';
}

void tokenize(const char *expression) {
    int i = 0, num = 0;
    while (expression[i]) {
        if (isspace(expression[i])) {
            i++;
            continue;
        }
        if (isdigit(expression[i])) {
            num = 0;
            while (isdigit(expression[i])) {
                num = num * 10 + (expression[i] - '0');
                i++;
            }
            tokens[token_index++] = (Token){TOKEN_TYPE_NUMBER, num};
        } else if (is_operator(expression[i])) {
            tokens[token_index++] = (Token){TOKEN_TYPE_OPERATOR, 0, expression[i]};
            i++;
        } else if (expression[i] == '(') {
            tokens[token_index++] = (Token){TOKEN_TYPE_LPAREN};
            i++;
        } else if (expression[i] == ')') {
            tokens[token_index++] = (Token){TOKEN_TYPE_RPAREN};
            i++;
        } else {
            error("Invalid character");
        }
    }
    tokens[token_index++] = (Token){TOKEN_TYPE_EOF};
}

int precedence(char op) {
    switch (op) {
        case '+':
        case '-':
            return 1;
        case '*':
        case '/':
            return 2;
        default:
            return 0;
    }
}

int apply_operator(int a, int b, char op) {
    switch (op) {
        case '+':
            return a + b;
        case '-':
            return a - b;
        case '*':
            return a * b;
        case '/':
            if (b == 0) error("Division by zero");
            return a / b;
        default:
            error("Invalid operator");
    }
}

int evaluate(int *start, int *end) {
    int value = (*start)->value;
    char op = '\0';
    for (int i = *start + 1; i <= *end; i++) {
        if (i->type == TOKEN_TYPE_OPERATOR) {
            op = i->operator;
        } else if (i->type == TOKEN_TYPE_NUMBER) {
            value = apply_operator(value, i->value, op);
        }
    }
    return value;
}

int parse_expression(int *start, int *end) {
    if (*start > *end) return 0;

    int left = evaluate(start, end);

    while (*start <= *end && tokens[*start].type == TOKEN_TYPE_OPERATOR) {
        char op = tokens[*start].operator;
        int right_start = *start + 1;
        int right_end = *end;

        if (op == '+' || op == '-') {
            int right_value = parse_expression(&right_start, &right_end);
            left = apply_operator(left, right_value, op);
        } else {
            int right_value = parse_expression(&right_start, &right_end);
            left = apply_operator(left, right_value, op);
        }

        *start = right_end + 1;
    }

    return left;
}

int evaluate_expression(const char *expression) {
    tokenize(expression);
    return parse_expression(tokens, tokens + token_index - 2);
}

int main() {
    printf("3 + 4 * (2 - 1) = %d\n", evaluate_expression("3 + 4 * (2 - 1)"));
    printf("2 * 3 + 4 = %d\n", evaluate_expression("2 * 3 + 4"));
    printf("2 * (3 + 4) = %d\n", evaluate_expression("2 * (3 + 4)"));
    printf("8 / 2 * (2 + 2) = %d\n", evaluate_expression("8 / 2 * (2 + 2)"));
    return 0;
}
