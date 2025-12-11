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
    EOF
} TokenType;

// Token structure
typedef struct {
    TokenType type;
    double value;
    char* str;
} Token;

// Lexer function
Token* lexer(char* expression) {
    int len = strlen(expression);
    Token* tokens = malloc((len + 1) * sizeof(Token));
    for (int i = 0; i < len; ++i) {
        if (isdigit(expression[i])) {
            char* start = &expression[i];
            while (start - expression >= 0 && isdigit(*start)) {
                ++start;
            }
            tokens[i].type = NUMBER;
            tokens[i].value = atof(start);
            tokens[i].str = malloc((start - expression) * sizeof(char));
            strcpy(tokens[i].str, expression + i);
        } else if (expression[i] == '+') {
            tokens[i].type = PLUS;
            tokens[i].str = &expression[i];
        } else if (expression[i] == '-') {
            tokens[i].type = MINUS;
            tokens[i].str = &expression[i];
        } else if (expression[i] == '*') {
            tokens[i].type = MUL;
            tokens[i].str = &expression[i];
        } else if (expression[i] == '/') {
            tokens[i].type = DIV;
            tokens[i].str = &expression[i];
        } else if (expression[i] == '(') {
            tokens[i].type = LPAREN;
            tokens[i].str = &expression[i];
        } else if (expression[i] == ')') {
            tokens[i].type = RPAREN;
            tokens[i].str = &expression[i];
        }
    }
    tokens[len].type = EOF;
    return tokens;
}

// Parser function
Token* parser(Token* tokens) {
    Token* stack = malloc(sizeof(Token));
    for (int i = 0; tokens[i].type != EOF; ++i) {
        if (tokens[i].type == LPAREN) {
            stack = realloc(stack, sizeof(Token) * (stacksize + 1));
            stack[stacksize++] = tokens[i];
        } else if (tokens[i].type == RPAREN) {
            --stacksize;
            while (stacksize > 0 && stack[stacksize - 1].type != LPAREN) {
                Token* temp = malloc(sizeof(Token));
                *temp = stack[--stacksize];
                Token* result = malloc(sizeof(Token));
                if (tokens[i].value == 0) {
                    result->type = MINUS;
                    result->str = &tokens[i].str[1];
                } else {
                    switch (tokens[i].value) {
                        case '+':
                            result->type = PLUS;
                            break;
                        case '*':
                            result->type = MUL;
                            break;
                        case '/':
                            result->type = DIV;
                            break;
                    }
                }
                if (result->str == NULL) {
                    free(temp);
                    continue;
                }
                temp->value = result->value;
                temp->str = malloc(strlen(result->str) + 1);
                strcpy(temp->str, result->str);
                result->str = temp->str;
                free(result);
            }
        } else if (tokens[i].type == NUMBER || tokens[i].type == PLUS || tokens[i].type == MINUS || tokens[i].type == MUL || tokens[i].type == DIV) {
            Token* temp = malloc(sizeof(Token));
            *temp = tokens[i];
            if (stacksize > 0 && stack[stacksize - 1].type != LPAREN) {
                Token* result = malloc(sizeof(Token));
                switch (tokens[i].value) {
                    case '+':
                        result->type = PLUS;
                        break;
                    case '-':
                        result->type = MINUS;
                        break;
                    case '*':
                        result->type = MUL;
                        break;
                    case '/':
                        result->type = DIV;
                        break;
                }
                temp->value = result->value;
                temp->str = malloc(strlen(result->str) + 1);
                strcpy(temp->str, result->str);
                free(result);
            }
            if (stacksize > 0 && stack[stacksize - 1].type == LPAREN) {
                Token* result = malloc(sizeof(Token));
                switch (tokens[i].value) {
                    case '+':
                        result->type = PLUS;
                        break;
                    case '-':
                        result->type = MINUS;
                        break;
                    case '*':
                        result->type = MUL;
                        break;
                    case '/':
                        result->type = DIV;
                        break;
                }
                temp->value = result->value;
                temp->str = malloc(strlen(result->str) + 1);
                strcpy(temp->str, result->str);
                free(result);
            }
        } else {
            continue;
        }
        stack = realloc(stack, sizeof(Token) * (stacksize + 1));
        stack[stacksize++] = tokens[i];
    }
    return stack;
}

// Evaluator function
double evaluate(Token* tokens) {
    Token* stack = malloc(sizeof(Token));
    for (int i = 0; tokens[i].type != EOF; ++i) {
        if (tokens[i].type == NUMBER || tokens[i].type == PLUS || tokens[i].type == MINUS || tokens[i].type == MUL || tokens[i].type == DIV) {
            Token* temp = malloc(sizeof(Token));
            *temp = tokens[i];
            if (stacksize > 0 && stack[stacksize - 1].type != LPAREN) {
                Token* result = malloc(sizeof(Token));
                switch (tokens[i].value) {
                    case '+':
                        result->type = PLUS;
                        break;
                    case '-':
                        result->type = MINUS;
                        break;
                    case '*':
                        result->type = MUL;
                        break;
                    case '/':
                        result->type = DIV;
                        break;
                }
                temp->value = result->value;
                temp->str = malloc(strlen(result->str) + 1);
                strcpy(temp->str, result->str);
                free(result);
            }
            if (stacksize > 0 && stack[stacksize - 1].type == LPAREN) {
                Token* result = malloc(sizeof(Token));
                switch (tokens[i].value) {
                    case '+':
                        result->type = PLUS;
                        break;
                    case '-':
                        result->type = MINUS;
                        break;
                    case '*':
                        result->type = MUL;
                        break;
                    case '/':
                        result->type = DIV;
                        break;
                }
                temp->value = result->value;
                temp->str = malloc(strlen(result->str) + 1);
                strcpy(temp->str, result->str);
                free(result);
            }
        } else if (tokens[i].type == LPAREN) {
            stacksize++;
            Token* temp = malloc(sizeof(Token));
            *temp = tokens[i];
            stack = realloc(stack, sizeof(Token) * (stacksize + 1));
            stack[stacksize++] = temp;
        } else if (tokens[i].type == RPAREN) {
            --stacksize;
            while (stacksize > 0 && stack[stacksize - 1].type != LPAREN) {
                Token* result = malloc(sizeof(Token));
                *result = stack[--stacksize];
                Token* temp = malloc(sizeof(Token));
                switch (tokens[i].value) {
                    case '+':
                        temp->type = PLUS;
                        break;
                    case '-':
                        temp->type = MINUS;
                        break;
                    case '*':
                        temp->type = MUL;
                        break;
                    case '/':
                        temp->type = DIV;
                        break;
                }
                result->value = temp->value;
                result->str = malloc(strlen(temp->str) + 1);
                strcpy(result->str, temp->str);
                free(temp);
            }
        } else {
            continue;
        }
    }
    double result = stack[stacksize - 1].value;
    for (int i = stacksize - 2; i >= 0; --i) {
        Token* temp = malloc(sizeof(Token));
        *temp = stack[i];
        switch (temp->type) {
            case PLUS:
                result += temp->value;
                break;
            case MINUS:
                result -= temp->value;
                break;
            case MUL:
                result *= temp->value;
                break;
            case DIV:
                result /= temp->value;
                break;
        }
    }
    free(stack);
    return result;
}

int main() {
    char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (char* expression : expressions) {
        Token* tokens = lexer(expression);
        Token* parsedTokens = parser(tokens);
        double result = evaluate(parsedTokens);
        printf("%s: %f\n", expression, result);
        free(tokens);
        free(parsedTokens);
    }
    return 0;
}