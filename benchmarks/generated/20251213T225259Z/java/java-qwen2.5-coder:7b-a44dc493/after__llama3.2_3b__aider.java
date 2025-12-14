import java.util.*;
import java.util.function.Function;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // Expected: 3
        System.out.println(evaluate("2 * 3 + 4")); // Expected: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Expected: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Expected: 16
    }

    public static int evaluate(String expression) {
        return new Parser(expression).parse();
    }

    private static class Tokenizer {
        private final String input;
        private int pos = 0;

        Tokenizer(String input) {
            this.input = input;
        }

        boolean hasNext() {
            skipWhitespace();
            return pos < input.length();
        }

        Token nextToken() {
            skipWhitespace();
            if (pos >= input.length()) throw new IllegalArgumentException("Unexpected end of expression");
            char ch = input.charAt(pos);
            if (Character.isDigit(ch)) {
                int start = pos;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) pos++;
            return new Token(TokenType.NUMBER, Integer.parseInt(input.substring(start, pos)));
        } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/' || ch == '-') {
                char op = ch;
                pos++;
                return new Token(TokenType.OPERATOR, op);
            } else if (ch == '(') {
                pos++;
                return new Token(TokenType.LPAREN, null);
            } else if (ch == ')') {
                pos++;
                return new Token(TokenType.RPAREN, null);
            } else {
                throw new IllegalArgumentException("Unexpected character: " + ch);
            }
        }

        private void skipWhitespace() {
            while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) pos++;
        }
    }

    private static class Parser {
        private final Tokenizer tokenizer;
        private Token currentToken;

        Parser(String expression) {
            this.tokenizer = new Tokenizer(expression);
            nextToken();
        }

        int parse() {
            return expression(0);
        }

        private int expression(int precedence) {
            int result = term();

            while (currentToken.type == TokenType.OPERATOR && precedence < getPrecedence(currentToken.value)) {
                char op = currentToken.value;
                nextToken();
                if (op == '+') result += term();
                else if (op == '-') result -= term();
                else throw new IllegalArgumentException("Unexpected operator: " + op);
            }

            return result;
        }

        private int term() {
            int result = factor();

            while (currentToken.type == TokenType.OPERATOR && getPrecedence(currentToken.value) >= 2) {
                char op = currentToken.value;
                nextToken();
                if (op == '*') result *= factor();
                else if (op == '/') result /= factor();
                else throw new IllegalArgumentException("Unexpected operator: " + op);
            }

            return result;
        }

        private int factor() {
            if (currentToken.type == TokenType.LPAREN) {
                nextToken();
                int result = expression(0);
                consume(TokenType.RPAREN);
                return result;
            } else if (currentToken.type == TokenType.OPERATOR && currentToken.value == '-') {
                nextToken();
                return -factor();
            } else if (currentToken.type == TokenType.NUMBER) {
                int value = currentToken.value;
                nextToken();
                return value;
            } else throw new IllegalArgumentException("Unexpected token: " + currentToken);
        }

        private void consume(TokenType type) {
            if (currentToken.type != type) throw new IllegalArgumentException("Expected " + type + ", but got " + currentToken.type);
            nextToken();
        }

        private int getPrecedence(char op) {
            return switch (op) {
                case '+', '-' -> 1;
                case '*', '/' -> 2;
                default -> -1;
            };
        }
    }

    private static class Token {
        enum TokenType { NUMBER, OPERATOR, LPAREN, RPAREN }
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
