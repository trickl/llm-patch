import java.util.*;
import java.util.function.BiFunction;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // Expected: 3
        System.out.println(evaluate("2 * 3 + 4")); // Expected: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Expected: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Expected: 16
    }

    public static int evaluate(String expression) {
        return new Parser(new Tokenizer(expression).tokenize()).parse();
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
                } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/') {
                    tokens.add(new Token(TokenType.OPERATOR, ch));
                    pos++;
                } else if (ch == '(') {
                    tokens.add(new Token(TokenType.PARENTHESIS, '('));
                    pos++;
                } else if (ch == ')') {
                    tokens.add(new Token(TokenType.PARENTHESIS, ')'));
                    pos++;
                } else if (Character.isWhitespace(ch)) {
                    pos++;
                } else {
                    throw new IllegalArgumentException("Unexpected character: " + ch);
                }
            }
            return tokens;
        }

        private static class Token {
            final TokenType type;
            final Object value;

            public Token(TokenType type, Object value) {
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

        enum TokenType {
            NUMBER,
            OPERATOR,
            PARENTHESIS
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
                if (token.type == Token.TokenType.OPERATOR && (token.value.equals("+") || token.value.equals("-"))) {
                    pos++;
                    int nextTerm = term();
                    result += token.value.equals("+") ? nextTerm : -nextTerm;
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
                if (token.type == Token.TokenType.OPERATOR && (token.value.equals("*") || token.value.equals("/"))) {
                    pos++;
                    int nextFactor = factor();
                    result += token.value.equals("*") ? nextFactor : result / nextFactor;
                } else {
                    break;
                }
            }
            return result;
        }

        private int factor() {
            Token token = tokens.get(pos);
            if (token.type == Token.TokenType.OPERATOR && token.value.equals("-")) {
                pos++;
                return -factor();
            } else if (token.type == Token.TokenType.PARENTHESIS && token.value.equals("(")) {
                pos++;
                int result = expression();
                if (pos < tokens.size() && tokens.get(pos).type == Token.TokenType.PARENTHESIS && tokens.get(pos).value.equals(")")) {
                    pos++;
                    return result;
                } else {
                    throw new IllegalArgumentException("Unmatched parenthesis");
                }
            } else if (token.type == Token.TokenType.NUMBER) {
                pos++;
                return (int) token.value;
            } else {
                throw new IllegalArgumentException("Unexpected token: " + token);
            }
        }
    }
}