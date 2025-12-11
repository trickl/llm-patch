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
    char* str;
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    for (int i = 0; i < length; ++i) {
        if (isdigit(expression[i])) {
            int j = i;
            while (j < length && isdigit(expression[j])) {
                ++j;
            }
            double value = atof(expression + i);
            tokens[i].type = NUMBER;
            tokens[i].value = value;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, expression + i);
        } else if (expression[i] == '+') {
            int j = i + 1;
            while (j < length && expression[j] != ' ') {
                ++j;
            }
            tokens[i].type = PLUS;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "+");
        } else if (expression[i] == '-') {
            int j = i + 1;
            while (j < length && expression[j] != ' ') {
                ++j;
            }
            tokens[i].type = MINUS;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "-");
        } else if (expression[i] == '*') {
            int j = i + 1;
            while (j < length && expression[j] != ' ') {
                ++j;
            }
            tokens[i].type = MUL;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "*");
        } else if (expression[i] == '/') {
            int j = i + 1;
            while (j < length && expression[j] != ' ') {
                ++j;
            }
            tokens[i].type = DIV;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "/");
        } else if (expression[i] == '(') {
            int j = i + 1;
            while (j < length && expression[j] != ')') {
                ++j;
            }
            tokens[i].type = LPAREN;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "(");
        } else if (expression[i] == ')') {
            int j = i + 1;
            while (j < length && expression[j] != ' ') {
                ++j;
            }
            tokens[i].type = RPAREN;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, ")");
        } else if (expression[i] == '-') {
            int j = i + 1;
            while (j < length && expression[j] != ' ') {
                ++j;
            }
            tokens[i].type = UNARY_MINUS;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "-");
        } else if (expression[i] == ' ') {
            continue;
        } else {
            return NULL;
        }
    }
    tokens[length].type = END_OF_EXPRESSION;
    tokens[length].value = 0.0;
    tokens[length].str = malloc(2 * sizeof(char));
    strcpy(tokens[length].str, "");
    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* current_token = tokens;
    while (current_token->type != END_OF_EXPRESSION) {
        if (current_token->type == NUMBER) {
            double value = current_token->value;
            ++current_token;
            if (current_token->type == PLUS || current_token->type == MINUS ||
                current_token->type == MUL || current_token->type == DIV) {
                Token* operand2 = parser(current_token);
                Token* operand1 = parser(current_token - 1);
                double result;
                switch (operand1->type) {
                    case PLUS:
                        result = operand1->value + operand2->value;
                        break;
                    case MINUS:
                        result = operand1->value - operand2->value;
                        break;
                    case MUL:
                        result = operand1->value * operand2->value;
                        break;
                    case DIV:
                        if (operand2->value == 0.0) {
                            return NULL;
                        }
                        result = operand1->value / operand2->value;
                        break;
                }
                Token* new_token = malloc(sizeof(Token));
                new_token->type = NUMBER;
                new_token->value = result;
                new_token->str = malloc(10 * sizeof(char));
                sprintf(new_token->str, "%f", result);
                return new_token;
            } else {
                ++current_token;
            }
        } else if (current_token->type == LPAREN) {
            Token* expression = parser(current_token + 1);
            if (expression == NULL) {
                free(current_token->str);
                free(current_token);
                return NULL;
            }
            ++current_token;
            if (current_token->type != RPAREN) {
                return NULL;
            }
            --current_token;
        } else if (current_token->type == UNARY_MINUS) {
            double value = -current_token->value;
            ++current_token;
            if (current_token->type == PLUS || current_token->type == MINUS ||
                current_token->type == MUL || current_token->type == DIV) {
                Token* operand2 = parser(current_token);
                Token* operand1 = parser(current_token - 1);
                double result;
                switch (operand1->type) {
                    case PLUS:
                        result = operand1->value + value;
                        break;
                    case MINUS:
                        result = operand1->value - value;
                        break;
                    case MUL:
                        result = operand1->value * value;
                        break;
                    case DIV:
                        if (operand2->value == 0.0) {
                            return NULL;
                        }
                        result = operand1->value / value;
                        break;
                }
                Token* new_token = malloc(sizeof(Token));
                new_token->type = NUMBER;
                new_token->value = result;
                new_token->str = malloc(10 * sizeof(char));
                sprintf(new_token->str, "%f", result);
                return new_token;
            } else {
                ++current_token;
            }
        } else {
            return NULL;
        }
    }
    free(current_token->str);
    free(current_token);
    return current_token - 1;
}

// Evaluator function to evaluate the parsed expression
double evaluator(Token* token) {
    if (token->type == NUMBER) {
        return token->value;
    } else {
        return evaluator(token + 1);
    }
}

int main() {
    const char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int num_expressions = sizeof(expressions) / sizeof(expressions[0]);
    for (int i = 0; i < num_expressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        if (tokens == NULL) {
            printf("Error: %s\n", expressions[i]);
            continue;
        }
        Token* parsed_expression = parser(tokens);
        double result = evaluator(parsed_expression);
        free(parsed_expression->str);
        free(parsed_expression);
        free(tokens->str);
        free(tokens);
        printf("%s => %f\n", expressions[i], result);
    }
    return 0;
}