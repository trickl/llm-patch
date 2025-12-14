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
        return new Parser(new Tokenizer(expression).tokenize()).parse();
    }

    private static class Tokenizer {
        private final String input;
        private int pos = 0;

        public Tokenizer(String input) {
            this.input = input;
        }

        public List<Object> tokenize() {
            List<Object> tokens = new ArrayList<>();
            while (pos < input.length()) {
                char c = input.charAt(pos);
                if (Character.isDigit(c)) {
                    int num = 0;
                    boolean isNegative = false;
                    if (c == '-') {
                        isNegative = true;
                        pos++;
                        c = input.charAt(pos);
                    }
                    while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                        num = num * 10 + (input.charAt(pos) - '0');
                        pos++;
                    }
                    tokens.add(isNegative ? -num : num);
                } else if (c == '+' || c == '-' || c == '*' || c == '/' || c == '(' || c == ')') {
                    tokens.add(c);
                    pos++;
                } else {
                    throw new IllegalArgumentException("Unexpected character: " + c);
                }
            }
            return tokens;
        }
    }

    private static class Parser {
        private final List<Object> tokens;
        private int pos = 0;

        public Parser(List<Object> tokens) {
            this.tokens = tokens;
        }

        public int parse() {
            return parseExpression();
        }

        private int parseExpression() {
            int result = parseTerm();
            while (pos < tokens.size()) {
                Object token = tokens.get(pos);
                if (!(token instanceof Character)) {
                    break;
                }
                char op = (Character) token;
                if (op != '+' && op != '-') {
                    break;
                }
                pos++;
                int nextTerm = parseTerm();
                result += (op == '+') ? nextTerm : -nextTerm;
            }
            return result;
        }

        private int parseTerm() {
            int result = parseFactor();
            while (pos < tokens.size()) {
                Object token = tokens.get(pos);
                if (!(token instanceof Character)) {
                    break;
                }
                char op = (Character) token;
                if (op != '*' && op != '/') {
                    break;
                }
                pos++;
                int nextFactor = parseFactor();
                result += (op == '*') ? nextFactor : result / nextFactor;
            }
            return result;
        }

        private int parseFactor() {
            Object token = tokens.get(pos);
            if (token instanceof Integer) {
                pos++;
                return (Integer) token;
            } else if (token instanceof Character && (Character) token == '-') {
                pos++;
                return -parseFactor();
            } else if (token instanceof Character && (Character) token == '(') {
                pos++;
                int result = parseExpression();
            if (!(tokens.get(pos++) instanceof Character) || tokens.get(pos - 1) != ')') {
                    throw new IllegalArgumentException("Unexpected token: '" + (Character) tokens.get(pos - 1) + "'");
            }
                return result;
            } else {
                throw new IllegalArgumentException("Unexpected token: " + token);
            }
        }
    }
}
