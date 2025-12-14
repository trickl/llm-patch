import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Output: 7
        System.out.println(evaluate("2 * 3 + 4")); // Output: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Output: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Output: 16
    }

    public static int evaluate(String expression) {
        return new Parser(new Tokenizer(expression)).parse();
    }
    private static class Tokenizer implements Iterable<Token> {
        private final String input;
        private int pos;

        Tokenizer(String input) {
            this.input = input;
            this.pos = 0;
        }

        List<Token> tokenize() {
            List<Token> tokens = new ArrayList<>();
            while (pos < input.length()) {
                skipWhitespace();
                if (Character.isDigit(input.charAt(pos))) {
                    tokens.add(parseNumber());
                } else if (input.charAt(pos) == '+' || input.charAt(pos) == '-' ||
                           input.charAt(pos) == '*' || input.charAt(pos) == '/' ||
                           input.charAt(pos) == '(' || input.charAt(pos) == ')') {
                    tokens.add(new Token(input.charAt(pos), pos));
                    pos++;
                } else {
                    throw new IllegalArgumentException("Unexpected character at position " + pos);
                }
            }
            return tokens;
        }

        private void skipWhitespace() {
            while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) {
                pos++;
            }
        }

        private Token parseNumber() {
            int start = pos;
            boolean negative = false;
            if (input.charAt(pos) == '-') {
                negative = true;
                pos++;
            }
            while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                pos++;
            }
            return new Token(negative ? -Integer.parseInt(input.substring(start + 1, pos)) : Integer.parseInt(input.substring(start, pos)), start);
        }
    }

    private static class Parser {
        private final List<Token> tokens;
        private int pos;

        Parser(List<Token> tokens) {
            this.tokens = tokens;
            this.pos = 0;
        }

        int parse() {
            return parseExpression();
        }

        private int parseExpression() {
            int result = parseTerm();
            while (pos < tokens.size()) {
                Token token = tokens.get(pos);
                if (token.type == '+' || token.type == '-') {
                    pos++;
                    int nextTerm = parseTerm();
                    result += token.type == '+' ? nextTerm : -nextTerm;
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
                if (token.type == '*' || token.type == '/') {
                    pos++;
                    int nextFactor = parseFactor();
                    result *= token.type == '*' ? nextFactor : result / nextFactor;
                } else {
                    break;
                }
            }
            return result;
            }
        }
        private int parseFactor() throws IllegalArgumentException {
            Token token = tokens.get(pos);
            if (token.type == '(') {
                pos++;
                int result = parseExpression();
                if (pos < tokens.size() && tokens.get(pos).type == ')') {
                    pos++;
                } else {
                    throw new IllegalArgumentException("Expected ')' at position " + pos);
                }
                return result;
            } else if (token.type instanceof Integer) {
                pos++;
                return (Integer) token.type;
            } else {
                throw new IllegalArgumentException("Unexpected token at position " + pos);
            }
        }
    }

    private static class Token {
        Object type;
        int position;

        Token(Object type, int position) {
            this.type = type;
            this.position = position;
        }

        @Override
        public String toString() {
            return "Token{" +
                    "type=" + type +
                    ", position=" + position +
                    '}';
        }
    }
}
