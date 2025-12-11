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

void error(const char *msg) {
    fprintf(stderr, "Error: %s\n", msg);
    exit(EXIT_FAILURE);
}

void skipWhitespace(char **str) {
    while (**str && isspace(**str)) (*str)++;
}

Token getNextToken(char **str) {
    skipWhitespace(str);

    if (**str == '\0') return (Token){TOKEN_EOF, 0};

    if (isdigit(**str)) {
        int value = 0;
        while (**str && isdigit(**str)) {
            value = value * 10 + (**str - '0');
            (*str)++;
        }
        return (Token){TOKEN_NUMBER, value};
    }

    switch (**str) {
        case '+': (*str)++; return (Token){TOKEN_PLUS, 0};
        case '-': (*str)++; return (Token){TOKEN_MINUS, 0};
        case '*': (*str)++; return (Token){TOKEN_MULTIPLY, 0};
        case '/': (*str)++; return (Token){TOKEN_DIVIDE, 0};
        case '(': (*str)++; return (Token){TOKEN_LPAREN, 0};
        case ')': (*str)++; return (Token){TOKEN_RPAREN, 0};
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
        case TOKEN_DIVIDE: if (b == 0) error("Division by zero"); return a / b;
        default: error("Invalid operator");
    }
}

int parseExpression(char **str, int minPrecedence);

int parseTerm(char **str) {
    Token token = getNextToken(str);
    if (token.type == TOKEN_NUMBER) return token.value;

    if (token.type == TOKEN_MINUS) {
        int value = parseTerm(str);
        return -value;
    }

    if (token.type != TOKEN_LPAREN) error("Expected number or '('");

    int result = parseExpression(str, 0);

    if (getNextToken(str).type != TOKEN_RPAREN) error("Expected ')'");
    return result;
}

int parseFactor(char **str) {
    Token token = getNextToken(str);
    if (token.type == TOKEN_NUMBER) return token.value;

    if (token.type == TOKEN_LPAREN) {
        int result = parseExpression(str, 0);

        if (getNextToken(str).type != TOKEN_RPAREN) error("Expected ')'");
        return result;
    }

    error("Unexpected token in factor");
}

int parseExpression(char **str, int minPrecedence) {
    int left = parseTerm(str);
    Token token;

    while ((token = getNextToken(str)).type != TOKEN_EOF && precedence(token.type) >= minPrecedence) {
        int right = parseFactor(str);

        if (precedence(token.type) < minPrecedence) {
            ungetc(token.value, stdin);
            return left;
        }

        left = evaluate(left, right, token.type);
    }

    ungetc(token.value, stdin);
    return left;
}

int main() {
    char input[256];
    while (1) {
        printf("Enter an expression: ");
        if (!fgets(input, sizeof(input), stdin)) break;

        TokenIndex = 0;
        int result = parseExpression(&input, 0);

        printf("Result: %d\n", result);
    }

    return 0;
}