import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // Expected: 3
        System.out.println(evaluate("2 * 3 + 4")); // Expected: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Expected: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Expected: 16
    }

    public static int evaluate(String expression) {
        return new Evaluator().evaluate(expression);
    }

    private static class Tokenizer {
        private final String input;
        private int pos = 0;

        Tokenizer(String input) {
            this.input = input;
        }

        Token nextToken() {
            skipWhitespace();
            if (pos >= input.length()) {
                return new Token(TokenType.EOF, null);
            }
            char ch = input.charAt(pos);
            if (Character.isDigit(ch)) {
                int start = pos;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                    pos++;
                }
                return new Token(TokenType.NUMBER, Integer.parseInt(input.substring(start, pos)));
            } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/' || ch == '(' || ch == ')') {
                char type = ch;
                pos++;
                return new Token(TokenType.OPERATOR, type);
            }
            throw new IllegalArgumentException("Unexpected character: " + ch);
        }

        private void skipWhitespace() {
            while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) {
                pos++;
            }
        }
    }

    private static class Parser {
        private final Tokenizer tokenizer;
        private Token currentToken;

        Parser(Tokenizer tokenizer) {
            this.tokenizer = tokenizer;
            this.currentToken = tokenizer.nextToken();
        }

        int parse() {
            return expression();
        }

        private int expression() {
            int result = term();
            while (currentToken.type == TokenType.OPERATOR && (currentToken.value == '+' || currentToken.value == '-')) {
                char op = currentToken.value;
                currentToken = tokenizer.nextToken();
                if (op == '+') {
                    result += term();
                } else {
                    result -= term();
                }
            }
            return result;
        }

        private int term() {
            int result = factor();
            while (currentToken.type == TokenType.OPERATOR && (currentToken.value == '*' || currentToken.value == '/')) {
                char op = currentToken.value;
                currentToken = tokenizer.nextToken();
                if (op == '*') {
                    result *= factor();
                } else {
                    result /= factor();
                }
            }
            return result;
        }

        private int factor() {
            if (currentToken.type == TokenType.OPERATOR && currentToken.value == '-') {
                currentToken = tokenizer.nextToken();
                return -factor();
            } else if (currentToken.type == TokenType.NUMBER) {
                int value = currentToken.value;
                currentToken = tokenizer.nextToken();
                return value;
            } else if (currentToken.type == TokenType.OPERATOR && currentToken.value == '(') {
                currentToken = tokenizer.nextToken();
                int result = expression();
                if (currentToken.type != TokenType.OPERATOR || currentToken.value != ')') {
                    throw new IllegalArgumentException("Expected )");
                }
                currentToken = tokenizer.nextToken();
                return result;
            } else {
                throw new IllegalArgumentException("Unexpected token: " + currentToken);
            }
        }
    }

    private static class Evaluator {
        public int evaluate(String expression) {
            Tokenizer tokenizer = new Tokenizer(expression);
            Parser parser = new Parser(tokenizer);
            return parser.parse();
        }
    }

    private enum TokenType {
        NUMBER, OPERATOR, EOF
    }

    private static class Token {
        final TokenType type;
        final Integer value;

        Token(TokenType type, Integer value) {
            this.type = type;
            this.value = value;
        }

        @Override
        public String toString() {
            return "Token{" +
                    "type=" + type +
                    ", value=" + value +
                    '}';
        }
    }
}