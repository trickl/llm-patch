#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Token types
typedef enum {
    NUMBER,
    PLUS,
    MINUS,
    MUL,
    DIV,
    LPAREN,
    RPAREN,
    UNARY_MINUS,
    END_OF_EXPRESSION
} TokenType;

// Token structure
typedef struct {
    TokenType type;
    double value;
    char* str;
} Token;

// Lexer function
Token* lexer(char* expression) {
    Token* tokens = malloc(100 * sizeof(Token));
    int tokenIndex = 0;
    char* currentChar = expression;

    while (*currentChar != '\0') {
        if (isdigit(*currentChar)) {
            double value = 0.0;
            while (isdigit(*currentChar)) {
                value = value * 10 + (*currentChar - '0');
                currentChar++;
            }
            tokens[tokenIndex].type = NUMBER;
            tokens[tokenIndex].value = value;
            tokens[tokenIndex].str = malloc(20);
            strcpy(tokens[tokenIndex].str, "number");
            tokenIndex++;
        } else if (*currentChar == '+') {
            tokens[tokenIndex].type = PLUS;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = malloc(5);
            strcpy(tokens[tokenIndex].str, "+");
            tokenIndex++;
        } else if (*currentChar == '-') {
            tokens[tokenIndex].type = MINUS;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = malloc(4);
            strcpy(tokens[tokenIndex].str, "-");
            tokenIndex++;
        } else if (*currentChar == '*') {
            tokens[tokenIndex].type = MUL;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = malloc(3);
            strcpy(tokens[tokenIndex].str, "*");
            tokenIndex++;
        } else if (*currentChar == '/') {
            tokens[tokenIndex].type = DIV;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = malloc(2);
            strcpy(tokens[tokenIndex].str, "/");
            tokenIndex++;
        } else if (*currentChar == '(') {
            tokens[tokenIndex].type = LPAREN;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = malloc(4);
            strcpy(tokens[tokenIndex].str, "(");
            tokenIndex++;
        } else if (*currentChar == ')') {
            tokens[tokenIndex].type = RPAREN;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = malloc(3);
            strcpy(tokens[tokenIndex].str, ")");
            tokenIndex++;
        } else if (*currentChar == '-') && *(currentChar + 1) != '\0' && isdigit(*(currentChar + 1))) {
            double value = 0.0;
            while (isdigit(*currentChar)) {
                value = value * 10 + (*currentChar - '0');
                currentChar++;
            }
            tokens[tokenIndex].type = UNARY_MINUS;
            tokens[tokenIndex].value = -value;
            tokens[tokenIndex].str = malloc(8);
            strcpy(tokens[tokenIndex].str, "-(");
            tokenIndex++;
        } else {
            break;
        }

        if (tokenIndex >= 100) {
            printf("Error: Expression too long\n");
            exit(1);
        }
    }

    return tokens;
}

// Parser function
Token* parse(Token* tokens) {
    Token* output = malloc(10 * sizeof(Token));
    int tokenIndex = 0;

    while (tokens[tokenIndex].type != END_OF_EXPRESSION && tokenIndex < 100) {
        if (tokens[tokenIndex].type == LPAREN) {
            Token* subExpression = parse(tokens + tokenIndex + 1);
            output[tokenIndex] = *subExpression;
            tokenIndex += 2;
        } else if (tokens[tokenIndex].type == NUMBER || tokens[tokenIndex].type == UNARY_MINUS) {
            double value = tokens[tokenIndex].value;
            if (tokens[tokenIndex].type == UNARY_MINUS) {
                value = -value;
            }
            output[tokenIndex] = {NUMBER, value, NULL};
            tokenIndex++;
        } else {
            Token* left = parse(tokens + tokenIndex);
            Token* right = parse(tokens + tokenIndex + 1);

            if (left.type == NUMBER || left.type == UNARY_MINUS) {
                double leftValue = left.value;
                if (left.type == UNARY_MINUS) {
                    leftValue = -leftValue;
                }
                output[tokenIndex] = {NUMBER, leftValue, NULL};
                tokenIndex += 2;
            } else {
                Token* operator = parse(tokens + tokenIndex);
                double result = 0.0;

                if (operator.type == PLUS) {
                    result = left.value + right.value;
                } else if (operator.type == MINUS) {
                    result = left.value - right.value;
                } else if (operator.type == MUL) {
                    result = left.value * right.value;
                } else if (operator.type == DIV) {
                    if (right.value != 0.0) {
                        result = left.value / right.value;
                    } else {
                        printf("Error: Division by zero\n");
                        exit(1);
                    }
                }

                output[tokenIndex] = {NUMBER, result, NULL};
                tokenIndex += 2;
            }
        }
    }

    return output;
}

// Evaluator function
double evaluate(Token* tokens) {
    Token* output = parse(tokens);

    double result = output->value;

    for (int i = 0; i < 100; i++) {
        if (output[i].type == NUMBER || output[i].type == UNARY_MINUS) {
            continue;
        } else {
            printf("Error: Unexpected token %d\n", output[i].type);
            exit(1);
        }
    }

    return result;
}

int main() {
    char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int numExpressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < numExpressions; i++) {
        Token* tokens = lexer(expressions[i]);
        double result = evaluate(tokens);
        free(tokens);

        printf("%s => %f\n", expressions[i], result);
    }

    return 0;
}