#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKENS 100

typedef enum { NUMBER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, END_OF_FILE } TokenType;

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

Token getNextToken() {
    while (isspace(tokens[tokenIndex].value)) {
        tokenIndex++;
    }

    if (tokenIndex >= MAX_TOKENS) {
        return (Token){EOF};
    }

    Token token = tokens[tokenIndex];
    tokenIndex++;

    return token;
}

int applyOp(int a, int b, char op) {
    switch (op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/':
            if (b == 0) error("Division by zero");
            return a / b;
        default: return 0;
    }
}

int precedence(char op) {
    if (op == '+' || op == '-') return 1;
    if (op == '*' || op == '/') return 2;
    return 0;
}

int evaluate() {
    int values[MAX_TOKENS] = {0};
    char ops[MAX_TOKENS] = {'\0'};
    int topValues = -1, topOps = -1;

    for (int i = 0; i < tokenIndex; i++) {
        Token currentToken = tokens[i];

        if (currentToken.type == NUMBER) {
            values[++topValues] = currentToken.value;
        } else if (currentToken.type == LPAREN) {
            ops[++topOps] = currentToken.value;
        } else if (currentToken.type == RPAREN) {
            while (ops[topOps] != '(') {
                int b = values[topValues--];
                int a = values[topValues--];
                char op = ops[topOps--];
                values[++topValues] = applyOp(a, b, op);
            }
            topOps--;
        } else {
            while (topOps >= 0 && precedence(ops[topOps]) >= precedence(currentToken.value)) {
                int b = values[topValues--];
                int a = values[topValues--];
                char op = ops[topOps--];
                values[++topValues] = applyOp(a, b, op);
            }
            ops[++topOps] = currentToken.value;
        }
    }

    while (topOps >= 0) {
        int b = values[topValues--];
        int a = values[topValues--];
        char op = ops[topOps--];
        values[++topValues] = applyOp(a, b, op);
    }

    return values[0];
}

void tokenize(const char *expression) {
    tokenIndex = 0;
    for (int i = 0; expression[i]; i++) {
        if (isspace(expression[i])) continue;

        Token token;
        if (isdigit(expression[i])) {
            int value = 0;
            while (i < strlen(expression) && isdigit(expression[i])) {
                value = value * 10 + (expression[i] - '0');
                i++;
            }
            token.type = NUMBER;
            token.value = value;
            tokens[tokenIndex++] = token;
            i--;
        } else if (expression[i] == '+' || expression[i] == '-' ||
                   expression[i] == '*' || expression[i] == '/' ||
                   expression[i] == '(' || expression[i] == ')') {
            token.type = expression[i];
            token.value = expression[i];
            tokens[tokenIndex++] = token;
        } else {
            error("Invalid character");
        }
    }
}

int main() {
    tokenize("3 + 4 * (2 - 1)");
    printf("%d\n", evaluate()); // Output: 9

    tokenize("2 * 3 + 4");
    printf("%d\n", evaluate()); // Output: 10

    tokenize("2 * (3 + 4)");
    printf("%d\n", evaluate()); // Output: 14

    tokenize("8 / 2 * (2 + 2)");
    printf("%d\n", evaluate()); // Output: 16

    return 0;
}