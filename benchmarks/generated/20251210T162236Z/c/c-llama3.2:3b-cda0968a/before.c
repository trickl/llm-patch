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
    char* text;
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    for (int i = 0; i < length; ++i) {
        if (isdigit(expression[i])) {
            int start = i;
            while (i < length && isdigit(expression[i])) {
                ++i;
            }
            double value = atof(expression + start);
            Token* token = malloc(sizeof(Token));
            token->type = NUMBER;
            token->value = value;
            token->text = strdup(expression + start);
            tokens[(length - i) * 2] = *token;
        } else if (expression[i] == '+') {
            int start = i;
            while (i < length && expression[i] != ' ') {
                ++i;
            }
            Token* token = malloc(sizeof(Token));
            token->type = PLUS;
            token->value = 0.0;
            token->text = strdup(expression + start);
            tokens[(length - i) * 2 + 1] = *token;
        } else if (expression[i] == '-') {
            int start = i;
            while (i < length && expression[i] != ' ') {
                ++i;
            }
            Token* token = malloc(sizeof(Token));
            token->type = MINUS;
            token->value = 0.0;
            token->text = strdup(expression + start);
            tokens[(length - i) * 2 + 1] = *token;
        } else if (expression[i] == '*') {
            int start = i;
            while (i < length && expression[i] != ' ') {
                ++i;
            }
            Token* token = malloc(sizeof(Token));
            token->type = MUL;
            token->value = 0.0;
            token->text = strdup(expression + start);
            tokens[(length - i) * 2 + 1] = *token;
        } else if (expression[i] == '/') {
            int start = i;
            while (i < length && expression[i] != ' ') {
                ++i;
            }
            Token* token = malloc(sizeof(Token));
            token->type = DIV;
            token->value = 0.0;
            token->text = strdup(expression + start);
            tokens[(length - i) * 2 + 1] = *token;
        } else if (expression[i] == '(') {
            int start = i;
            while (i < length && expression[i] != ')') {
                ++i;
            }
            Token* token = malloc(sizeof(Token));
            token->type = LPAREN;
            token->value = 0.0;
            token->text = strdup(expression + start);
            tokens[(length - i) * 2 + 1] = *token;
        } else if (expression[i] == ')') {
            int start = i;
            while (i < length && expression[i] != ' ') {
                ++i;
            }
            Token* token = malloc(sizeof(Token));
            token->type = RPAREN;
            token->value = 0.0;
            token->text = strdup(expression + start);
            tokens[(length - i) * 2 + 1] = *token;
        } else {
            continue;
        }
    }
    tokens[length / 2] = {EOF, 0.0, NULL};
    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* current_token = &tokens[0];
    while (current_token->type != EOF) {
        if (current_token->type == LPAREN) {
            // Parse the subexpression inside the parentheses
            Token* subexpression = parser(tokens + 1);
            int i = 0;
            while (subexpression[i].type != RPAREN && i < strlen(subexpression[0].text)) {
                ++i;
            }
            tokens[(strlen(tokens) - i) * 2] = *subexpression + i;
        } else if (current_token->type == NUMBER || current_token->type == PLUS || current_token->type == MINUS || current_token->type == MUL || current_token->type == DIV) {
            // Parse the operand
            Token* operand = &tokens[0];
            while (operand->type != EOF && operand->type != current_token->type) {
                ++operand;
            }
            if (operand->type == current_token->type) {
                // Parse the operator and its operands
                int precedence = 0;
                if (current_token->type == PLUS || current_token->type == MINUS) {
                    precedence = 1;
                } else if (current_token->type == MUL || current_token->type == DIV) {
                    precedence = 2;
                }
                Token* operator = &tokens[0];
                while (operator->type != EOF && operator->type != current_token->type) {
                    ++operator;
                }
                if (operator->type == current_token->type) {
                    // Evaluate the expression
                    double result = evaluate(operator + 1, operand - 1);
                    tokens[(strlen(tokens) - i) * 2] = {current_token->type, result, NULL};
                    return &tokens[0];
                }
            } else if (operand->type == current_token->type) {
                // Evaluate the expression
                double result = evaluate(operand + 1, operator - 1);
                tokens[(strlen(tokens) - i) * 2] = {current_token->type, result, NULL};
                return &tokens[0];
            }
        } else if (current_token->type == EOF) {
            break;
        }
        ++current_token;
    }
    return &tokens[0];
}

// Evaluator function to evaluate the parsed expression
double evaluate(Token* tokens, int start_index) {
    double result = 0.0;
    for (int i = start_index; i < strlen(tokens[0].text); ++i) {
        if (tokens[i].type == NUMBER) {
            result += atof(tokens[i].text);
        } else if (tokens[i].type == PLUS || tokens[i].type == MINUS) {
            double operand = atof(tokens[i - 1].text);
            switch (tokens[i].type) {
                case PLUS:
                    result += operand;
                    break;
                case MINUS:
                    result -= operand;
                    break;
            }
        } else if (tokens[i].type == MUL || tokens[i].type == DIV) {
            double operand = atof(tokens[i - 1].text);
            switch (tokens[i].type) {
                case MUL:
                    result *= operand;
                    break;
                case DIV:
                    result /= operand;
                    break;
            }
        }
    }
    return result;
}

// Main function to run the CLI
int main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (const char* expression : expressions) {
        Token* tokens = lexer(expression);
        Token* parsed_expression = parser(tokens);
        double result = evaluate(parsed_expression, 0);
        printf("%s => %f\n", expression, result);
        free(tokens);
        free(parsed_expression);
    }
    return 0;
}