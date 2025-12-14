import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Should print 7
        System.out.println(evaluate("2 * 3 + 4")); // Should print 10
        System.out.println(evaluate("2 * (3 + 4)")); // Should print 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Should print 16
    }

    public static int evaluate(String expression) {
        return new Evaluator().evaluate(expression);
    }

    private static class Tokenizer {
        private final String input;
        private int pos = 0;

        public Tokenizer(String input) {
            this.input = input;
        }

        public List<String> tokenize() {
            List<String> tokens = new ArrayList<>();
            while (pos < input.length()) {
                char ch = input.charAt(pos);
                if (Character.isDigit(ch)) {
                    int start = pos;
                    while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                        pos++;
                    }
                    tokens.add(input.substring(start, pos));
                } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/' || ch == '(' || ch == ')') {
                    tokens.add(String.valueOf(ch));
                    pos++;
                } else {
                    throw new IllegalArgumentException("Invalid character: " + ch);
                }
            }
            return tokens;
        }
    }

    private static class Evaluator {
        private final List<String> tokens;
        private int pos = 0;

        public Evaluator() {
            this.tokens = new Tokenizer("").tokenize();
        }

        public Evaluator(List<String> tokens) {
            this.tokens = tokens;
        }

        public int evaluate(String expression) {
            this.tokens = new Tokenizer(expression).tokenize();
            return parseExpression();
        }

        private int parseExpression() {
            return parseTerm();
        }

        private int parseTerm() {
            int result = parseFactor();
            while (pos < tokens.size()) {
                String token = tokens.get(pos);
                if (token.equals("+")) {
                    pos++;
                    result += parseFactor();
                } else if (token.equals("-")) {
                    pos++;
                    result -= parseFactor();
                } else {
                    break;
                }
            }
            return result;
        }

        private int parseFactor() {
            String token = tokens.get(pos);
            if (Character.isDigit(token.charAt(0))) {
                pos++;
                return Integer.parseInt(token);
            } else if (token.equals("-")) {
                pos++;
                return -parseFactor();
            } else if (token.equals("(")) {
                pos++;
                int result = parseExpression();
                if (!tokens.get(pos).equals(")")) {
                    throw new IllegalArgumentException("Expected ')'");
                }
                pos++;
                return result;
            } else {
                throw new IllegalArgumentException("Unexpected token: " + token);
            }
        }
    }
}