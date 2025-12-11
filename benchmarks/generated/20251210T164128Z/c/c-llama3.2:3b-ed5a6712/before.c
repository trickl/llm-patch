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
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    for (int i = 0; i < length; i++) {
        if (isdigit(expression[i])) {
            double value = 0;
            while (i < length && isdigit(expression[i])) {
                value = value * 10 + expression[i++] - '0';
            }
            tokens[i].type = NUMBER;
            tokens[i].value = value;
        } else if (expression[i] == '+' || expression[i] == '-') {
            tokens[i].type = PLUS;
            tokens[i].value = expression[i];
            i++;
        } else if (expression[i] == '*' || expression[i] == '/') {
            tokens[i].type = MUL;
            tokens[i].value = expression[i];
            i++;
        } else if (expression[i] == '(') {
            tokens[i].type = LPAREN;
            tokens[i].value = expression[i];
            i++;
        } else if (expression[i] == ')') {
            tokens[i].type = RPAREN;
            tokens[i].value = expression[i];
            i++;
        } else if (expression[i] == '-') {
            tokens[i].type = UNARY_MINUS;
            tokens[i].value = expression[i];
            i++;
        } else {
            return NULL; // invalid character
        }
    }
    tokens[length].type = END_OF_EXPRESSION;
    tokens[length].value = 0;
    return tokens;
}

// Parser function to parse the tokenized input into an abstract syntax tree (AST)
Token* parser(Token* tokens) {
    Token* current_token = tokens;
    while (current_token->type != END_OF_EXPRESSION) {
        if (current_token->type == LPAREN) {
            // Recursively parse the expression inside the parentheses
            Token* inner_expression = parser(current_token + 1);
            if (inner_expression == NULL) return NULL; // invalid syntax

            // Create a new node for the parsed expression and add it to the AST
            Token* new_node = malloc(sizeof(Token));
            new_node->type = NUMBER;
            new_node->value = inner_expression->value;
        } else if (current_token->type == UNARY_MINUS) {
            // Recursively parse the operand of the unary minus operation
            Token* operand = parser(current_token + 1);
            if (operand == NULL) return NULL; // invalid syntax

            // Create a new node for the parsed operand and add it to the AST
            Token* new_node = malloc(sizeof(Token));
            new_node->type = NUMBER;
            new_node->value = -operand->value;
        } else {
            // Find the next operator or operand in the token stream
            while (current_token->next != NULL && current_token->next->type != LPAREN &&
                   current_token->next->type != UNARY_MINUS) {
                if (current_token->next->type == PLUS || current_token->next->type == MINUS ||
                    current_token->next->type == MUL || current_token->next->type == DIV) {
                    // Create a new node for the operator and add it to the AST
                    Token* new_node = malloc(sizeof(Token));
                    new_node->type = current_token->next->type;
                    new_node->value = current_token->next->value;
                    break;
                }
            }

            if (current_token->next == NULL) return NULL; // invalid syntax

            // Create a new node for the operand and add it to the AST
            Token* new_node = malloc(sizeof(Token));
            new_node->type = NUMBER;
            new_node->value = current_token->next->value;
        }
        current_token = current_token->next;
    }
    return NULL; // end of expression reached
}

// Evaluator function to evaluate the abstract syntax tree (AST)
double evaluator(Token* ast) {
    if (ast == NULL) return 0.0;

    double value = ast->value;
    if (ast->type == NUMBER) return value;
    else if (ast->type == PLUS) {
        Token* operand = parser(ast.next);
        if (operand == NULL) return 0.0; // invalid syntax
        value += evaluator(operand);
        free(operand);
    } else if (ast->type == MINUS) {
        Token* operand = parser(ast.next);
        if (operand == NULL) return 0.0; // invalid syntax
        value -= evaluator(operand);
        free(operand);
    } else if (ast->type == MUL) {
        Token* operand = parser(ast.next);
        if (operand == NULL) return 0.0; // invalid syntax
        value *= evaluator(operand);
        free(operand);
    } else if (ast->type == DIV) {
        Token* operand = parser(ast.next);
        if (operand == NULL) return 0.0; // invalid syntax
        value /= evaluator(operand);
        free(operand);
    }

    return value;
}

int main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int num_expressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < num_expressions; i++) {
        Token* tokens = lexer(expressions[i]);
        if (tokens == NULL) return 1; // invalid input

        Token* ast = parser(tokens);
        if (ast == NULL) return 1; // invalid syntax

        double result = evaluator(ast);
        printf("%s => %f\n", expressions[i], result);

        free(ast);
    }

    return 0;
}