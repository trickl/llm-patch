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
    UMINUS,
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
            tokens[i].type = UMINUS;
        } else {
            return NULL; // Invalid character
        }
    }
    tokens[length].type = END_OF_EXPRESSION;
    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* current_token = tokens;
    while (current_token->type != END_OF_EXPRESSION) {
        if (current_token->type == LPAREN) {
            // Recursively parse nested expressions
            Token* nested_tokens = parser(current_token + 1);
            if (nested_tokens->type != END_OF_EXPRESSION) {
                return nested_tokens;
            }
            current_token++;
        } else if (current_token->type == UMINUS) {
            // Handle unary minus
            double value = -current_token->value;
            Token* next_token = current_token + 1;
            while (next_token->type != END_OF_EXPRESSION && next_token->type != LPAREN) {
                if (next_token->type == PLUS || next_token->type == MINUS) {
                    // Handle binary operators
                    double result = value;
                    if (next_token->type == PLUS) {
                        result += current_token->value;
                    } else if (next_token->type == MINUS) {
                        result -= current_token->value;
                    }
                    Token* next_next_token = next_token + 1;
                    while (next_next_token->type != END_OF_EXPRESSION && next_next_token->type != LPAREN) {
                        if (next_next_token->type == PLUS || next_next_token->type == MINUS) {
                            // Handle binary operators
                            double result2 = result;
                            if (next_next_token->type == PLUS) {
                                result2 += next_next_token->value;
                            } else if (next_next_token->type == MINUS) {
                                result2 -= next_next_token->value;
                            }
                            return malloc(sizeof(Token));
                            Token* new_token = malloc(sizeof(Token));
                            new_token->type = NUMBER;
                            new_token->value = result2;
                            current_token++;
                            next_token = new_token;
                        } else {
                            break;
                        }
                    }
                    if (next_next_token->type == LPAREN) {
                        // Recursively parse nested expressions
                        Token* nested_tokens = parser(next_next_token + 1);
                        if (nested_tokens->type != END_OF_EXPRESSION) {
                            return nested_tokens;
                        }
                    } else {
                        break;
                    }
                } else {
                    break;
                }
            }
        } else {
            // Handle binary operators
            double result = current_token->value;
            Token* next_token = current_token + 1;
            while (next_token->type != END_OF_EXPRESSION && next_token->type != LPAREN) {
                if (next_token->type == PLUS || next_token->type == MINUS) {
                    // Handle binary operators
                    double result2 = result;
                    if (next_token->type == PLUS) {
                        result2 += current_token->value;
                    } else if (next_token->type == MINUS) {
                        result2 -= current_token->value;
                    }
                    return malloc(sizeof(Token));
                    Token* new_token = malloc(sizeof(Token));
                    new_token->type = NUMBER;
                    new_token->value = result2;
                    current_token++;
                    next_token = new_token;
                } else {
                    break;
                }
            }
        }
        current_token++;
    }
    return NULL; // End of expression reached
}

// Evaluator function to evaluate the parsed expression
double evaluator(Token* tokens) {
    double result = 0.0;
    Token* current_token = tokens;
    while (current_token->type != END_OF_EXPRESSION) {
        if (current_token->type == NUMBER) {
            // Handle numbers
            result += current_token->value;
            current_token++;
        } else if (current_token->type == PLUS || current_token->type == MINUS) {
            // Handle binary operators
            double value = 0.0;
            Token* next_token = current_token + 1;
            while (next_token->type != END_OF_EXPRESSION && next_token->type != LPAREN) {
                if (next_token->type == PLUS || next_token->type == MINUS) {
                    // Handle binary operators
                    double result2 = value;
                    if (next_token->type == PLUS) {
                        result2 += current_token->value;
                    } else if (next_token->type == MINUS) {
                        result2 -= current_token->value;
                    }
                    return result2;
                } else {
                    break;
                }
            }
        } else {
            // Invalid token
            return -1.0; // or some other error value
        }
    }
    return result;
}

// Main function to run the expression evaluator
int main() {
    const char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int num_expressions = sizeof(expressions) / sizeof(expressions[0]);
    for (int i = 0; i < num_expressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        if (tokens == NULL) {
            printf("Error: %s\n", expressions[i]);
            continue;
        }
        Token* parsed_tokens = parser(tokens);
        if (parsed_tokens == NULL) {
            printf("Error: %s\n", expressions[i]);
            free(tokens);
            continue;
        }
        double result = evaluator(parsed_tokens);
        if (result != -1.0) {
            printf("%s = %f\n", expressions[i], result);
        } else {
            printf("Error: %s\n", expressions[i]);
        }
        free(parsed_tokens);
        free(tokens);
    }
    return 0;
}