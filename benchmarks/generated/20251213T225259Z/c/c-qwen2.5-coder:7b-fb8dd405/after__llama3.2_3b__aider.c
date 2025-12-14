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

Token getNextToken() {
    while (isspace(tokens[tokenIndex].value)) {
        tokenIndex++;
    }

    if (tokens[tokenIndex].type == TOKEN_EOF) {
        return tokens[tokenIndex];
    }

    Token current = tokens[tokenIndex];
    tokenIndex++;

    switch (current.type) {
        case TOKEN_NUMBER:
            break;
        case TOKEN_PLUS:
        case TOKEN_MINUS:
        case TOKEN_MULTIPLY:
        case TOKEN_DIVIDE:
        case TOKEN_LPAREN:
        case TOKEN_RPAREN:
            break;
        default:
            error("Unexpected token");
    }

    return current;
}

int evaluateExpression() {
  int result = evaluateTerm();
    while (tokens[tokenIndex].type == TOKEN_PLUS || tokens[tokenIndex].type == TOKEN_MINUS) {
    Token op = getNextToken(); // Added parentheses around this line
      if (op.type == TOKEN_PLUS) {
        result += evaluateTerm();
        } else {
            result -= evaluateTerm();
        }
    }
    return result;
}

int evaluateTerm() {
    int result = evaluateFactor();
    while (tokens[tokenIndex].type == TOKEN_MULTIPLY || tokens[tokenIndex].type == TOKEN_DIVIDE) {
        Token op = getNextToken();
        if (op.type == TOKEN_MULTIPLY) {
            result *= evaluateFactor();
        } else {
            int divisor = evaluateFactor();
            if (divisor == 0) {
                error("Division by zero");
            }
            result /= divisor;
        }
    }
    return result;
}

int evaluateFactor() {
    Token token = getNextToken();
    switch (token.type) {
        case TOKEN_NUMBER:
            return token.value;
        case TOKEN_PLUS:
            return evaluateExpression();
        case TOKEN_MINUS:
            return -evaluateExpression();
        case TOKEN_LPAREN:
            int result = evaluateExpression();
            if (tokens[tokenIndex].type != TOKEN_RPAREN) {
                error("Missing right parenthesis");
            }
            getNextToken(); // consume RPAREN
            return result;
        default:
            error("Unexpected token in factor");
    }
}

void tokenize(const char *expression) {
    int i = 0, num = 0, sign = 1;
    while (expression[i]) {
        if (isdigit(expression[i])) {
            num = num * 10 + (expression[i] - '0');
        } else if (expression[i] == '-') {
            if (i > 0 && isdigit(expression[i-1])) {
                tokens[tokenIndex++] = (Token){TOKEN_NUMBER, sign * num};
                num = 0;
                sign = -1;
            } else {
                sign = -1;
            }
        } else if (expression[i] == '+') {
            tokens[tokenIndex++] = (Token){TOKEN_NUMBER, sign * num};
            num = 0;
            sign = 1;
        } else if (expression[i] == '*') {
            tokens[tokenIndex++] = (Token){TOKEN_MULTIPLY, 0};
        } else if (expression[i] == '/') {
            tokens[tokenIndex++] = (Token){TOKEN_DIVIDE, 0};
        } else if (expression[i] == '(') {
            tokens[tokenIndex++] = (Token){TOKEN_LPAREN, 0};
        } else if (expression[i] == ')') {
            tokens[tokenIndex++] = (Token){TOKEN_RPAREN, 0};
        }
        i++;
    }
    if (num != 0 || sign == -1) {
        tokens[tokenIndex++] = (Token){TOKEN_NUMBER, sign * num};
    }
    tokens[tokenIndex++] = (Token){TOKEN_EOF, 0};
}

int main() {
    tokenize("3 + 4 * (2 - 1)");
    printf("%d\n", evaluateExpression()); // Output: 7

    tokenize("2 * 3 + 4");
    printf("%d\n", evaluateExpression()); // Output: 10

    tokenize("2 * (3 + 4)");
    printf("%d\n", evaluateExpression()); // Output: 14

    tokenize("8 / 2 * (2 + 2)");
    printf("%d\n", evaluateExpression()); // Output: 16

    return 0;
}
