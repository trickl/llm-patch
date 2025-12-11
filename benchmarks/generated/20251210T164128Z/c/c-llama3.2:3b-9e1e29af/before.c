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
    END
} TokenType;

// Token structure
typedef struct {
    TokenType type;
    double value;
    char* str;
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    int len = strlen(expression);
    Token* tokens = malloc((len + 1) * sizeof(Token));
    for (int i = 0; i < len; ++i) {
        if (isdigit(expression[i])) {
            int j = i;
            while (j < len && isdigit(expression[j]))
                ++j;
            tokens[i].type = NUMBER;
            tokens[i].value = atof(expression + i);
            tokens[i].str = malloc((j - i + 1) * sizeof(char));
            strcpy(tokens[i].str, expression + i);
        } else if (expression[i] == '+') {
            int j = i + 1;
            while (j < len && expression[j] != ' ') ++j;
            tokens[i].type = PLUS;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "+");
        } else if (expression[i] == '-') {
            int j = i + 1;
            while (j < len && expression[j] != ' ') ++j;
            tokens[i].type = MINUS;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "-");
        } else if (expression[i] == '*') {
            int j = i + 1;
            while (j < len && expression[j] != ' ') ++j;
            tokens[i].type = MUL;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "*");
        } else if (expression[i] == '/') {
            int j = i + 1;
            while (j < len && expression[j] != ' ') ++j;
            tokens[i].type = DIV;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "/");
        } else if (expression[i] == '(') {
            int j = i + 1;
            while (j < len && expression[j] != ')') ++j;
            tokens[i].type = LPAREN;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "(");
        } else if (expression[i] == ')') {
            int j = i + 1;
            while (j < len && expression[j] != ' ') ++j;
            tokens[i].type = RPAREN;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, ")");
        } else if (expression[i] == '-') {
            int j = i + 1;
            while (j < len && expression[j] != ' ') ++j;
            tokens[i].type = UMINUS;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "-");
        } else {
            int j = i + 1;
            while (j < len && expression[j] != ' ') ++j;
            tokens[i].type = END;
            tokens[i].value = 0.0;
            tokens[i].str = malloc((j - i) * sizeof(char));
            strcpy(tokens[i].str, "");
        }
    }
    return tokens;
}

// Parser function to parse the tokenized expression
void* parser(Token* tokens, int len) {
    int precedence = 0;
    void* output = NULL;

    for (int i = 0; i < len; ++i) {
        if (tokens[i].type == NUMBER) {
            double value = tokens[i].value;
            if (output != NULL)
                output = malloc(sizeof(double));
            (*output) = value;
        } else if (tokens[i].type == PLUS || tokens[i].type == MINUS ||
                   tokens[i].type == MUL || tokens[i].type == DIV) {
            double value = 0.0;
            if (i > 0 && tokens[i - 1].type == UMINUS)
                value = -tokens[i - 1].value;
            else
                value = tokens[i].value;

            if (output != NULL)
                output = malloc(sizeof(double));
            (*output) = value;
        } else if (tokens[i].type == LPAREN) {
            void* temp = parser(tokens, i + 1);
            if (temp != NULL)
                output = malloc(sizeof(void*));
            (*output) = temp;
        } else if (tokens[i].type == RPAREN) {
            break;
        }
    }

    return output;
}

// Evaluator function to evaluate the parsed expression
double evaluator(void* expression) {
    double result = 0.0;

    for (int i = 0; i < 10; ++i) {
        if (((double*)expression)[i] == '+')
            result += ((double)((char*)((void*)expression))[i + 1]);
        else if (((double*)expression)[i] == '-')
            result -= ((double)((char*)((void*)expression))[i + 1]);
        else if (((double*)expression)[i] == '*')
            result *= ((double)((char*)((void*)expression))[i + 1]);
        else if (((double*)expression)[i] == '/')
            result /= ((double)((char*)((void*)expression))[i + 1]);
    }

    return result;
}

int main() {
    const char* expressions[] = {"3 + 4 * (2 - 1)", "2 * 3 + 4", "2 * (3 + 4)", "8 / 2 * (2 + 2)"};
    int len = sizeof(expressions) / sizeof(expressions[0]);

    for (int i = 0; i < len; ++i) {
        Token* tokens = lexer(expressions[i]);
        void* parsed_expression = parser(tokens, strlen(expressions[i]));
        double result = evaluator(parsed_expression);
        printf("%s => %f\n", expressions[i], result);

        free(tokens->str);
        for (int j = 0; j < len; ++j) {
            free(tokens[j].str);
        }
        free(tokens);
    }

    return 0;
}