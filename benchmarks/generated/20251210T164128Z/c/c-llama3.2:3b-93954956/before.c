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
    char* str;
} Token;

// Lexer function to tokenize the input string
Token* lexer(const char* expression) {
    Token* tokens = malloc(100 * sizeof(Token));
    int tokenIndex = 0;
    const char* currentChar = expression;

    while (*currentChar != '\0') {
        if (isdigit(*currentChar)) {
            // Parse number
            double numValue = 0.0;
            while (isdigit(currentChar[1])) {
                numValue = numValue * 10 + (*currentChar - '0');
                currentChar++;
            }
            tokens[tokenIndex].type = NUMBER;
            tokens[tokenIndex].value = numValue;
            tokens[tokenIndex].str = malloc(20);
            sprintf(tokens[tokenIndex].str, "%lf", tokens[tokenIndex].value);
            tokenIndex++;

            // Skip whitespace
            while (*currentChar != '\0' && isspace(*currentChar)) {
                currentChar++;
            }
        } else if (*currentChar == '+') {
            // Parse plus operator
            tokens[tokenIndex].type = PLUS;
            tokens[tokenIndex].str = malloc(3);
            strcpy(tokens[tokenIndex].str, "+");
            tokenIndex++;

            // Skip whitespace
            while (*currentChar != '\0' && isspace(*currentChar)) {
                currentChar++;
            }
        } else if (*currentChar == '-') {
            // Parse minus operator
            tokens[tokenIndex].type = MINUS;
            tokens[tokenIndex].str = malloc(2);
            strcpy(tokens[tokenIndex].str, "-");
            tokenIndex++;

            // Skip whitespace
            while (*currentChar != '\0' && isspace(*currentChar)) {
                currentChar++;
            }
        } else if (*currentChar == '*') {
            // Parse multiplication operator
            tokens[tokenIndex].type = MUL;
            tokens[tokenIndex].str = malloc(2);
            strcpy(tokens[tokenIndex].str, "*");
            tokenIndex++;

            // Skip whitespace
            while (*currentChar != '\0' && isspace(*currentChar)) {
                currentChar++;
            }
        } else if (*currentChar == '/') {
            // Parse division operator
            tokens[tokenIndex].type = DIV;
            tokens[tokenIndex].str = malloc(2);
            strcpy(tokens[tokenIndex].str, "/");
            tokenIndex++;

            // Skip whitespace
            while (*currentChar != '\0' && isspace(*currentChar)) {
                currentChar++;
            }
        } else if (*currentChar == '(') {
            // Parse left parenthesis
            tokens[tokenIndex].type = LPAREN;
            tokenIndex++;

            // Skip whitespace
            while (*currentChar != '\0' && isspace(*currentChar)) {
                currentChar++;
            }
        } else if (*currentChar == ')') {
            // Parse right parenthesis
            tokens[tokenIndex].type = RPAREN;
            tokenIndex++;

            // Skip whitespace
            while (*currentChar != '\0' && isspace(*currentChar)) {
                currentChar++;
            }
        } else if (*currentChar == '-') {
            // Parse unary minus operator
            tokens[tokenIndex].type = UNARY_MINUS;
            tokens[tokenIndex].str = malloc(2);
            strcpy(tokens[tokenIndex].str, "-");
            tokenIndex++;

            // Skip whitespace
            while (*currentChar != '\0' && isspace(*currentChar)) {
                currentChar++;
            }
        } else if (*currentChar == '\n') {
            // End of expression
            tokens[tokenIndex].type = END_OF_EXPRESSION;
            break;
        } else {
            printf("Error: Invalid character '%c'\n", *currentChar);
            exit(1);
        }

        while (isspace(*currentChar)) {
            currentChar++;
        }
    }

    return tokens;
}

// Parser function to parse the tokenized expression
Token* parser(Token* tokens) {
    Token* outputTokens = malloc(100 * sizeof(Token));
    int outputTokenIndex = 0;

    // Parse numbers and operators
    while (tokens[tokenIndex].type != END_OF_EXPRESSION && tokens[tokenIndex].type != UNARY_MINUS) {
        if (tokens[tokenIndex].type == NUMBER) {
            outputTokens[outputTokenIndex].type = NUMBER;
            outputTokens[outputTokenIndex].value = tokens[tokenIndex].value;
            outputTokens[outputTokenIndex].str = malloc(20);
            sprintf(outputTokens[outputTokenIndex].str, "%lf", outputTokens[outputTokenIndex].value);
            outputTokenIndex++;

            // Skip whitespace
            while (tokens[tokenIndex].type == NUMBER && isspace(*(&tokens[tokenIndex].str + 1))) {
                tokenIndex++;
            }
        } else if (tokens[tokenIndex].type == PLUS || tokens[tokenIndex].type == MINUS) {
            outputTokens[outputTokenIndex].type = tokens[tokenIndex].type;
            outputTokens[outputTokenIndex].str = malloc(3);
            strcpy(outputTokens[outputTokenIndex].str, tokens[tokenIndex].str);
            outputTokenIndex++;

            // Skip whitespace
            while (tokens[tokenIndex].type == PLUS || tokens[tokenIndex].type == MINUS && isspace(*(&tokens[tokenIndex].str + 1))) {
                tokenIndex++;
            }
        } else if (tokens[tokenIndex].type == MUL || tokens[tokenIndex].type == DIV) {
            outputTokens[outputTokenIndex].type = tokens[tokenIndex].type;
            outputTokens[outputTokenIndex].str = malloc(3);
            strcpy(outputTokens[outputTokenIndex].str, tokens[tokenIndex].str);
            outputTokenIndex++;

            // Skip whitespace
            while (tokens[tokenIndex].type == MUL || tokens[tokenIndex].type == DIV && isspace(*(&tokens[tokenIndex].str + 1))) {
                tokenIndex++;
            }
        } else if (tokens[tokenIndex].type == LPAREN) {
            Token* nestedTokens = parser(tokens + tokenIndex + 1);
            outputTokens[outputTokenIndex].type = tokens[tokenIndex].type;
            outputTokens[outputTokenIndex].str = malloc(2);
            strcpy(outputTokens[outputTokenIndex].str, "(");
            outputTokenIndex++;

            // Skip whitespace
            while (tokens[tokenIndex].type == LPAREN && isspace(*(&tokens[tokenIndex].str + 1))) {
                tokenIndex++;
            }

            // Add nested tokens to output
            for (int i = 0; i < nestedTokens->tokenIndex; i++) {
                outputTokens[outputTokenIndex].value = nestedTokens->tokens[i].value;
                outputTokens[outputTokenIndex].str = malloc(20);
                sprintf(outputTokens[outputTokenIndex].str, "%lf", outputTokens[outputTokenIndex].value);
                outputTokenIndex++;
            }

            // Skip whitespace
            while (tokens[tokenIndex].type == LPAREN && isspace(*(&tokens[tokenIndex].str + 1))) {
                tokenIndex++;
            }
        } else if (tokens[tokenIndex].type == UNARY_MINUS) {
            Token* unaryMinusValue = parser(tokens + tokenIndex + 1);
            outputTokens[outputTokenIndex].type = tokens[tokenIndex].type;
            outputTokens[outputTokenIndex].str = malloc(2);
            strcpy(outputTokens[outputTokenIndex].str, "-");
            outputTokenIndex++;

            // Skip whitespace
            while (tokens[tokenIndex].type == UNARY_MINUS && isspace(*(&tokens[tokenIndex].str + 1))) {
                tokenIndex++;
            }

            // Add unary minus value to output
            for (int i = 0; i < unaryMinusValue->tokenIndex; i++) {
                outputTokens[outputTokenIndex].value = unaryMinusValue->tokens[i].value;
                outputTokens[outputTokenIndex].str = malloc(20);
                sprintf(outputTokens[outputTokenIndex].str, "%lf", outputTokens[outputTokenIndex].value);
                outputTokenIndex++;
            }

            // Skip whitespace
            while (tokens[tokenIndex].type == UNARY_MINUS && isspace(*(&tokens[tokenIndex].str + 1))) {
                tokenIndex++;
            }
        } else if (tokens[tokenIndex].type == RPAREN) {
            break;
        }
    }

    return outputTokens;
}

// Evaluator function to evaluate the parsed expression
double evaluator(Token* tokens) {
    double result = 0.0;

    // Evaluate numbers and operators
    for (int i = 0; i < tokens->tokenIndex; i++) {
        if (tokens[i].type == NUMBER) {
            result += tokens[i].value;
        } else if (tokens[i].type == PLUS || tokens[i].type == MINUS) {
            if (i > 0 && tokens[i - 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += opValue;
                        break;
                    case MINUS:
                        result -= opValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER) {
                // Handle operator precedence
                double numValue = tokens[i].value;
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case PLUS:
                        result += numValue;
                        break;
                    case MINUS:
                        result -= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type != NUMBER) {
                // Handle operator precedence
                double opValue = evaluator(tokens + i);
                switch (tokens[i].type) {
                    case MUL:
                        result *= numValue;
                        break;
                    case DIV:
                        result /= numValue;
                        break;
                }
            } else if (i > 0 && tokens[i - 1].type == NUMBER && i < tokens->tokenIndex - 1 && tokens[i + 1].type == NUMBER) {