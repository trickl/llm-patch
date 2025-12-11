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
} Token;

// Lexer function to tokenize the input string
Token* lexer(char* expression) {
    int length = strlen(expression);
    Token* tokens = malloc((length + 1) * sizeof(Token));
    char* token = strtok(expression, "+-*/() ");
    int index = 0;
    while (token != NULL && index < length) {
        if (strcmp(token, "+") == 0 || strcmp(token, "-") == 0 ||
            strcmp(token, "*") == 0 || strcmp(token, "/") == 0) {
            tokens[index].type = get_token_type(token);
            tokens[index].value = token[0] == '-' ? -1.0 : 1.0;
            index++;
        } else if (token[0] >= '0' && token[0] <= '9') {
            double value = atof(token);
            tokens[index].type = NUMBER;
            tokens[index].value = value;
            index++;
        } else if (token[0] == '(') {
            tokens[index].type = LPAREN;
            index++;
        } else if (token[0] == ')') {
            tokens[index].type = RPAREN;
            index++;
        }
        token = strtok(NULL, "+-*/() ");
    }
    return tokens;
}

// Parser function to parse the tokens
void* parser(Token* tokens) {
    int length = 0;
    for (int i = 0; i < strlen(tokens[0].value); i++) {
        if (tokens[i].type == LPAREN) {
            length++;
        } else if (tokens[i].type == RPAREN) {
            length--;
        }
    }

    // Allocate memory for the abstract syntax tree
    void* ast = malloc((length + 1) * sizeof(void*));

    // Parse the tokens into an abstract syntax tree
    int index = 0;
    while (index < length) {
        if (tokens[index].type == LPAREN) {
            ast[index] = parser(tokens + index + 1);
            index++;
        } else if (tokens[index].type == RPAREN) {
            break;
        } else if (tokens[index].type == NUMBER || tokens[index].type == PLUS ||
                   tokens[index].type == MINUS || tokens[index].type == MUL ||
                   tokens[index].type == DIV) {
            ast[index] = NULL; // Leaf node
            index++;
        }
    }

    return ast;
}

// Evaluator function to evaluate the abstract syntax tree
double evaluator(void* ast) {
    if (ast == NULL) {
        return 0.0;
    } else if (ast == LPAREN) {
        return evaluator(ast);
    } else if (ast == NUMBER) {
        return *(double*)ast;
    } else if (ast == PLUS || ast == MINUS ||
               ast == MUL || ast == DIV) {
        double left = evaluator((void*)((char*)ast + 1));
        double right = evaluator((void*)((char*)ast + 2));
        switch ((TokenType)ast) {
            case PLUS:
                return left + right;
            case MINUS:
                return left - right;
            case MUL:
                return left * right;
            case DIV:
                if (right == 0.0) {
                    printf("Error: Division by zero\n");
                    exit(1);
                }
                return left / right;
        }
    }
}

int main() {
    char expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    for (int i = 0; i < sizeof(expressions) / strlen(expressions); i++) {
        Token* tokens = lexer(expressions[i]);
        void* ast = parser(tokens);
        double result = evaluator(ast);
        printf("%s => %f\n", expressions[i], result);
        free(tokens);
        free(ast);
    }
    return 0;
}