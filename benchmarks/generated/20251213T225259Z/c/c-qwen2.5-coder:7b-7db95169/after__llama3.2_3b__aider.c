#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_TOKENS 100

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

Token tokens[MAX_TOKENS];
int tokenIndex = 0;

void error(const char *message) {
    fprintf(stderr, "Error: %s\n", message);
    exit(EXIT_FAILURE);
}

void skipWhitespace(char **input) {
    while (**input && isspace(**input)) (*input)++;
}

  Token getNextToken(char **input) {
    skipWhitespace(&input);
     if (**input == '\0') return (Token){TOKEN_EOF, 0};

    if (isdigit(**input)) {
        int value = 0;
        while (**input && isdigit(**input)) {
            value = value * 10 + (**input - '0');
            (*input)++;
        }
        return (Token){TOKEN_NUMBER, value};
    }

    switch (**input) {
        case '+': (*input)++; return (Token){TOKEN_PLUS, 0};
        case '-': (*input)++; return (Token){TOKEN_MINUS, 0};
        case '*': (*input)++; return (Token){TOKEN_MULTIPLY, 0};
        case '/': (*input)++; return (Token){TOKEN_DIVIDE, 0};
        case '(': (*input)++; return (Token){TOKEN_LPAREN, 0};
        case ')': (*input)++; return (Token){TOKEN_RPAREN, 0};
        default: error("Unexpected character");
    }
}

int precedence(TokenType type) {
    switch (type) {
        case TOKEN_PLUS:
        case TOKEN_MINUS: return 1;
        case TOKEN_MULTIPLY:
        case TOKEN_DIVIDE: return 2;
        default: return -1;
    }
}

int evaluate(int a, int b, TokenType op) {
    switch (op) {
        case TOKEN_PLUS: return a + b;
        case TOKEN_MINUS: return a - b;
        case TOKEN_MULTIPLY: return a * b;
        case TOKEN_DIVIDE: return a / b;
        default: error("Invalid operator");
    }
}

int parseExpression(char **input, int precedenceLevel) {
    Token current = getNextToken(input);
    if (current.type == TOKEN_NUMBER) {
        int result = current.value;
        while (tokenIndex < MAX_TOKENS && tokens[tokenIndex].type != TOKEN_EOF) {
            Token next = tokens[tokenIndex++];
            if (precedence(next.type) <= precedenceLevel) break;
            int right = parseExpression(input, precedence(next.type));
            result = evaluate(result, right, next.type);
        }
        return result;
    } else if (current.type == TOKEN_LPAREN) {
        int result = parseExpression(input, 0);
        Token next = getNextToken(input);
        if (next.type != TOKEN_RPAREN) error("Expected ')'");
        return result;
    } else if (current.type == TOKEN_MINUS && tokenIndex < MAX_TOKENS && tokens[tokenIndex].type == TOKEN_NUMBER) {
        int value = tokens[tokenIndex++].value;
        return -value + parseExpression(input, 0);
    } else {
        error("Unexpected token");
    }
}

int evaluateInfix(const char *expression) {
    const char *input = expression;
    while (*input) {
        Token token = getNextToken(&input);
        if (token.type == TOKEN_EOF) break;
        tokens[tokenIndex++] = token;
    }

    return parseExpression((char **)&tokens, 0);
}

int main() {
    printf("%d\n", evaluateInfix("1 + 2")); // Output: 3
    printf("%d\n", evaluateInfix("2 * 3 + 4")); // Output: 10
    printf("%d\n", evaluateInfix("2 * (3 + 4)")); // Output: 14
    printf("%d\n", evaluateInfix("8 / 2 * (2 + 2)")); // Output: 16

    return 0;
}
