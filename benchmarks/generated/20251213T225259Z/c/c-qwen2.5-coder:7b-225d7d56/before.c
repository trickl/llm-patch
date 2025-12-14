#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKEN_LENGTH 1024

typedef enum {
    TOKEN_TYPE_NUMBER,
    TOKEN_TYPE_OPERATOR,
    TOKEN_TYPE_LPAREN,
    TOKEN_TYPE_RPAREN,
    TOKEN_TYPE_EOF
} TokenType;

typedef struct {
    TokenType type;
    char value[MAX_TOKEN_LENGTH];
} Token;

Token tokenize(const char **input) {
    Token token = {TOKEN_TYPE_EOF, ""};
    while (**input && isspace(**input)) (*input)++;
    if (!**input) return token;
    if (isdigit(**input) || (**input == '-' && isdigit((*input)[1]))) {
        int i = 0;
        do {
            token.value[i++] = **input++;
        } while (**input && (isdigit(**input) || **input == '.'));
        token.value[i] = '\0';
        token.type = TOKEN_TYPE_NUMBER;
    } else if (**input == '+' || **input == '-' || **input == '*' || **input == '/') {
        token.value[0] = **input++;
        token.value[1] = '\0';
        token.type = TOKEN_TYPE_OPERATOR;
    } else if (**input == '(') {
        token.value[0] = **input++;
        token.value[1] = '\0';
        token.type = TOKEN_TYPE_LPAREN;
    } else if (**input == ')') {
        token.value[0] = **input++;
        token.value[1] = '\0';
        token.type = TOKEN_TYPE_RPAREN;
    }
    return token;
}

int precedence(char op) {
    switch (op) {
        case '+':
        case '-': return 1;
        case '*':
        case '/': return 2;
        default: return -1;
    }
}

int apply_operator(int a, int b, char op) {
    switch (op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return a / b;
        default: return 0;
    }
}

int evaluate_expression(const char *expression) {
    Token tokens[MAX_TOKEN_LENGTH];
    int token_count = 0;

    const char *input = expression;
    while (**input) {
        tokens[token_count++] = tokenize(&input);
    }

    // Shunting Yard Algorithm
    int output_stack[MAX_TOKEN_LENGTH] = {0};
    char operator_stack[MAX_TOKEN_LENGTH] = {0};
    int output_top = -1, operator_top = -1;

    for (int i = 0; i < token_count; i++) {
        Token token = tokens[i];
        if (token.type == TOKEN_TYPE_NUMBER) {
            output_stack[++output_top] = atoi(token.value);
        } else if (token.type == TOKEN_TYPE_LPAREN) {
            operator_stack[++operator_top] = token.value[0];
        } else if (token.type == TOKEN_TYPE_RPAREN) {
            while (operator_stack[operator_top] != '(') {
                int b = output_stack[output_top--];
                int a = output_stack[output_top--];
                char op = operator_stack[operator_top--];
                output_stack[++output_top] = apply_operator(a, b, op);
            }
            operator_top--; // Pop '('
        } else if (token.type == TOKEN_TYPE_OPERATOR) {
            while (operator_top >= 0 && precedence(operator_stack[operator_top]) >= precedence(token.value[0])) {
                int b = output_stack[output_top--];
                int a = output_stack[output_top--];
                char op = operator_stack[operator_top--];
                output_stack[++output_top] = apply_operator(a, b, op);
            }
            operator_stack[++operator_top] = token.value[0];
        }
    }

    while (operator_top >= 0) {
        int b = output_stack[output_top--];
        int a = output_stack[output_top--];
        char op = operator_stack[operator_top--];
        output_stack[++output_top] = apply_operator(a, b, op);
    }

    return output_stack[output_top];
}

int main() {
    printf("%d\n", evaluate_expression("1 + 2")); // Output: 3
    printf("%d\n", evaluate_expression("2 * 3 + 4")); // Output: 10
    printf("%d\n", evaluate_expression("2 * (3 + 4)")); // Output: 14
    printf("%d\n", evaluate_expression("8 / 2 * (2 + 2)")); // Output: 16
    return 0;
}