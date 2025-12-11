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
    char* literal;
} Token;

// Lexer function to tokenize the input string
Token* lexer(char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    for (int i = 0; i < length; ++i) {
        if (isdigit(expression[i])) {
            char* start = &expression[i];
            while (start - expression >= 0 && isdigit(*start)) {
                ++start;
            }
            tokens[i].type = NUMBER;
            tokens[i].value = atof(start - expression);
            tokens[i].literal = malloc((start - expression) * sizeof(char));
            strcpy(tokens[i].literal, start - expression);
        } else if (expression[i] == '+') {
            tokens[i].type = PLUS;
            tokens[i].value = 1.0;
            tokens[i].literal = malloc(2 * sizeof(char));
            strcpy(tokens[i].literal, "+");
        } else if (expression[i] == '-') {
            tokens[i].type = MINUS;
            tokens[i].value = -1.0;
            tokens[i].literal = malloc(2 * sizeof(char));
            strcpy(tokens[i].literal, "-");
        } else if (expression[i] == '*') {
            tokens[i].type = MUL;
            tokens[i].value = 1.0;
            tokens[i].literal = malloc(2 * sizeof(char));
            strcpy(tokens[i].literal, "*");
        } else if (expression[i] == '/') {
            tokens[i].type = DIV;
            tokens[i].value = 1.0;
            tokens[i].literal = malloc(2 * sizeof(char));
            strcpy(tokens[i].literal, "/");
        } else if (expression[i] == '(') {
            tokens[i].type = LPAREN;
            tokens[i].value = 0.0;
            tokens[i].literal = malloc(1 * sizeof(char));
            strcpy(tokens[i].literal, "(");
        } else if (expression[i] == ')') {
            tokens[i].type = RPAREN;
            tokens[i].value = 0.0;
            tokens[i].literal = malloc(1 * sizeof(char));
            strcpy(tokens[i].literal, ")");
        } else if (expression[i] == '-') {
            tokens[i].type = UNARY_MINUS;
            tokens[i].value = -1.0;
            tokens[i].literal = malloc(2 * sizeof(char));
            strcpy(tokens[i].literal, "-");
        }
    }
    tokens[length].type = END_OF_EXPRESSION;
    return tokens;
}

// Parser function to parse the tokenized expression
double* parser(Token* tokens) {
    double* stack = malloc((tokens[0].type == LPAREN ? 1 : 0) * sizeof(double));
    int top = 0;
    for (int i = 0; i < tokens.length; ++i) {
        if (tokens[i].type != END_OF_EXPRESSION && tokens[i].type != LPAREN) {
            double value = stack[top--];
            switch (tokens[i].type) {
                case PLUS:
                    stack[++top] = value + tokens[i].value;
                    break;
                case MINUS:
                    stack[++top] = value - tokens[i].value;
                    break;
                case MUL:
                    stack[++top] = value * tokens[i].value;
                    break;
                case DIV:
                    if (tokens[i].value == 0.0) {
                        printf("Error: Division by zero\n");
                        exit(1);
                    }
                    stack[++top] = value / tokens[i].value;
                    break;
            }
        } else if (tokens[i].type == LPAREN) {
            double* substack = parser(tokens + i + 1);
            for (int j = top; j >= 0; --j) {
                stack[j] = substack[--top];
            }
        } else if (tokens[i].type == RPAREN) {
            break;
        } else if (tokens[i].type == UNARY_MINUS) {
            double value = stack[top--];
            switch (tokens[i].value) {
                case -1.0:
                    stack[++top] = -value;
                    break;
            }
        }
    }
    return stack + top;
}

// Evaluator function to evaluate the parsed expression
double evaluator(double* stack, int length) {
    double result = stack[0];
    for (int i = 1; i < length; ++i) {
        switch (stack[i].type) {
            case PLUS:
                result += stack[i + 1];
                break;
            case MINUS:
                result -= stack[i + 1];
                break;
            case MUL:
                result *= stack[i + 1];
                break;
            case DIV:
                if (stack[i + 1] == 0.0) {
                    printf("Error: Division by zero\n");
                    exit(1);
                }
                result /= stack[i + 1];
                break;
        }
    }
    return result;
}

int main() {
    char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (char* expression : expressions) {
        Token* tokens = lexer(expression);
        double* stack = parser(tokens);
        printf("%s => %f\n", expression, evaluator(stack, strlen(stack)));
        free(stack);
        free(tokens->literal);
        for (int i = 0; i < tokens.length - 1; ++i) {
            free(tokens[i].literal);
        }
    }
    return 0;
}