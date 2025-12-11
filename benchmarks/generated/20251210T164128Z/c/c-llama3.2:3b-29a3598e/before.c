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
    for (int i = 0; i < len; i++) {
        if (isdigit(expression[i])) {
            char* start = &expression[i];
            while (i < len && isdigit(expression[i])) {
                i++;
            }
            tokens[i].type = NUMBER;
            tokens[i].value = atof(start);
            tokens[i].str = strdup(start);
        } else if (expression[i] == '+') {
            tokens[i].type = PLUS;
            tokens[i].value = 0.0;
            tokens[i].str = "";
        } else if (expression[i] == '-') {
            tokens[i].type = MINUS;
            tokens[i].value = 0.0;
            tokens[i].str = "";
        } else if (expression[i] == '*') {
            tokens[i].type = MUL;
            tokens[i].value = 0.0;
            tokens[i].str = "";
        } else if (expression[i] == '/') {
            tokens[i].type = DIV;
            tokens[i].value = 0.0;
            tokens[i].str = "";
        } else if (expression[i] == '(') {
            tokens[i].type = LPAREN;
            tokens[i].value = 0.0;
            tokens[i].str = "";
        } else if (expression[i] == ')') {
            tokens[i].type = RPAREN;
            tokens[i].value = 0.0;
            tokens[i].str = "";
        }
    }
    tokens[len].type = EOF;
    tokens[len].value = 0.0;
    tokens[len].str = NULL;

    return tokens;
}

// Parser function
Token* parse(Token* tokens) {
    Token* stack = malloc((tokens[0].len + 1) * sizeof(Token));
    int top = -1;
    for (int i = 0; i < tokens[0].len; i++) {
        if (tokens[i].type == LPAREN) {
            stack[++top] = tokens[i];
        } else if (tokens[i].type == RPAREN) {
            while (stack[top].type != LPAREN) {
                Token* token = stack[top--].str ? malloc(strlen(stack[top].str) + 1) : NULL;
                strcpy(token, stack[top].str);
                stack[top--].value = evaluate(token);
                free(token);
            }
            top--;
        } else if (tokens[i].type == EOF) {
            break;
        } else {
            Token* token = malloc(strlen(tokens[i].str) + 1);
            strcpy(token, tokens[i].str);
            while (top >= 0 && getPrecedence(stack[top].type) >= getPrecedence(tokens[i].type)) {
                Token* temp = stack[top--].value;
                if (stack[top].type == MUL || stack[top].type == DIV) {
                    token->value = divide(token->value, temp);
                } else if (stack[top].type == PLUS || stack[top].type == MINUS) {
                    token->value = add(token->value, temp);
                }
            }
            stack[++top] = *token;
        }
    }

    while (top >= 0) {
        Token* temp = stack[top--].value;
        if (stack[top].type == MUL || stack[top].type == DIV) {
            token->value = divide(token->value, temp);
        } else if (stack[top].type == PLUS || stack[top].type == MINUS) {
            token->value = add(token->value, temp);
        }
    }

    return stack[0];
}

// Evaluator function
double evaluate(Token* token) {
    if (token->type == NUMBER) {
        return token->value;
    } else if (token->type == PLUS || token->type == MINUS) {
        return add(evaluate(token), 0.0);
    } else if (token->type == MUL || token->type == DIV) {
        return divide(evaluate(token), 1.0);
    }
}

// Helper functions
double add(double a, double b) {
    return a + b;
}

double subtract(double a, double b) {
    return a - b;
}

double multiply(double a, double b) {
    return a * b;
}

double divide(double a, double b) {
    if (b == 0.0) {
        printf("Error: Division by zero\n");
        exit(1);
    }
    return a / b;
}

int getPrecedence(TokenType type) {
    switch (type) {
        case PLUS:
        case MINUS:
            return 1;
        case MUL:
        case DIV:
            return 2;
        default:
            return 0;
    }
}

// Main function
int main() {
    char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (int i = 0; i < sizeof(expressions) / sizeof(expressions[0]); i++) {
        Token* tokens = lexer(expressions[i]);
        Token* parsed = parse(tokens);
        double result = evaluate(parsed);
        printf("%s => %f\n", expressions[i], result);
        free(tokens);
    }
    return 0;
}