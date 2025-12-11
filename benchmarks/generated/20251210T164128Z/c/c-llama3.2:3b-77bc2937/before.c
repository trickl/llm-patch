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

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    Token* tokens = malloc(100 * sizeof(Token));
    int tokenIndex = 0;
    char* currentChar = expression;

    while (*currentChar != '\0') {
        if (isdigit(*currentChar)) {
            // Parse number
            double numValue = 0.0;
            int sign = 1;
            while (isdigit(*currentChar) || *currentChar == '.') {
                numValue = numValue * 10 + (*currentChar - '0');
                currentChar++;
            }
            if (*currentChar == '-') {
                sign = -1;
                currentChar++;
            }

            tokens[tokenIndex].type = NUMBER;
            tokens[tokenIndex].value = sign * numValue;
            tokens[tokenIndex].str = NULL;

            tokenIndex++;

        } else if (*currentChar == '+') {
            // Parse plus operator
            tokens[tokenIndex].type = PLUS;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = "+";
            tokenIndex++;

        } else if (*currentChar == '-') {
            // Parse minus operator
            tokens[tokenIndex].type = MINUS;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = "-";
            tokenIndex++;

        } else if (*currentChar == '*') {
            // Parse multiplication operator
            tokens[tokenIndex].type = MUL;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = "*";
            tokenIndex++;

        } else if (*currentChar == '/') {
            // Parse division operator
            tokens[tokenIndex].type = DIV;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = "/";
            tokenIndex++;

        } else if (*currentChar == '(') {
            // Parse left parenthesis
            tokens[tokenIndex].type = LPAREN;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = "(";
            tokenIndex++;

        } else if (*currentChar == ')') {
            // Parse right parenthesis
            tokens[tokenIndex].type = RPAREN;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = ")";
            tokenIndex++;

        } else if (*currentChar == '-') {
            // Parse unary minus operator
            tokens[tokenIndex].type = UNARY_MINUS;
            tokens[tokenIndex].value = 0.0;
            tokens[tokenIndex].str = "-";
            tokenIndex++;

        } else {
            // Error: Unexpected character
            printf("Error: Unexpected character '%c'\n", *currentChar);
            return NULL;
        }
    }

    tokens[tokenIndex].type = END_OF_EXPRESSION;
    tokens[tokenIndex].value = 0.0;
    tokens[tokenIndex].str = NULL;

    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* outputTokens = malloc(100 * sizeof(Token));
    int outputTokenIndex = 0;
    double value = 0.0;

    while (tokens[tokenIndex].type != END_OF_EXPRESSION) {
        if (tokens[tokenIndex].type == NUMBER) {
            // Parse number
            value += tokens[tokenIndex].value;
            tokenIndex++;
        } else if (tokens[tokenIndex].type == PLUS || tokens[tokenIndex].type == MINUS) {
            // Parse addition or subtraction operator
            Token* rightOperand = parser(tokens);
            outputTokens[outputTokenIndex].type = tokens[tokenIndex].type;
            outputTokens[outputTokenIndex].value = value;
            outputTokens[outputTokenIndex].str = tokens[tokenIndex].str;

            if (tokens[tokenIndex].type == PLUS) {
                value += rightOperand.value;
            } else {
                value -= rightOperand.value;
            }

            free(rightOperand);
            tokenIndex++;
        } else if (tokens[tokenIndex].type == MUL || tokens[tokenIndex].type == DIV) {
            // Parse multiplication or division operator
            Token* rightOperand = parser(tokens);
            outputTokens[outputTokenIndex].type = tokens[tokenIndex].type;
            outputTokens[outputTokenIndex].value = value;
            outputTokens[outputTokenIndex].str = tokens[tokenIndex].str;

            if (tokens[tokenIndex].type == MUL) {
                value *= rightOperand.value;
            } else {
                value /= rightOperand.value;
            }

            free(rightOperand);
            tokenIndex++;
        } else if (tokens[tokenIndex].type == LPAREN) {
            // Parse left parenthesis
            Token* rightOperand = parser(tokens + 1);
            outputTokens[outputTokenIndex].type = tokens[tokenIndex].type;
            outputTokens[outputTokenIndex].value = value;
            outputTokens[outputTokenIndex].str = tokens[tokenIndex].str;

            free(rightOperand);
            tokenIndex++;
        } else if (tokens[tokenIndex].type == RPAREN) {
            // Parse right parenthesis
            break;
        } else if (tokens[tokenIndex].type == UNARY_MINUS) {
            // Parse unary minus operator
            Token* operand = parser(tokens + 1);
            outputTokens[outputTokenIndex].type = tokens[tokenIndex].type;
            outputTokens[outputTokenIndex].value = -operand.value;
            outputTokens[outputTokenIndex].str = tokens[tokenIndex].str;

            free(operand);
            tokenIndex++;
        }
    }

    outputTokens[outputTokenIndex].type = END_OF_EXPRESSION;
    outputTokens[outputTokenIndex].value = value;
    outputTokens[outputTokenIndex].str = NULL;

    return outputTokens;
}

// Evaluator function to evaluate the parsed expression
double evaluator(Token* tokens) {
    double result = 0.0;

    for (int i = 0; i < tokenIndex; i++) {
        if (tokens[i].type == NUMBER) {
            result += tokens[i].value;
        }
    }

    return result;
}

// Main function to run the expression evaluator
void main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int numExpressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < numExpressions; i++) {
        Token* tokens = lexer(expressions[i]);
        if (tokens == NULL) {
            printf("Error: Failed to tokenize expression '%s'\n", expressions[i]);
            return;
        }

        Token* parsedTokens = parser(tokens);
        if (parsedTokens == NULL) {
            printf("Error: Failed to parse tokenized expression '%s'\n", expressions[i]);
            free(tokens);
            return;
        }

        double result = evaluator(parsedTokens);
        printf("Result for '%s': %f\n", expressions[i], result);

        free(parsedTokens);
        free(tokens);
    }
}