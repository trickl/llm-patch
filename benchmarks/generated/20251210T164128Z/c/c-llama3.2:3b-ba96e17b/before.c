#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Token type enumeration
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
    double value; // for numbers and operators
    char* str; // for strings (not used in this implementation)
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    int tokenIndex = 0;
    double currentValue = 0.0;

    for (int i = 0; i < length; ++i) {
        char c = expression[i];
        if (isdigit(c)) {
            // Parse a number
            while (i < length && isdigit(expression[i])) {
                currentValue = currentValue * 10 + (expression[i++] - '0');
            }
            tokens[tokenIndex].type = NUMBER;
            tokens[tokenIndex].value = currentValue;
            tokenIndex++;
        } else if (c == '+' || c == '-' || c == '*' || c == '/') {
            // Parse an operator
            tokens[tokenIndex].type = c == '+' ? PLUS : c == '-' ? MINUS : c == '*' ? MUL : DIV;
            tokens[tokenIndex].value = c == '+' ? 1.0 : c == '-' ? -1.0 : c == '*' ? 1.0 : 2.0;
            tokenIndex++;
        } else if (c == '(') {
            // Parse a left parenthesis
            tokens[tokenIndex].type = LPAREN;
            tokenIndex++;
        } else if (c == ')') {
            // Parse a right parenthesis
            tokens[tokenIndex].type = RPAREN;
            tokenIndex++;
        } else if (c == '-') {
            // Parse a unary minus operator
            tokens[tokenIndex].type = UNARY_MINUS;
            tokenIndex++;
        }
    }

    // Add the end of expression token
    tokens[tokenIndex].type = END_OF_EXPRESSION;

    return tokens;
}

// Parser function to parse the tokens into an abstract syntax tree (AST)
Token* parser(Token* tokens) {
    Token* ast = malloc(sizeof(Token));
    int index = 0;

    while (tokens[index].type != END_OF_EXPRESSION && tokens[index].type != LPAREN) {
        if (tokens[index].type == NUMBER) {
            // Parse a number
            ast->value = tokens[index].value;
            ast->type = NUMBER;
        } else if (tokens[index].type == PLUS || tokens[index].type == MINUS ||
                   tokens[index].type == MUL || tokens[index].type == DIV) {
            // Parse an operator
            Token* operand2 = parser(tokens + index + 1);
            Token* operand1 = parser(tokens + index + 1);

            if (tokens[index].type == PLUS) {
                ast->value = operand1->value + operand2->value;
                ast->type = NUMBER;
            } else if (tokens[index].type == MINUS) {
                ast->value = operand1->value - operand2->value;
                ast->type = NUMBER;
            } else if (tokens[index].type == MUL) {
                ast->value = operand1->value * operand2->value;
                ast->type = NUMBER;
            } else if (tokens[index].type == DIV) {
                ast->value = operand1->value / operand2->value;
                ast->type = NUMBER;
            }

            free(operand2);
            free(operand1);
        } else if (tokens[index].type == LPAREN) {
            // Parse a left parenthesis
            Token* rightParenthesis = parser(tokens + index + 1);
            free(rightParenthesis);

            // Create an AST node for the expression inside the parentheses
            Token* expressionNode = malloc(sizeof(Token));
            expressionNode->value = ast->value;
            expressionNode->type = NUMBER;

            // Add the left parenthesis and right parenthesis to the AST
            Token* leftParenthesis = malloc(sizeof(Token));
            leftParenthesis->type = LPAREN;
            leftParenthesis->value = tokens[index].value;
            Token* rightParenthesis2 = malloc(sizeof(Token));
            rightParenthesis2->type = RPAREN;
            rightParenthesis2->value = tokens[index + 1].value;

            // Create the AST
            ast->left = expressionNode;
            ast->right = leftParenthesis;
            ast->right->right = rightParenthesis2;
        }

        index++;
    }

    return ast;
}

// Evaluator function to evaluate the abstract syntax tree (AST)
double evaluator(Token* ast) {
    if (ast->type == NUMBER) {
        return ast->value;
    } else if (ast->type == PLUS || ast->type == MINUS ||
               ast->type == MUL || ast->type == DIV) {
        Token* operand2 = parser(ast);
        Token* operand1 = parser(ast);

        if (ast->type == PLUS) {
            return operand1->value + operand2->value;
        } else if (ast->type == MINUS) {
            return operand1->value - operand2->value;
        } else if (ast->type == MUL) {
            return operand1->value * operand2->value;
        } else if (ast->type == DIV) {
            return operand1->value / operand2->value;
        }
    }

    // Handle unary minus
    Token* operand = parser(ast);
    return -operand->value;

    // Handle end of expression token
    free(operand);
}

// Main function to run the CLI
int main() {
    const char* expressions[] = {"1 + 2", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int numExpressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < numExpressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        Token* ast = parser(tokens);
        double result = evaluator(ast);

        printf("%s => %f\n", expressions[i], result);

        free(tokens);
        free(ast);
    }

    return 0;
}