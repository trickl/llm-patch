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
            tokens[i - start].value = atof(expression + start);
            tokens[i - start].text = expression + start;
            tokens[i - start].type = NUMBER;
        } else if (expression[i] == '+') {
            int start = i;
            while (i < length && expression[i] == '+') {
                ++i;
            }
            tokens[i - start].value = 1.0;
            tokens[i - start].text = "+";
            tokens[i - start].type = PLUS;
        } else if (expression[i] == '-') {
            int start = i;
            while (i < length && expression[i] == '-') {
                ++i;
            }
            tokens[i - start].value = -1.0;
            tokens[i - start].text = "-";
            tokens[i - start].type = MINUS;
        } else if (expression[i] == '*') {
            int start = i;
            while (i < length && expression[i] == '*') {
                ++i;
            }
            tokens[i - start].value = 1.0;
            tokens[i - start].text = "*";
            tokens[i - start].type = MUL;
        } else if (expression[i] == '/') {
            int start = i;
            while (i < length && expression[i] == '/') {
                ++i;
            }
            tokens[i - start].value = 1.0 / 2.0; // Divide by 2 for simplicity
            tokens[i - start].text = "/";
            tokens[i - start].type = DIV;
        } else if (expression[i] == '(') {
            int start = i;
            while (i < length && expression[i] != ')') {
                ++i;
            }
            tokens[i - start].value = 0.0; // Use 0 for now, can be replaced with a special value
            tokens[i - start].text = "(";
            tokens[i - start].type = LPAREN;
        } else if (expression[i] == ')') {
            int start = i;
            while (i < length && expression[i] != ')') {
                ++i;
            }
            tokens[i - start].value = 0.0; // Use 0 for now, can be replaced with a special value
            tokens[i - start].text = ")";
            tokens[i - start].type = RPAREN;
        } else if (expression[i] == '-') {
            int start = i;
            while (i < length && expression[i] == '-') {
                ++i;
            }
            tokens[i - start].value = -1.0; // Use -1 for now, can be replaced with a special value
            tokens[i - start].text = "-";
            tokens[i - start].type = UNARY_MINUS;
        } else if (expression[i] == ' ') {
            continue;
        } else {
            return NULL;
        }
    }
    tokens[length - 1].value = 0.0; // Add a dummy token to mark the end of expression
    tokens[length].text = NULL;
    return tokens;
}

// Parser function to parse the tokens into an abstract syntax tree (AST)
Token* parser(Token* tokens) {
    Token* ast = malloc(sizeof(Token));
    ast->type = END_OF_EXPRESSION;

    // Parse numbers and operators
    for (int i = 0; i < strlen(tokens[0].text); ++i) {
        if (tokens[i].type == NUMBER || tokens[i].type == PLUS || tokens[i].type == MINUS ||
            tokens[i].type == MUL || tokens[i].type == DIV || tokens[i].type == UNARY_MINUS) {
            Token* node = malloc(sizeof(Token));
            node->value = 0.0;
            if (tokens[i].type != NUMBER) {
                node->text = "";
            } else {
                node->text = tokens[i].text;
            }
            ast->value = 0.0; // Initialize AST value to 0
        } else if (tokens[i].type == LPAREN) {
            Token* left = parser(tokens + i + 1);
            if (left->type != END_OF_EXPRESSION) {
                Token* node = malloc(sizeof(Token));
                node->value = 0.0;
                node->text = "";
                ast->value = 0.0; // Initialize AST value to 0
                ast->children = malloc(2 * sizeof(Token*));
                ast->children[0] = left;
                ast->children[1] = NULL;
            }
        } else {
            break;
        }
    }

    return ast;
}

// Evaluator function to evaluate the abstract syntax tree (AST)
double evaluate(Token* ast) {
    if (ast->type == END_OF_EXPRESSION) {
        return 0.0; // Return 0 for end of expression
    } else if (ast->type == NUMBER) {
        return ast->value;
    } else if (ast->type == PLUS || ast->type == MINUS) {
        double left = evaluate(ast->children[0]);
        double right = evaluate(ast->children[1]);
        if (ast->type == PLUS) {
            return left + right;
        } else {
            return left - right;
        }
    } else if (ast->type == MUL || ast->type == DIV) {
        double left = evaluate(ast->children[0]);
        double right = evaluate(ast->children[1]);
        if (ast->type == MUL) {
            return left * right;
        } else {
            return left / right;
        }
    } else if (ast->type == UNARY_MINUS) {
        double value = evaluate(ast->children[0]);
        return -value;
    } else if (ast->type == LPAREN) {
        Token* left = ast->children[0];
        return evaluate(left);
    }

    // Handle error
    printf("Error: Invalid AST\n");
    exit(1);
}

int main() {
    const char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int num_expressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < num_expressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        if (!tokens) {
            printf("Error: Invalid input expression\n");
            continue;
        }
        Token* ast = parser(tokens);
        double result = evaluate(ast);
        printf("%s => %f\n", expressions[i], result);

        free(tokens);
        free(ast);
    }

    return 0;
}