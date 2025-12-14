#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKENS 100

typedef enum { TOKEN_NUMBER, TOKEN_PLUS, TOKEN_MINUS, TOKEN_MULTIPLY, TOKEN_DIVIDE, TOKEN_LPAREN, TOKEN_RPAREN, TOKEN_EOF } TokenType;
typedef struct {
    TokenType type;
    int value;
} Token;

Token tokens[MAX_TOKENS];
int tokenIndex = 0;

void error(const char *msg) {
    fprintf(stderr, "Error: %s\n", msg);
    exit(1);
}

void skipWhitespace() {
    while (isspace(tokens[tokenIndex].value)) {
        tokenIndex++;
    }
}

int isOperator(int ch) {
    return ch == '+' || ch == '-' || ch == '*' || ch == '/';
}

int precedence(int op) {
    switch (op) {
        case '*':
        case '/': return 2;
        case '+':
        case '-': return 1;
        default: return 0;
    }
}

Token getNextToken() {
    skipWhitespace();
    Token token = tokens[tokenIndex++];
    if (token.type == TOKEN_EOF) {
        error("Unexpected end of input");
    }
    return token;
}

int evaluateExpression(int left, int op, int right) {
    switch (op) {
        case '+': return left + right;
        case '-': return left - right;
        case '*': return left * right;
        case '/': if (right == 0) error("Division by zero"); return left / right;
        default: error("Unknown operator");
    }
}

int parseExpression() {
    int result = parseTerm();
    while (tokenIndex < MAX_TOKENS && isOperator(tokens[tokenIndex].value)) {
        int op = tokens[tokenIndex++].value;
        int right = parseFactor(); // Corrected function call
        result = evaluateExpression(result, op, right);
    }
    return result;
}

int parseTerm() {
    int result = parseFactor();
    while (tokenIndex < MAX_TOKENS && (tokens[tokenIndex].type == TOKEN_MULTIPLY || tokens[tokenIndex].type == TOKEN_DIVIDE)) {
        int op = tokens[tokenIndex++].value;
        int right = parseTerm(); // Corrected function call
        result = evaluateExpression(result, op, right);
    }
    return result;
}

int parseFactor() {
    if (tokens[tokenIndex].type == TOKEN_NUMBER) {
        int value = tokens[tokenIndex++].value;
        return value;
    } else if (tokens[tokenIndex].type == TOKEN_MINUS) {
        tokenIndex++;
        return -parseFactor();
    } else if (tokens[tokenIndex].type == TOKEN_LPAREN) {
        tokenIndex++;
        int result = parseExpression();
        if (tokens[tokenIndex].type != TOKEN_RPAREN) {
            error("Expected ')'");
        }
        tokenIndex++;
        return result;
    } else {
        error("Unexpected token");
        return 0;
    }
}

void tokenize(const char *input) {
    int i = 0, j = 0;
    while (i < strlen(input)) {
        if (isdigit(input[i])) {
            int value = 0;
            while (i < strlen(input) && isdigit(input[i])) {
                value = value * 10 + (input[i++] - '0');
            } // Corrected indentation
            tokens[j].type = TOKEN_NUMBER;
            tokens[j++].value = value;
        } else if (isOperator(input[i])) {
            tokens[j].type = input[i];
            tokens[j++].value = input[i++];
        } else if (input[i] == '(') {
            tokens[j].type = TOKEN_LPAREN;
            tokens[j++].value = input[i++];
        } else if (input[i] == ')') {
            tokens[j].type = TOKEN_RPAREN;
            tokens[j++].value = input[i++];
        } else if (isspace(input[i])) {
            i++;
        } else {
            error("Unexpected character");
        }
    }
    tokens[j].type = TOKEN_EOF;
}

int evaluate(const char *input) {
    tokenize(input);
    return parseExpression();
}

int main() {
    printf("%d\n", evaluate("1 + 2")); // Output: 3
    printf("%d\n", evaluate("2 * 3 + 4")); // Output: 10
    printf("%d\n", evaluate("2 * (3 + 4)")); // Output: 14
    printf("%d\n", evaluate("8 / 2 * (2 + 2)")); // Output: 16
    return 0;
}
