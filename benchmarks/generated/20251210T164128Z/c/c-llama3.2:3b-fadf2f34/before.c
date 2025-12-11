#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Token types
enum TokenType {
    NUMBER,
    PLUS,
    MINUS,
    MUL,
    DIV,
    LPAREN,
    RPAREN,
    UMINUS,
    END_OF_EXPRESSION
};

// Token structure
typedef struct {
    enum TokenType type;
    char* value;
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
            tokens[i - start] = {NUMBER, expression + start};
        } else if (expression[i] == '+' || expression[i] == '-' ||
                   expression[i] == '*' || expression[i] == '/') {
            int start = i;
            while (i < length && (expression[i] == '+' || expression[i] == '-' ||
                                  expression[i] == '*' || expression[i] == '/')) {
                ++i;
            }
            tokens[i - start] = {expression[i], &expression[start]};
        } else if (expression[i] == '(') {
            int start = i;
            while (i < length && expression[i] != ')') {
                ++i;
            }
            tokens[i - start] = {LPAREN, &expression[start]};
        } else if (expression[i] == ')') {
            int start = i;
            while (i < length && expression[i] != '(') {
                --i;
            }
            tokens[i - start + 1] = {RPAREN, &expression[start]};
        } else if (expression[i] == '-') {
            int start = i;
            while (i < length && expression[i] == '-') {
                ++i;
            }
            tokens[i - start] = {UMINUS, &expression[start]};
        } else {
            return NULL; // Invalid character
        }
    }
    tokens[length] = {END_OF_EXPRESSION, NULL};
    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* current_token = tokens;
    while (current_token->type != END_OF_EXPRESSION && current_token->value[0] != '\0') {
        if (current_token->type == NUMBER) {
            // Skip whitespace and operator tokens
            while (*current_token->value != '\0' && isspace(*current_token->value)) {
                ++current_token;
            }
            if (*current_token->value == '+') {
                Token* next_token = current_token + 1;
                while (next_token->type != END_OF_EXPRESSION &&
                       next_token->type != NUMBER) {
                    ++next_token;
                }
                // Apply operator
                int result = atoi(current_token->value);
                if (next_token->type == PLUS) {
                    result += atoi(next_token->value);
                } else if (next_token->type == MINUS) {
                    result -= atoi(next_token->value);
                } else if (next_token->type == MUL) {
                    result *= atoi(next_token->value);
                } else if (next_token->type == DIV) {
                    result /= atoi(next_token->value);
                }
                current_token = next_token;
            } else if (*current_token->value == '-') {
                Token* next_token = current_token + 1;
                while (next_token->type != END_OF_EXPRESSION &&
                       next_token->type != NUMBER) {
                    ++next_token;
                }
                // Apply operator
                int result = -atoi(current_token->value);
                if (next_token->type == PLUS) {
                    result += atoi(next_token->value);
                } else if (next_token->type == MINUS) {
                    result -= atoi(next_token->value);
                } else if (next_token->type == MUL) {
                    result *= atoi(next_token->value);
                } else if (next_token->type == DIV) {
                    result /= atoi(next_token->value);
                }
                current_token = next_token;
            }
        } else if (current_token->type == LPAREN) {
            // Recursively parse nested expression
            Token* nested_expression = parser(current_token + 1);
            if (nested_expression->type != END_OF_EXPRESSION) {
                // Apply operator
                int result = atoi(current_token->value);
                if (nested_expression->type == PLUS) {
                    result += atoi(nested_expression->value);
                } else if (nested_expression->type == MINUS) {
                    result -= atoi(nested_expression->value);
                } else if (nested_expression->type == MUL) {
                    result *= atoi(nested_expression->value);
                } else if (nested_expression->type == DIV) {
                    result /= atoi(nested_expression->value);
                }
                free(nested_expression->value);
                free(nested_expression);
            }
            current_token = nested_expression;
        } else if (current_token->type == RPAREN) {
            // Skip operator tokens
            while (*current_token->value != '\0' && isspace(*current_token->value)) {
                ++current_token;
            }
            break;
        }
    }
    return current_token;
}

// Evaluator function to evaluate the parsed expression
int evaluator(Token* token) {
    if (token->type == NUMBER) {
        return atoi(token->value);
    } else if (token->type == PLUS || token->type == MINUS ||
               token->type == MUL || token->type == DIV) {
        int result = 0;
        Token* current_token = token + 1;
        while (current_token->type != END_OF_EXPRESSION &&
               current_token->type != NUMBER) {
            ++current_token;
        }
        if (current_token->type == PLUS) {
            result += evaluator(current_token);
        } else if (current_token->type == MINUS) {
            result -= evaluator(current_token);
        } else if (current_token->type == MUL) {
            result *= evaluator(current_token);
        } else if (current_token->type == DIV) {
            result /= evaluator(current_token);
        }
        free(current_token->value);
        free(current_token);
        return result;
    } else {
        // Invalid token type
        return 0;
    }
}

int main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (const char* expression : expressions) {
        Token* tokens = lexer(expression);
        if (tokens == NULL) {
            printf("Error: %s\n", expression);
            continue;
        }
        Token* parsed_expression = parser(tokens);
        int result = evaluator(parsed_expression);
        free(parsed_expression->value);
        free(parsed_expression);
        printf("%s => %d\n", expression, result);
    }
    return 0;
}