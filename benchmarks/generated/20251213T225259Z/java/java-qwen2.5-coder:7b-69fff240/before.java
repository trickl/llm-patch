import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Should print 7
        System.out.println(evaluate("2 * 3 + 4")); // Should print 10
        System.out.println(evaluate("2 * (3 + 4)")); // Should print 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Should print 16
    }

    public static int evaluate(String expression) {
        return new Parser(new Tokenizer(expression)).parse();
    }

    private static class Tokenizer {
        private final String input;
        private int pos = 0;

        public Tokenizer(String input) {
            this.input = input;
        }

        public List<Token> tokenize() {
            List<Token> tokens = new ArrayList<>();
            while (pos < input.length()) {
                char ch = input.charAt(pos);
                if (Character.isDigit(ch)) {
                    int value = 0;
                    while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                        value = value * 10 + (input.charAt(pos) - '0');
                        pos++;
                    }
                    tokens.add(new Token(TokenType.NUMBER, value));
                } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/' || ch == '(' || ch == ')') {
                    tokens.add(new Token(TokenType.OPERATOR, ch));
                    pos++;
                } else if (Character.isWhitespace(ch)) {
                    pos++;
                } else {
                    throw new IllegalArgumentException("Unexpected character: " + ch);
                }
            }
            return tokens;
        }
    }

    private static class Parser {
        private final List<Token> tokens;
        private int pos = 0;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
        }

        public int parse() {
            return expression();
        }

        private int expression() {
            int result = term();
            while (pos < tokens.size()) {
                Token token = tokens.get(pos);
                if (token.type == TokenType.OPERATOR && (token.value == '+' || token.value == '-')) {
                    pos++;
                    int rhs = term();
                    if (token.value == '+') {
                        result += rhs;
                    } else {
                        result -= rhs;
                    }
                } else {
                    break;
                }
            }
            return result;
        }

        private int term() {
            int result = factor();
            while (pos < tokens.size()) {
                Token token = tokens.get(pos);
                if (token.type == TokenType.OPERATOR && (token.value == '*' || token.value == '/')) {
                    pos++;
                    int rhs = factor();
                    if (token.value == '*') {
                        result *= rhs;
                    } else {
                        result /= rhs;
                    }
                } else {
                    break;
                }
            }
            return result;
        }

        private int factor() {
            Token token = tokens.get(pos);
            pos++;
            if (token.type == TokenType.OPERATOR && token.value == '-') {
                return -factor();
            } else if (token.type == TokenType.NUMBER) {
                return token.value;
            } else if (token.type == TokenType.OPERATOR && token.value == '(') {
                int result = expression();
                token = tokens.get(pos);
                pos++;
                if (token.type != TokenType.OPERATOR || token.value != ')') {
                    throw new IllegalArgumentException("Expected ')' but found " + token.value);
                }
                return result;
            } else {
                throw new IllegalArgumentException("Unexpected token: " + token.value);
            }
        }
    }

    private static class Token {
        public enum TokenType { NUMBER, OPERATOR }
        public final TokenType type;
        public final int value;

        public Token(TokenType type, int value) {
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