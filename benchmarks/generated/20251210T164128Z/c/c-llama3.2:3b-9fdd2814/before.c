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
    UNARY_MINUS
} TokenType;

// Token structure
typedef struct {
    TokenType type;
    double value;
    char* str;
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
        } else if (expression[i] == '+') {
            tokens[i] = {PLUS, 0, "+"};
        } else if (expression[i] == '-') {
            tokens[i] = {MINUS, 0, "-"};
        } else if (expression[i] == '*') {
            tokens[i] = {MUL, 0, "*"};
        } else if (expression[i] == '/') {
            tokens[i] = {DIV, 0, "/"};
        } else if (expression[i] == '(') {
            tokens[i] = {LPAREN, 0, "("};
        } else if (expression[i] == ')') {
            tokens[i] = {RPAREN, 0, ")"};
        } else if (expression[i] == '-') {
            tokens[i] = {UNARY_MINUS, 0, "-"};
        }
    }
    tokens[length] = {NULL, 0, NULL}; // sentinel token
    return tokens;
}

// Parser function to parse the tokens and build an abstract syntax tree
void* parser(Token* tokens) {
    int length = 0;
    for (int i = 0; tokens[i].str != NULL; ++i) {
        if (tokens[i].type == LPAREN) {
            length = i + 1;
        }
    }

    // Create a stack to store the nodes
    void** nodeStack = malloc((length + 2) * sizeof(void*));

    // Push the root node onto the stack
    nodeStack[0] = NULL;

    for (int i = 0; tokens[i].str != NULL && i < length; ++i) {
        if (tokens[i].type == LPAREN) {
            nodeStack[++length] = malloc(sizeof(void*));
            *(void**)nodeStack[length] = parser(tokens + i + 1);
        } else if (tokens[i].type == RPAREN) {
            --length;
        } else if (tokens[i].type == NUMBER || tokens[i].type == PLUS ||
                   tokens[i].type == MINUS || tokens[i].type == MUL ||
                   tokens[i].type == DIV) {
            nodeStack[++length] = malloc(sizeof(void*));
            *(void**)nodeStack[length] = tokens + i;
        }
    }

    // Pop the nodes off the stack and build the abstract syntax tree
    void** currentNode = nodeStack[0];
    while (currentNode != NULL && *currentNode != NULL) {
        void* leftChild = *(void**)currentNode;
        if (*leftChild == NULL) {
            break;
        }
        void* rightChild = *(void**)++nodeStack[length - 1];
        if (*rightChild == NULL) {
            break;
        }

        // Create a new node and push it onto the stack
        void* newNode = malloc(sizeof(void*));
        *(void**)newNode = malloc(sizeof(Node));
        ((Node*)*newNode)->left = leftChild;
        ((Node*)*newNode)->right = rightChild;

        // Update the current node's children
        *currentNode = newNode;
        --length;
    }

    free(nodeStack);
    return NULL; // Return a void pointer to indicate success
}

// Evaluator function to evaluate the abstract syntax tree
double evaluator(void* root) {
    if (root == NULL) {
        return 0;
    } else if (*(void**)root == NULL) {
        double value = *(Token*)*(void**)root->left;
        if ((*(void**)root)->right != NULL) {
            Token* rightChild = *(Token*)*(void**)root->right;
            if (rightChild->type == PLUS || rightChild->type == MINUS ||
                rightChild->type == MUL || rightChild->type == DIV) {
                double result = value;
                if (rightChild->type == PLUS) {
                    result += evaluator(*(void**)rightChild);
                } else if (rightChild->type == MINUS) {
                    result -= evaluator(*(void**)rightChild);
                } else if (rightChild->type == MUL) {
                    result *= evaluator(*(void**)rightChild);
                } else if (rightChild->type == DIV) {
                    result /= evaluator(*(void**)rightChild);
                }
                return result;
            }
        }
    }

    // Handle unary minus
    double value = *(Token*)*(void**)root->left;
    if ((*(void**)root)->right != NULL && (*(void**)root)->right->type == UNARY_MINUS) {
        return -value;
    } else {
        return value;
    }
}

// Helper function to print the abstract syntax tree
void printTree(void* root, int indent) {
    if (root == NULL) {
        return;
    }

    for (int i = 0; i < indent; ++i) {
        printf(" ");
    }
    printf("(");
    if (*(void**)root != NULL) {
        printTree(*(void**)root->left, indent + 1);
        printTree(*(void**)root->right, indent + 1);
    }
    for (int i = 0; i < indent; ++i) {
        printf(" ");
    }
    printf(")");
}

// Main function to test the expression evaluator
int main() {
    const char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int numExpressions = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < numExpressions; ++i) {
        Token* tokens = lexer(expressions[i]);
        void* root = parser(tokens);
        double result = evaluator(root);
        free(tokens);

        printf("%s => %f\n", expressions[i], result);
        printTree(root, 0);
    }

    return 0;
}