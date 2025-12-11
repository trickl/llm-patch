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
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    for (int i = 0; i < length; ++i) {
        if (isdigit(expression[i])) {
            double value = 0;
            while (i < length && isdigit(expression[i])) {
                value = value * 10 + expression[i++] - '0';
            }
            tokens[i].type = NUMBER;
            tokens[i].value = value;
        } else if (expression[i] == '+') {
            tokens[i].type = PLUS;
        } else if (expression[i] == '-') {
            tokens[i].type = MINUS;
        } else if (expression[i] == '*') {
            tokens[i].type = MUL;
        } else if (expression[i] == '/') {
            tokens[i].type = DIV;
        } else if (expression[i] == '(') {
            tokens[i].type = LPAREN;
        } else if (expression[i] == ')') {
            tokens[i].type = RPAREN;
        } else if (expression[i] == '-') {
            tokens[i].type = UNARY_MINUS;
        } else {
            return NULL; // Invalid character
        }
    }
    tokens[length].type = END_OF_EXPRESSION;
    tokens[length].value = 0;
    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* stack = malloc(1024 * sizeof(Token));
    int top = -1;

    while (tokens != NULL && tokens->type != END_OF_EXPRESSION) {
        if (tokens->type == LPAREN) {
            ++top;
            stack[top] = *tokens;
            tokens = tokens->next;
        } else if (tokens->type == RPAREN) {
            --top;
            if (top < 0) return NULL; // Unbalanced parentheses
            stack[top] = *tokens;
            tokens = tokens->next;
        } else if (tokens->type == NUMBER || tokens->type == UNARY_MINUS) {
            Token* new_token = malloc(sizeof(Token));
            new_token->type = tokens->type;
            new_token->value = tokens->value;
            new_token->next = stack[top];
            stack[top] = *new_token;
            tokens = tokens->next;
        } else if (tokens->type == PLUS || tokens->type == MINUS) {
            Token* new_token = malloc(sizeof(Token));
            new_token->type = tokens->type;
            new_token->value = 0;
            new_token->next = stack[top];
            stack[top] = *new_token;
            tokens = tokens->next;
        } else if (tokens->type == MUL || tokens->type == DIV) {
            Token* new_token = malloc(sizeof(Token));
            new_token->type = tokens->type;
            new_token->value = 0;
            new_token->next = stack[top];
            stack[top] = *new_token;
            tokens = tokens->next;
        }
    }

    if (top != -1) return NULL; // Unbalanced parentheses

    Token* result = malloc(sizeof(Token));
    result->type = NUMBER;
    result->value = 0;
    result->next = NULL;

    while (stack[top].type == NUMBER || stack[top].type == UNARY_MINUS) {
        double value = stack[top].value;
        if (stack[top].type == UNARY_MINUS) value = -value;
        Token* new_token = malloc(sizeof(Token));
        new_token->type = NUMBER;
        new_token->value = value;
        new_token->next = result;
        result = *new_token;
        top--;
    }

    return result;
}

// Evaluator function to evaluate the parsed expression
double evaluator(Token* token) {
    if (token->type == NUMBER) return token->value;

    double left_value = evaluator(token->next);
    double right_value = evaluator(token->next);

    switch (token->type) {
        case PLUS:
            return left_value + right_value;
        case MINUS:
            return left_value - right_value;
        case MUL:
            return left_value * right_value;
        case DIV:
            if (right_value == 0) return NAN; // Division by zero
            return left_value / right_value;
    }
}

int main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int num_expressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < num_expressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        if (tokens == NULL) {
            printf("Error: %s\n", expressions[i]);
            continue;
        }

        Token* result = parser(tokens);
        if (result == NULL) {
            printf("Error: %s\n", expressions[i]);
            free(tokens);
            continue;
        }

        double value = evaluator(result);
        printf("%s => %.2f\n", expressions[i], value);

        free(result);
        free(tokens);
    }

    return 0;
}