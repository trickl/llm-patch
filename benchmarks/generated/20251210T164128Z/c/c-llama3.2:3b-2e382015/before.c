#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Token type enum
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
    char* text;
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int length = strlen(expression);
    Token tokens[length];
    int tokenIndex = 0;

    for (int i = 0; i < length; ++i) {
        if (isdigit(expression[i])) {
            double value = 0;
            while (i < length && isdigit(expression[i])) {
                value = value * 10 + expression[i++] - '0';
            }
            tokens[tokenIndex].type = NUMBER;
            tokens[tokenIndex].value = value;
            tokens[tokenIndex].text = malloc(5);
            sprintf(tokens[tokenIndex].text, "%d", (int)value);
            tokenIndex++;
        } else if (expression[i] == '+') {
            tokens[tokenIndex].type = PLUS;
            tokenIndex++;
        } else if (expression[i] == '-') {
            tokens[tokenIndex].type = MINUS;
            tokenIndex++;
        } else if (expression[i] == '*') {
            tokens[tokenIndex].type = MUL;
            tokenIndex++;
        } else if (expression[i] == '/') {
            tokens[tokenIndex].type = DIV;
            tokenIndex++;
        } else if (expression[i] == '(') {
            tokens[tokenIndex].type = LPAREN;
            tokenIndex++;
        } else if (expression[i] == ')') {
            tokens[tokenIndex].type = RPAREN;
            tokenIndex++;
        } else if (expression[i] == '-') {
            tokens[tokenIndex].type = UNARY_MINUS;
            tokenIndex++;
        }
    }

    // Pad with END_OF_EXPRESSION
    Token endToken;
    endToken.type = END_OF_EXPRESSION;
    endToken.value = 0;
    endToken.text = malloc(15);
    sprintf(endToken.text, "%s", "");
    tokens[tokenIndex] = endToken;

    return &tokens[0];
}

// Parser function to parse the tokenized expression
void* parser(Token* tokens) {
    int length = 0;
    for (int i = 0; i < strlen(tokens[length].text); ++i) {
        if (tokens[length].type == NUMBER || tokens[length].type == PLUS ||
            tokens[length].type == MINUS || tokens[length].type == MUL ||
            tokens[length].type == DIV || tokens[length].type == LPAREN ||
            tokens[length].type == RPAREN || tokens[length].type == UNARY_MINUS) {
            length++;
        }
    }

    // Allocate memory for the parsed expression
    void* expression = malloc(length * sizeof(char));
    for (int i = 0; i < length; ++i) {
        if (tokens[i].type == NUMBER) {
            sprintf(expression + i * 5, "%d", (int)tokens[i].value);
        } else if (tokens[i].type == PLUS || tokens[i].type == MINUS ||
                   tokens[i].type == MUL || tokens[i].type == DIV) {
            char* operator = malloc(3);
            switch (tokens[i].type) {
                case PLUS:
                    strcpy(operator, "+");
                    break;
                case MINUS:
                    strcpy(operator, "-");
                    break;
                case MUL:
                    strcpy(operator, "*");
                    break;
                case DIV:
                    strcpy(operator, "/");
                    break;
            }
            sprintf(expression + i * 5, "%s", operator);
        } else if (tokens[i].type == LPAREN) {
            char* parenthesis = malloc(2);
            strcpy(parenthesis, "(");
            sprintf(expression + i * 5, "%s", parenthesis);
        } else if (tokens[i].type == RPAREN) {
            char* parenthesis = malloc(2);
            strcpy(parenthesis, ")");
            sprintf(expression + i * 5, "%s", parenthesis);
        } else if (tokens[i].type == UNARY_MINUS) {
            char* minusOperator = malloc(6);
            strcpy(minusOperator, "-(-");
            sprintf(expression + i * 5, "%s", minusOperator);
        }
    }

    return expression;
}

// Evaluator function to evaluate the parsed expression
double evaluator(void* expression) {
    // Evaluate the expression using a simple recursive descent parser
    double result = 0;
    int operatorIndex = 0;

    while (*expression != '\0') {
        if (*expression == '(') {
            // Handle left parenthesis
            char* parenthesis = malloc(2);
            strcpy(parenthesis, "(");
            ++expression;
            result = evaluator(expression);
            --expression;
            strcpy(parenthesis + 1, ")");
            expression += strlen(parenthesis) - 1;

            while (*expression != '\0' && *expression != '(') {
                if (*expression == '+') {
                    // Handle addition
                    char* operator = malloc(3);
                    strcpy(operator, "+");
                    ++expression;
                    result += evaluator(expression);
                    --expression;
                    strcpy(operator + 2, ")");
                    expression += strlen(operator) - 1;

                    while (*expression != '\0' && *expression != '+' && *expression != '-') {
                        if (*expression == '*') {
                            // Handle multiplication
                            char* operator = malloc(3);
                            strcpy(operator, "*");
                            ++expression;
                            result *= evaluator(expression);
                            --expression;
                            strcpy(operator + 2, ")");
                            expression += strlen(operator) - 1;

                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                if (*expression == '/') {
                                    // Handle division
                                    char* operator = malloc(3);
                                    strcpy(operator, "/");
                                    ++expression;
                                    result /= evaluator(expression);
                                    --expression;
                                    strcpy(operator + 2, ")");
                                    expression += strlen(operator) - 1;

                                    while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                        if (*expression == '-') {
                                            // Handle subtraction
                                            char* operator = malloc(3);
                                            strcpy(operator, "-");
                                            ++expression;
                                            result -= evaluator(expression);
                                            --expression;
                                            strcpy(operator + 2, ")");
                                            expression += strlen(operator) - 1;

                                            while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                if (*expression == '*') {
                                                    // Handle multiplication
                                                    char* operator = malloc(3);
                                                    strcpy(operator, "*");
                                                    ++expression;
                                                    result *= evaluator(expression);
                                                    --expression;
                                                    strcpy(operator + 2, ")");
                                                    expression += strlen(operator) - 1;

                                                    while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                        if (*expression == '/') {
                                                            // Handle division
                                                            char* operator = malloc(3);
                                                            strcpy(operator, "/");
                                                            ++expression;
                                                            result /= evaluator(expression);
                                                            --expression;
                                                            strcpy(operator + 2, ")");
                                                            expression += strlen(operator) - 1;

                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                if (*expression == '-') {
                                                                    // Handle subtraction
                                                                    char* operator = malloc(3);
                                                                    strcpy(operator, "-");
                                                                    ++expression;
                                                                    result -= evaluator(expression);
                                                                    --expression;
                                                                    strcpy(operator + 2, ")");
                                                                    expression += strlen(operator) - 1;

                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                        if (*expression == '*') {
                                                                            // Handle multiplication
                                                                            char* operator = malloc(3);
                                                                            strcpy(operator, "*");
                                                                            ++expression;
                                                                            result *= evaluator(expression);
                                                                            --expression;
                                                                            strcpy(operator + 2, ")");
                                                                            expression += strlen(operator) - 1;

                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                if (*expression == '/') {
                                                                                    // Handle division
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "/");
                                                                                    ++expression;
                                                                                    result /= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                        if (*expression == '-') {
                                                                                            // Handle subtraction
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "-");
                                                                                            ++expression;
                                                                                            result -= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                if (*expression == '*') {
                                                                                                    // Handle multiplication
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "*");
                                                                                                    ++expression;
                                                                                                    result *= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                        if (*expression == '/') {
                                                                                                            // Handle division
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "/");
                                                                                                            ++expression;
                                                                                                            result /= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '/') {
                                                                                                                                    // Handle division
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "/");
                                                                                                                                    ++expression;
                                                                                                                                    result /= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                        if (*expression == '-') {
                                                                                                                                            // Handle subtraction
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "-");
                                                                                                                                            ++expression;
                                                                                                                                            result -= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                                if (*expression == '*') {
                                                                                                                                                    // Handle multiplication
                                                                                                                                                    char* operator = malloc(3);
                                                                                                                                                    strcpy(operator, "*");
                                                                                                                                                    ++expression;
                                                                                                                                                    result *= evaluator(expression);
                                                                                                                                                    --expression;
                                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                                    while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                        if (*expression == '/') {
                                                                                                                                                            // Handle division
                                                                                                                                                            char* operator = malloc(3);
                                                                                                                                                            strcpy(operator, "/");
                                                                                                                                                            ++expression;
                                                                                                                                                            result /= evaluator(expression);
                                                                                                                                                            --expression;
                                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                                                                                    // Handle subtraction
                                                                                                                                                    char* operator = malloc(3);
                                                                                                                                                    strcpy(operator, "-");
                                                                                                                                                    ++expression;
                                                                                                                                                    result -= evaluator(expression);
                                                                                                                                                    --expression;
                                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;
                                                                                            result *= evaluator(expression);
                                                                                            --expression;
                                                                                            strcpy(operator + 2, ")");
                                                                                            expression += strlen(operator) - 1;

                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                if (*expression == '-') {
                                                                                                    // Handle subtraction
                                                                                                    char* operator = malloc(3);
                                                                                                    strcpy(operator, "-");
                                                                                                    ++expression;
                                                                                                    result -= evaluator(expression);
                                                                                                    --expression;
                                                                                                    strcpy(operator + 2, ")");
                                                                                                    expression += strlen(operator) - 1;

                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                        if (*expression == '*') {
                                                                                                            // Handle multiplication
                                                                                                            char* operator = malloc(3);
                                                                                                            strcpy(operator, "*");
                                                                                                            ++expression;
                                                                                                            result *= evaluator(expression);
                                                                                                            --expression;
                                                                                                            strcpy(operator + 2, ")");
                                                                                                            expression += strlen(operator) - 1;

                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                if (*expression == '-') {
                                                                                                                    // Handle subtraction
                                                                                                                    char* operator = malloc(3);
                                                                                                                    strcpy(operator, "-");
                                                                                                                    ++expression;
                                                                                                                    result -= evaluator(expression);
                                                                                                                    --expression;
                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                        if (*expression == '*') {
                                                                                                                            // Handle multiplication
                                                                                                                            char* operator = malloc(3);
                                                                                                                            strcpy(operator, "*");
                                                                                                                            ++expression;
                                                                                                                            result *= evaluator(expression);
                                                                                                                            --expression;
                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                if (*expression == '-') {
                                                                                                                                    // Handle subtraction
                                                                                                                                    char* operator = malloc(3);
                                                                                                                                    strcpy(operator, "-");
                                                                                                                                    ++expression;
                                                                                                                                    result -= evaluator(expression);
                                                                                                                                    --expression;
                                                                                                                                    strcpy(operator + 2, ")");
                                                                                                                                    expression += strlen(operator) - 1;

                                                                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                                                                        if (*expression == '*') {
                                                                                                                                            // Handle multiplication
                                                                                                                                            char* operator = malloc(3);
                                                                                                                                            strcpy(operator, "*");
                                                                                                                                            ++expression;
                                                                                                                                            result *= evaluator(expression);
                                                                                                                                            --expression;
                                                                                                                                            strcpy(operator + 2, ")");
                                                                                                                                            expression += strlen(operator) - 1;

                                                                                                                                            while (*expression != '\0' && *expression != '*' && *expression != '/') {
                                                                                                                                                if (*expression == '-') {
                                                                                    // Handle subtraction
                                                                                    char* operator = malloc(3);
                                                                                    strcpy(operator, "-");
                                                                                    ++expression;
                                                                                    result -= evaluator(expression);
                                                                                    --expression;
                                                                                    strcpy(operator + 2, ")");
                                                                                    expression += strlen(operator) - 1;

                                                                                    while (*expression != '\0' && *expression != '-' && *expression != '+') {
                                                                                        if (*expression == '*') {
                                                                                            // Handle multiplication
                                                                                            char* operator = malloc(3);
                                                                                            strcpy(operator, "*");
                                                                                            ++expression;