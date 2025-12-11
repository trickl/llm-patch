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
            tokens[i - start] = {NUMBER, value, NULL};
        } else if (expression[i] == '+' || expression[i] == '-') {
            int start = i;
            while (i < length && (expression[i] == '+' || expression[i] == '-' || expression[i] == '(')) {
                ++i;
            }
            tokens[i - start] = {PLUS, 0, NULL};
        } else if (expression[i] == '*' || expression[i] == '/') {
            int start = i;
            while (i < length && (expression[i] == '*' || expression[i] == '/' || expression[i] == ')')) {
                ++i;
            }
            tokens[i - start] = {MUL, 0, NULL};
        } else if (expression[i] == '(') {
            int start = i;
            while (i < length && expression[i] != ')') {
                ++i;
            }
            tokens[i - start] = {LPAREN, 0, NULL};
        } else if (expression[i] == '-') {
            int start = i;
            while (i < length && expression[i] == '-') {
                ++i;
            }
            tokens[i - start] = {UMINUS, 0, NULL};
        } else if (expression[i] == ')') {
            int start = i;
            while (i < length && expression[i] != ')') {
                ++i;
            }
            tokens[i - start] = {RPAREN, 0, NULL};
        } else {
            int start = i;
            while (i < length && !isspace(expression[i])) {
                ++i;
            }
            char* text = malloc((i - start) + 1);
            strcpy(text, expression + start);
            tokens[i - start] = {END_OF_EXPRESSION, 0, text};
        }
    }
    tokens[length] = {END_OF_EXPRESSION, 0, NULL};
    return tokens;
}

// Parser function to parse the tokenized input
Token* parser(Token* tokens) {
    Token* current_token = tokens;
    while (current_token->type != END_OF_EXPRESSION) {
        if (current_token->type == NUMBER) {
            // Skip number tokens
            ++current_token;
        } else if (current_token->type == PLUS || current_token->type == MINUS) {
            // Check for operator precedence
            if (current_token->type == PLUS && current_token->next->type == MUL ||
                current_token->type == MINUS && current_token->next->type == MUL) {
                Token* next_token = current_token->next;
                double result = evaluate(current_token->value, next_token->value);
                free(next_token->text);
                free(next_token);
                current_token = tokens + current_token->index - 1;
            } else if (current_token->type == PLUS && current_token->next->type == DIV ||
                       current_token->type == MINUS && current_token->next->type == DIV) {
                Token* next_token = current_token->next;
                double result = evaluate(current_token->value, next_token->value);
                free(next_token->text);
                free(next_token);
                current_token = tokens + current_token->index - 1;
            } else if (current_token->type == PLUS || current_token->type == MINUS) {
                // Handle addition and subtraction
                Token* next_token = current_token->next;
                double result = evaluate(current_token->value, next_token->value);
                free(next_token->text);
                free(next_token);
                current_token = tokens + current_token->index - 1;
            } else if (current_token->type == LPAREN) {
                // Handle left parenthesis
                Token* inner_tokens = parser(tokens + current_token->index + 1);
                double result = evaluate(inner_tokens[0].value, 0);
                free(inner_tokens[0].text);
                free(inner_tokens);
                current_token = tokens + current_token->index - 1;
            } else if (current_token->type == UMINUS) {
                // Handle unary minus
                Token* next_token = current_token->next;
                double result = evaluate(-next_token->value, 0);
                free(next_token->text);
                free(next_token);
                current_token = tokens + current_token->index - 1;
            } else if (current_token->type == RPAREN) {
                // Handle right parenthesis
                Token* next_token = current_token->next;
                double result = evaluate(0, next_token->value);
                free(next_token->text);
                free(next_token);
                current_token = tokens + current_token->index - 1;
            } else if (current_token->type == END_OF_EXPRESSION) {
                // Handle end of expression
                break;
            }
        } else if (current_token->type == MUL || current_token->type == DIV) {
            // Check for operator precedence
            if (current_token->type == MUL && current_token->next->type == PLUS ||
                current_token->type == DIV && current_token->next->type == PLUS) {
                Token* next_token = current_token->next;
                double result = evaluate(current_token->value, next_token->value);
                free(next_token->text);
                free(next_token);
                current_token = tokens + current_token->index - 1;
            } else if (current_token->type == MUL && current_token->next->type == DIV ||
                       current_token->type == DIV && current_token->next->type == MUL) {
                Token* next_token = current_token->next;
                double result = evaluate(current_token->value, next_token->value);
                free(next_token->text);
                free(next_token);
                current_token = tokens + current_token->index - 1;
            } else if (current_token->type == MUL || current_token->type == DIV) {
                // Handle multiplication and division
                Token* next_token = current_token->next;
                double result = evaluate(current_token->value, next_token->value);
                free(next_token->text);
                free(next_token);
                current_token = tokens + current_token->index - 1;
            }
        } else if (current_token->type == LPAREN) {
            // Handle left parenthesis
            Token* inner_tokens = parser(tokens + current_token->index + 1);
            double result = evaluate(inner_tokens[0].value, 0);
            free(inner_tokens[0].text);
            free(inner_tokens);
            current_token = tokens + current_token->index - 1;
        } else if (current_token->type == UMINUS) {
            // Handle unary minus
            Token* next_token = current_token->next;
            double result = evaluate(-next_token->value, 0);
            free(next_token->text);
            free(next_token);
            current_token = tokens + current_token->index - 1;
        } else if (current_token->type == RPAREN) {
            // Handle right parenthesis
            Token* next_token = current_token->next;
            double result = evaluate(0, next_token->value);
            free(next_token->text);
            free(next_token);
            current_token = tokens + current_token->index - 1;
        } else if (current_token->type == END_OF_EXPRESSION) {
            // Handle end of expression
            break;
        }
    }
    return current_token;
}

// Evaluator function to evaluate the parsed token
double evaluate(double left, double right) {
    if (left == 0) {
        return -right;
    } else {
        return left * right;
    }
}

int main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (const char* expression : expressions) {
        Token* tokens = lexer(expression);
        Token* result_token = parser(tokens);
        double result = evaluate(result_token->value, 0);
        printf("%s = %f\n", expression, result);
        free(result_token->text);
        free(tokens);
    }
    return 0;
}