import java.util.*;
import java.util.regex.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // Expected: 3
        System.out.println(evaluate("2 * 3 + 4")); // Expected: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Expected: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Expected: 16
    }

    public static int evaluate(String expression) {
        return new Parser(new Tokenizer(expression)).parse();
    }

    private static class Tokenizer {
        private final String input;
        private int pos = 0;

        Tokenizer(String input) {
            this.input = input.replaceAll("\\s+", "");
        }

        List<Token> tokenize() {
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
                } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/') {
                    tokens.add(new Token(TokenType.OPERATOR, ch));
                    pos++;
                } else if (ch == '(') {
                    tokens.add(new Token(TokenType.PARENTHESIS, '('));
                    pos++;
                } else if (ch == ')') {
                    tokens.add(new Token(TokenType.PARENTHESIS, ')'));
                    pos++;
                }
            }
            return tokens;
        }
    }

    private static class Parser {
        private final List<Token> tokens;
        private int pos = 0;

        Parser(List<Token> tokens) {
            this.tokens = tokens;
        }

        int parse() {
            return parseExpression();
        }

        private int parseExpression() {
            int result = parseTerm();
            while (pos < tokens.size()) {
                Token token = tokens.get(pos);
                if (token.type == TokenType.OPERATOR && (token.value == '+' || token.value == '-')) {
                    pos++;
                    int nextTerm = parseTerm();
                    if (token.value == '+') {
                        result += nextTerm;
                    } else {
                        result -= nextTerm;
                    }
                } else {
                    break;
                }
            }
            return result;
        }

        private int parseTerm() {
            int result = parseFactor();
            while (pos < tokens.size()) {
                Token token = tokens.get(pos);
                if (token.type == TokenType.OPERATOR && (token.value == '*' || token.value == '/')) {
                    pos++;
                    int nextFactor = parseFactor();
                    if (token.value == '*') {
                        result *= nextFactor;
                    } else {
                        result /= nextFactor;
                    }
                } else {
                    break;
                }
            }
            return result;
        }

        private int parseFactor() {
            Token token = tokens.get(pos);
            if (token.type == TokenType.OPERATOR && token.value == '-') {
                pos++;
                return -parsePrimary();
            } else {
                return parsePrimary();
            }
        }

        private int parsePrimary() {
            Token token = tokens.get(pos);
            if (token.type == TokenType.NUMBER) {
                pos++;
                return token.value;
            } else if (token.type == TokenType.PARENTHESIS && token.value == '(') {
                pos++;
                int result = parseExpression();
                if (pos < tokens.size() && tokens.get(pos).type == TokenType.PARENTHESIS && tokens.get(pos).value == ')') {
                    pos++;
                    return result;
                } else {
                    throw new IllegalArgumentException("Missing closing parenthesis");
                }
            } else {
                throw new IllegalArgumentException("Unexpected token: " + token);
            }
        }
    }

    private static class Token {
        enum TokenType { NUMBER, OPERATOR, PARENTHESIS }
        final TokenType type;
        final int value;

        Token(TokenType type, int value) {
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