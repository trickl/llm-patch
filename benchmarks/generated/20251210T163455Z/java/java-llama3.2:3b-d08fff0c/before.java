import java.util.*;

public class ExpressionEvaluator {

    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }

    public static int evaluate(String expression) {
        Tokenizer tokenizer = new Tokenizer(expression);
        Parser parser = new Parser(tokenizer);
        return parser.parse();
    }

    private static class Tokenizer {

        private final String expression;
        private final List<Token> tokens;

        public Tokenizer(String expression) {
            this.expression = expression;
            tokens = tokenize(expression);
        }

        private List<Token> tokenize(String expression) {
            List<Token> tokens = new ArrayList<>();
            StringBuilder currentNumber = new StringBuilder();
            for (char c : expression.toCharArray()) {
                if (Character.isDigit(c)) {
                    currentNumber.append(c);
                } else if (c == '(' || c == ')') {
                    tokens.add(new Token(c, Token.Type.PAREN));
                } else if (c == '+' || c == '-' || c == '*' || c == '/') {
                    tokens.add(new Token(c, Token.Type.OPERATOR));
                }
            }
            if (!currentNumber.isEmpty()) {
                tokens.add(new Token(currentNumber.toString(), Token.Type.NUMBER));
            }
            return tokens;
        }

        public List<Token> getTokens() {
            return tokens;
        }
    }

    private static class Parser {

        private final List<Token> tokens;
        private int index;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
            this.index = 0;
        }

        public int parse() {
            return parseExpression();
        }

        private int parseExpression() {
            int result = parseTerm();
            while (index < tokens.size()) {
                Token token = tokens.get(index);
                if (token.type == Token.Type.OPERATOR) {
                    switch (token.value) {
                        case "+":
                            result += parseTerm();
                            break;
                        case "-":
                            result -= parseTerm();
                            break;
                    }
                    index++;
                } else if (token.type == Token.Type.PAREN) {
                    int expressionResult = parseExpression();
                    if (expressionResult != Integer.MIN_VALUE) {
                        return expressionResult;
                    }
                    index++; // skip closing parenthesis
                } else {
                    throw new RuntimeException("Unexpected token: " + token.value);
                }
            }
            return result;
        }

        private int parseTerm() {
            int result = parseFactor();
            while (index < tokens.size()) {
                Token token = tokens.get(index);
                if (token.type == Token.Type.OPERATOR) {
                    switch (token.value) {
                        case "*":
                            result *= parseFactor();
                            break;
                        case "/":
                            result /= parseFactor();
                            break;
                    }
                    index++;
                } else if (token.type == Token.Type.PAREN) {
                    int expressionResult = parseExpression();
                    if (expressionResult != Integer.MIN_VALUE) {
                        return expressionResult;
                    }
                    index++; // skip closing parenthesis
                } else {
                    throw new RuntimeException("Unexpected token: " + token.value);
                }
            }
            return result;
        }

        private int parseFactor() {
            if (index >= tokens.size()) {
                return Integer.MIN_VALUE; // invalid expression
            }
            Token token = tokens.get(index++);
            switch (token.type) {
                case Token.Type.NUMBER:
                    return Integer.parseInt(token.value);
                case Token.Type.PAREN:
                    int expressionResult = parseExpression();
                    if (expressionResult != Integer.MIN_VALUE) {
                        return expressionResult;
                    }
                    index++; // skip closing parenthesis
                case Token.Type.MINUS:
                    return -parseFactor();
                default:
                    throw new RuntimeException("Unexpected token: " + token.value);
            }
        }
    }

    private static class Token {

        public enum Type { NUMBER, OPERATOR, PAREN };

        private final String value;
        private final Type type;

        public Token(String value, Type type) {
            this.value = value;
            this.type = type;
        }

        @Override
        public String toString() {
            return value;
        }
    }
}