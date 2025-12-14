import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Output: 7
        System.out.println(evaluate("2 * 3 + 4")); // Output: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Output: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Output: 16
    }

    public static int evaluate(String expression) {
        return new Evaluator().evaluate(expression);
    }

    private static class Tokenizer {
        private final String input;
        private int pos;

        public Tokenizer(String input) {
            this.input = input;
            this.pos = 0;
        }

        public List<String> tokenize() {
            List<String> tokens = new ArrayList<>();
            while (pos < input.length()) {
                char c = input.charAt(pos);
                if (Character.isDigit(c)) {
                    int start = pos;
                    while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                        pos++;
                    }
                    tokens.add(input.substring(start, pos));
                } else if (c == '+' || c == '-' || c == '*' || c == '/' || c == '(' || c == ')') {
                    tokens.add(String.valueOf(c));
                    pos++;
                } else if (Character.isWhitespace(c)) {
                    pos++;
                } else {
                    throw new IllegalArgumentException("Invalid character: " + c);
                }
            }
            return tokens;
        }
    }

    private static class Evaluator {
        private final List<String> tokens;
        private int pos;

        public Evaluator() {
            this.tokens = new Tokenizer("").tokenize();
            this.pos = 0;
        }

        public int evaluate(String expression) {
            this.tokens = new Tokenizer(expression).tokenize();
            this.pos = 1; // Change pos to 1 instead of 0
            return parseExpression();
        }

        private int parseExpression() {
            int result = parseTerm();
            while (pos < tokens.size()) {
                String operator = tokens.get(pos);
                if (!operator.equals("+") && !operator.equals("-")) {
                    break;
                }
                pos++;
                int nextTerm = parseTerm();
                if (operator.equals("+")) {
                    result += nextTerm;
                } else {
                    result -= nextTerm;
                }
            }
            return result;
        }

        private int parseTerm() {
            int result = parseFactor();
            while (pos < tokens.size()) {
                String operator = tokens.get(pos);
                if (!operator.equals("*") && !operator.equals("/")) {
                    break;
                }
                pos++;
                int nextFactor = parseFactor();
                if (operator.equals("*")) {
                    result *= nextFactor;
                } else {
                    result /= nextFactor;
                }
            }
            return result;
        }

        private int parseFactor() {
            String token = tokens.get(pos);
            if (token.equals("+")) {
                pos++;
                return parseExpression();
            } else if (token.equals("-")) {
                pos++;
                return -parseExpression();
            } else if (token.equals("(")) {
                pos++;
                int result = parseExpression();
                if (!tokens.get(pos).equals(")")) {
                    throw new IllegalArgumentException("Expected ')'");
                }
                pos++;
                return result;
            } else {
                try {
                    int value = Integer.parseInt(token);
                    pos++;
                    return value;
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Invalid number: " + token);
                }
            }
        }
    }
}
