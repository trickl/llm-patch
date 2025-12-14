#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define MAX_TOKEN_LENGTH 1024

typedef enum {
    TOKEN_TYPE_NUMBER,
    TOKEN_TYPE_OPERATOR,
    TOKEN_TYPE_LPAREN,
    TOKEN_TYPE_RPAREN,
    TOKEN_TYPE_EOF
} TokenType;

typedef struct {
    TokenType type;
    char value[MAX_TOKEN_LENGTH];
} Token;

typedef struct {
    int top;
    double stack[1024];
} Stack;

void init_stack(Stack *stack) {
    stack->top = -1;
}

int is_empty(Stack *stack) {
    return stack->top == -1;
}

double pop(Stack *stack) {
    if (is_empty(stack)) {
        fprintf(stderr, "Error: stack underflow\n");
        exit(EXIT_FAILURE);
    }
    return stack->stack[stack->top--];
}

void push(Stack *stack, double value) {
    if (stack->top >= 1023) {
        fprintf(stderr, "Error: stack overflow\n");
        exit(EXIT_FAILURE);
    }
    stack->stack[++stack->top] = value;
}

int precedence(char op) {
    switch (op) {
        case '+':
        case '-':
            return 1;
        case '*':
        case '/':
            return 2;
        default:
            return -1;
    }
}

double apply_operator(double a, double b, char op) {
    switch (op) {
        case '+':
            return a + b;
        case '-':
            return a - b;
        case '*':
            return a * b;
        case '/':
            if (b == 0) {
                fprintf(stderr, "Error: division by zero\n");
                exit(EXIT_FAILURE);
            }
            return a / b;
        default:
            fprintf(stderr, "Error: unknown operator\n");
            exit(EXIT_FAILURE);
    }
}

Token get_next_token(char **expression) {
    Token token = {TOKEN_TYPE_EOF, ""};
    while (**expression && isspace(**expression)) (*expression)++;
    if (!**expression) return token;

    switch (**expression) {
        case '+':
        case '-':
        case '*':
        case '/':
            token.type = TOKEN_TYPE_OPERATOR;
            token.value[0] = **expression;
            token.value[1] = '\0';
            (*expression)++;
            break;
        case '(':
            token.type = TOKEN_TYPE_LPAREN;
            (*expression)++;
            break;
        case ')':
            token.type = TOKEN_TYPE_RPAREN;
            (*expression)++;
            break;
        default:
            if (isdigit(**expression) || (**expression == '-' && isdigit((*expression)[1]))) {
                int i = 0;
                while (**expression && (isdigit(**expression) || **expression == '.')) {
                    token.value[i++] = **expression;
                    (*expression)++;
                }
                token.value[i] = '\0';
                token.type = TOKEN_TYPE_NUMBER;
            } else {
                fprintf(stderr, "Error: unknown character\n");
                exit(EXIT_FAILURE);
            }
    }

    return token;
}

double evaluate_expression(char *expression) {
    Stack values_stack, operators_stack;
    init_stack(&values_stack);
    init_stack(&operators_stack);

    Token current_token = get_next_token(&expression);
    while (current_token.type != TOKEN_TYPE_EOF) {
        switch (current_token.type) {
            case TOKEN_TYPE_NUMBER:
                push(&values_stack, atof(current_token.value));
                break;
            case TOKEN_TYPE_OPERATOR:
                while (!is_empty(&operators_stack) && precedence(peek(&operators_stack)) >= precedence(current_token.value[0])) {
                    double b = pop(&values_stack);
                    double a = pop(&values_stack);
                    char op = peek(&operators_stack); // Corrected to use peek
                    push(&values_stack, apply_operator(a, b, op));
                }
                push(&operators_stack, current_token.value[0]);
                break;
            case TOKEN_TYPE_LPAREN:
                push(&operators_stack, '(');
                break;
            case TOKEN_TYPE_RPAREN:
                while (!is_empty(&operators_stack) && peek(&operators_stack) != '(') {
                    double b = pop(&values_stack);
                    double a = pop(&values_stack);
                    char op = pop(&operators_stack);
                    push(&values_stack, apply_operator(a, b, op));
                }
                if (peek(&operators_stack) == '(') {
                    pop(&operators_stack);
                } else {
                    fprintf(stderr, "Error: unmatched parentheses\n");
                    exit(EXIT_FAILURE);
                }
                break;
        }
        current_token = get_next_token(&expression);
    }

    while (!is_empty(&operators_stack)) {
        double b = pop(&values_stack);
        double a = pop(&values_stack);
        char op = pop(&operators_stack);
        push(&values_stack, apply_operator(a, b, op));
    }

    return pop(&values_stack);
}

int main() {
    printf("%d\n", (int)evaluate_expression("1 + 2")); // Output: 3
    printf("%d\n", (int)evaluate_expression("2 * 3 + 4")); // Output: 10
    printf("%d\n", (int)evaluate_expression("2 * (3 + 4)")); // Output: 14
    printf("%d\n", (int)evaluate_expression("8 / 2 * (2 + 2)")); // Output: 16
    return 0;
}