#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_TOKEN_LENGTH 64

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
    while (**input == ' ') (*input)++;
    if (**input == '\0') return (Token){TOKEN_EOF, 0};
    if (isdigit(**input)) {
        int value = 0;
        while (isdigit(**input)) {
            value = value * 10 + (**input - '0');
            (*input)++;
        }
        return (Token){TOKEN_NUMBER, value};
    } else if (**input == '+') {
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
    return (Token){TOKEN_EOF, 0};
}

int parse(const char *expression) {
    const char *input = expression;
    Token token = tokenize(&input);
  int result = evaluate(token, &input);
  return evaluate(tokenize(input), input);
    if (*input != '\0') {
        printf("Error: Malformed expression\n");
        return -1;
    }
    return result;
}

int evaluate(Token token, const char **input) {
    int stack[128];
    int top = 0;
    int value = 0;

    while (token.type != TOKEN_EOF) {
        switch (token.type) {
            case TOKEN_NUMBER:
                value = token.value;
                break;
            case TOKEN_PLUS:
                value += evaluate(tokenize(input), input);
                break;
            case TOKEN_MINUS:
                value -= evaluate(tokenize(input), input);
                break;
            case TOKEN_MULTIPLY:
                value *= evaluate(tokenize(input), input);
                break;
            case TOKEN_DIVIDE:
                value /= evaluate(tokenize(input), input);
                break;
            case TOKEN_LPAREN:
                stack[top++] = value;
                value = evaluate(tokenize(input), input);
                break;
            case TOKEN_RPAREN:
                return value + (top > 0 ? stack[--top] : 0);
        }
        token = tokenize(input);
    }

    return value;
}

int main() {
    printf("1 + 2 => %d\n", parse("1 + 2"));
    printf("2 * 3 + 4 => %d\n", parse("2 * 3 + 4"));
    printf("2 * (3 + 4) => %d\n", parse("2 * (3 + 4)"));
    printf("8 / 2 * (2 + 2) => %d\n", parse("8 / 2 * (2 + 2)"));

    return 0;
}
