#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_TOKEN_LENGTH 256

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

Token tokenize(const char **input) {
    while (**input && isspace(**input)) (*input)++;
    if (!**input) return (Token){TOKEN_EOF, 0};

    if (**input == '+') {
        (*input)++;
        return (Token){TOKEN_PLUS, 0};
    } else if (**input == '-') {
        (*input)++;
        return (Token){TOKEN_MINUS, 0};
    } else if (**input == '*') {
        (*input)++;
        return (Token){TOKEN_MULTIPLY, 0};
    } else if (**input == '/') {
        (*input)++;
        return (Token){TOKEN_DIVIDE, 0};
    } else if (**input == '(') {
        (*input)++;
        return (Token){TOKEN_LPAREN, 0};
    } else if (**input == ')') {
        (*input)++;
        return (Token){TOKEN_RPAREN, 0};
    }

    Token token = {TOKEN_NUMBER, 0};
    while (**input && isdigit(**input)) {
        token.value = token.value * 10 + (**input - '0');
        (*input)++;
    }
    return token;
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

int parse_and_evaluate(const char *expression) {
    const char *input = expression;
    Token tokens[MAX_TOKEN_LENGTH];
    int token_count = 0;

    while (**input != '\0') {
        tokens[token_count++] = tokenize(input); // Fix: Pass input instead of &input
     }

    int values[token_count];
    TokenType ops[token_count - 1];
    int value_index = 0, op_index = 0;

    for (int i = 0; i < token_count; i++) {
        if (tokens[i].type == TOKEN_NUMBER) {
            values[value_index++] = tokens[i].value;
        } else if (tokens[i].type == TOKEN_LPAREN) {
            int j = i + 1, depth = 1;
            while (depth > 0) {
                if (tokens[j].type == TOKEN_LPAREN) depth++;
                else if (tokens[j].type == TOKEN_RPAREN) depth--;
                j++;
            }
            values[value_index] = parse_and_evaluate(expression + i + 1);
            value_index++;
            i = j - 1;
        } else {
            while (op_index > 0 && precedence(ops[op_index - 1]) >= precedence(tokens[i].type)) {
                int b = values[--value_index];
                int a = values[--value_index];
                ops[--op_index] = tokens[i].type;
                values[value_index++] = evaluate(a, b, ops[op_index]);
            }
            ops[op_index++] = tokens[i].type;
        }
    }

    while (op_index > 0) {
        int b = values[--value_index];
        int a = values[--value_index];
        ops[--op_index] = tokens[token_count - 1].type;
        values[value_index++] = evaluate(a, b, ops[op_index]);
    }

    return values[0];
}

int main() {
    printf("%d\n", parse_and_evaluate("3 + 4 * (2 - 1)")); // Output: 9
    printf("%d\n", parse_and_evaluate("2 * 3 + 4"));       // Output: 10
    printf("%d\n", parse_and_evaluate("2 * (3 + 4)"));     // Output: 14
    printf("%d\n", parse_and_evaluate("8 / 2 * (2 + 2)"));   // Output: 16

    return 0;
}
