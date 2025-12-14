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
        return new Parser(new Tokenizer(expression)).parse();
    }
    private List<Object> tokenize(String expression) {
    private static class Tokenizer {
        private final String input;
        private int pos = 0;

        Tokenizer(String input) {
            this.input = input;
        }

        List<Object> tokenize() {
            List<Object> tokens = new ArrayList<>();
            while (pos < input.length()) {
                char ch = input.charAt(pos);
                if (Character.isDigit(ch)) {
                    tokens.add(parseNumber());
                } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/') {
                    tokens.add(ch);
                    pos++;
                } else if (ch == '(') {
                    tokens.add('(');
                    pos++;
                } else if (ch == ')') {
                    tokens.add(')');
                    pos++;
                } else if (Character.isWhitespace(ch)) {
                    pos++;
                } else {
                    throw new IllegalArgumentException("Unexpected character: " + ch);
                }
            }
            return tokens;
        }

        private int parseNumber() {
            int start = pos;
            while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                pos++;
            }
            return Integer.parseInt(input.substring(start, pos));
        }
    }

    private static class Parser {
        private final List<Object> tokens;
        private int pos = 0;

        Parser(List<Object> tokens) {
            this.tokens = tokens;
        }

        int parse() {
            return parseExpression();
        }

        private int parseExpression() {
            Stack<Integer> values = new Stack<>();
            Stack<Character> ops = new Stack<>();
            while (pos < tokens.size()) {
                Object token = tokens.get(pos);
                if (token instanceof Integer) {
                    values.push((Integer) token);
                } else if (token == '(') {
                    ops.push((Character) token);
                } else if (token == ')') {
                    while (!ops.isEmpty() && ops.peek() != '(') {
                        applyOp(values, ops.pop());
                    }
                    ops.pop();
                } else {
                    while (!ops.isEmpty() && hasPrecedence((Character) token, ops.peek())) {
                        applyOp(values, ops.pop());
                    }
                    ops.push((Character) token);
                }
                pos++;
            }

            while (!ops.isEmpty()) {
                applyOp(values, ops.pop());
            }

            return values.pop();
        }

        private boolean hasPrecedence(char op1, char op2) {
            if (op2 == '(' || op2 == ')') {
                return false;
            }
            if ((op1 == '*' || op1 == '/') && (op2 == '+' || op2 == '-')) {
                return false;
            }
            return true;
        }

        private void applyOp(Stack<Integer> values, char op) {
            int b = values.pop();
            int a = values.pop();
            switch (op) {
                case '+':
                    values.push(a + b);
                    break;
                case '-':
                    values.push(a - b);
                    break;
                case '*':
                    values.push(a * b);
                    break;
                case '/':
                    if (b == 0) throw new ArithmeticException("Division by zero");
                    values.push(a / b);
                    break;
            }
        }
    }
}
