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
    UMINUS
} TokenType;

// Token structure
typedef struct {
    TokenType type;
    double value;
    char* str;
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    for (int i = 0; i < length; ++i) {
        switch (expression[i]) {
            case '0': case '1': case '2': case '3': case '4':
            case '5': case '6': case '7': case '8': case '9':
                tokens[i].type = NUMBER;
                if (!tokens[i].str) {
                    tokens[i].str = malloc(10 * sizeof(char));
                    sprintf(tokens[i].str, "%d", expression[i] - '0');
                }
                break;
            case '+': case '-': case '*': case '/':
                tokens[i].type = PLUS;
                if (!tokens[i].str) {
                    tokens[i].str = malloc(3 * sizeof(char));
                    sprintf(tokens[i].str, "%c", expression[i]);
                }
                break;
            case '(':
                tokens[i].type = LPAREN;
                if (!tokens[i].str) {
                    tokens[i].str = malloc(2 * sizeof(char));
                    sprintf(tokens[i].str, "(");
                }
                break;
            case ')':
                tokens[i].type = RPAREN;
                if (!tokens[i].str) {
                    tokens[i].str = malloc(2 * sizeof(char));
                    sprintf(tokens[i].str, ")");
                }
                break;
            case '-':
                tokens[i].type = UMINUS;
                if (!tokens[i].str) {
                    tokens[i].str = malloc(1 * sizeof(char));
                    tokens[i].str[0] = '-';
                }
                break;
        }
    }
    tokens[length].type = NUMBER;
    tokens[length].value = 0.0;
    tokens[length].str = NULL;

    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* output = malloc(sizeof(Token));
    output->type = NUMBER;
    output->value = 0.0;
    output->str = NULL;

    while (tokens[0].type != RPAREN) {
        if (tokens[0].type == LPAREN) {
            // Handle nested expressions
            Token* inner = parser(tokens + 1);
            Token* result = parser(tokens + 1);

            double value = inner->value;
            int operator = tokens[1].type;

            switch (operator) {
                case PLUS:
                    output->value += value;
                    break;
                case MINUS:
                    output->value -= value;
                    break;
                case MUL:
                    output->value *= value;
                    break;
                case DIV:
                    output->value /= value;
                    break;
            }

            free(inner);
        } else if (tokens[0].type == UMINUS) {
            // Handle unary minus
            Token* operand = parser(tokens + 1);

            double value = -operand->value;

            switch (tokens[1].type) {
                case PLUS:
                    output->value += value;
                    break;
                case MINUS:
                    output->value -= value;
                    break;
                case MUL:
                    output->value *= value;
                    break;
                case DIV:
                    output->value /= value;
                    break;
            }

            free(operand);
        } else {
            // Handle binary expressions
            Token* operand1 = parser(tokens + 1);
            Token* operator = tokens[0];
            Token* operand2 = parser(tokens + 2);

            double value;

            switch (operator->type) {
                case PLUS:
                    value = operand1->value + operand2->value;
                    break;
                case MINUS:
                    value = operand1->value - operand2->value;
                    break;
                case MUL:
                    value = operand1->value * operand2->value;
                    break;
                case DIV:
                    if (operand2->value == 0) {
                        // Handle division by zero
                        free(operand1);
                        free(operand2);
                        return NULL;
                    }
                    value = operand1->value / operand2->value;
                    break;
            }

            output->value = value;

            free(operand1);
            free(operator);
            free(operand2);
        }

        tokens++;
    }

    free(tokens);

    return output;
}

// Evaluator function to evaluate the parsed expression
double evaluator(Token* token) {
    if (token->type == NUMBER) {
        return token->value;
    } else {
        // Handle unknown operators
        printf("Unknown operator: %c\n", token->str[0]);
        exit(1);
    }
}

int main() {
    const char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int numExpressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < numExpressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        if (!tokens) {
            printf("Error: %s\n", expressions[i]);
            return 1;
        }
        Token* parsedToken = parser(tokens);
        double result = evaluator(parsedToken);
        free(parsedToken);
        free(tokens);

        printf("%s => %f\n", expressions[i], result);
    }

    return 0;
}