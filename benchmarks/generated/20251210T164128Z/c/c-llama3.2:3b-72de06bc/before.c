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
    Token tokens[length];
    int tokenIndex = 0;

    for (int i = 0; i < length; ++i) {
        if (isdigit(expression[i])) {
            double value = 0;
            while (i < length && isdigit(expression[i])) {
                value = value * 10 + expression[i++] - '0';
            }
            tokens[tokenIndex].type = NUMBER;
            tokens[tokenIndex].value = value;
            ++tokenIndex;
        } else if (expression[i] == '+') {
            tokens[tokenIndex].type = PLUS;
            ++tokenIndex;
        } else if (expression[i] == '-') {
            tokens[tokenIndex].type = MINUS;
            ++tokenIndex;
        } else if (expression[i] == '*') {
            tokens[tokenIndex].type = MUL;
            ++tokenIndex;
        } else if (expression[i] == '/') {
            tokens[tokenIndex].type = DIV;
            ++tokenIndex;
        } else if (expression[i] == '(') {
            tokens[tokenIndex].type = LPAREN;
            ++tokenIndex;
        } else if (expression[i] == ')') {
            tokens[tokenIndex].type = RPAREN;
            ++tokenIndex;
        } else if (expression[i] == '-') {
            tokens[tokenIndex].type = UNARY_MINUS;
            ++tokenIndex;
        }
    }

    // Pad with END_OF_EXPRESSION token
    Token endToken;
    endToken.type = END_OF_EXPRESSION;
    tokens[tokenIndex++] = endToken;

    return &tokens[0];
}

// Parser function to parse the tokens into an abstract syntax tree (AST)
void* parser(Token* tokens) {
    int length = 0;
    for (int i = 0; i < tokenIndex; ++i) {
        if (tokens[i].type == END_OF_EXPRESSION) {
            break;
        }
        length++;
    }

    // Create a new AST node
    void* astNode = malloc(sizeof(Node));
    Node* currentNode = (Node*)astNode;

    // Parse the tokens into an AST
    for (int i = 0; i < tokenIndex; ++i) {
        if (tokens[i].type == NUMBER) {
            currentNode->value = tokens[i].value;
            currentNode->left = NULL;
            currentNode->right = NULL;
        } else if (tokens[i].type == PLUS || tokens[i].type == MINUS) {
            Node* leftChild = currentNode;
            currentNode = malloc(sizeof(Node));
            currentNode->value = 0;
            currentNode->left = leftChild;
            currentNode->right = NULL;

            // Recursively parse the right child
            void* rightChild = parser(tokens + i + 1);
            currentNode->right = (Node*)rightChild;
        } else if (tokens[i].type == MUL || tokens[i].type == DIV) {
            Node* leftChild = currentNode;
            currentNode = malloc(sizeof(Node));
            currentNode->value = 0;
            currentNode->left = leftChild;
            currentNode->right = NULL;

            // Recursively parse the right child
            void* rightChild = parser(tokens + i + 1);
            currentNode->right = (Node*)rightChild;
        } else if (tokens[i].type == LPAREN) {
            Node* leftChild = currentNode;
            currentNode = malloc(sizeof(Node));
            currentNode->value = 0;
            currentNode->left = leftChild;
            currentNode->right = NULL;

            // Recursively parse the right child
            void* rightChild = parser(tokens + i + 1);
            currentNode->right = (Node*)rightChild;
        } else if (tokens[i].type == RPAREN) {
            currentNode->right = NULL;
        } else if (tokens[i].type == UNARY_MINUS) {
            Node* leftChild = currentNode;
            currentNode = malloc(sizeof(Node));
            currentNode->value = 0;
            currentNode->left = leftChild;
            currentNode->right = NULL;

            // Recursively parse the right child
            void* rightChild = parser(tokens + i + 1);
            currentNode->right = (Node*)rightChild;
        }
    }

    return astNode;
}

// Evaluator function to evaluate the AST
double evaluator(Node* node) {
    if (node->value != 0) {
        return node->value;
    } else {
        double leftValue = evaluator(node->left);
        double rightValue = evaluator(node->right);

        switch (node->value) {
            case '+':
                return leftValue + rightValue;
            case '-':
                return leftValue - rightValue;
            case '*':
                return leftValue * rightValue;
            case '/':
                if (rightValue == 0) {
                    printf("Error: Division by zero\n");
                    exit(1);
                }
                return leftValue / rightValue;
        }
    }
}

// Helper function to print the AST
void printAST(Node* node, int indentLevel) {
    for (int i = 0; i < indentLevel; ++i) {
        printf(" ");
    }

    if (node->value != 0) {
        printf("%f ", node->value);
    } else {
        printf("(");

        if (node->left == NULL && node->right == NULL) {
            return;
        }

        printAST(node->left, indentLevel + 1);
        printAST(node->right, indentLevel + 1);

        printf(")");
    }
}

int main() {
    const char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int numExpressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < numExpressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        void* astNode = parser(tokens);
        double result = evaluator(astNode);

        printf("Expression: %s\n", expressions[i]);
        printAST((Node*)astNode, 0);
        printf("Result: %f\n\n");
    }

    return 0;
}