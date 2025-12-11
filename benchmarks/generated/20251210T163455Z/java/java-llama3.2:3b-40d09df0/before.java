import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }

    public static int evaluate(String expression) {
        return new ExpressionEvaluator().evaluate(expression);
    }

    private static class Tokenizer implements Iterable<String> {
        private final String expression;
        private int pos = 0;

        public Tokenizer(String expression) {
            this.expression = expression;
        }

        @Override
        public Iterator<String> iterator() {
            while (pos < expression.length()) {
                if (Character.isDigit(expression.charAt(pos))) {
                    StringBuilder sb = new StringBuilder();
                    while (pos < expression.length() && Character.isDigit(expression.charAt(pos))) {
                        sb.append(expression.charAt(pos));
                        pos++;
                    }
                    yield sb.toString();
                } else if (expression.charAt(pos) == '(' || expression.charAt(pos) == ')') {
                    yield String.valueOf(expression.charAt(pos));
                    pos++;
                } else if (expression.charAt(pos) == '+' || expression.charAt(pos) == '-' || expression.charAt(pos) == '*' || expression.charAt(pos) == '/') {
                    yield String.valueOf(expression.charAt(pos));
                    pos++;
                }
            }
        }
    }

    private static class Parser implements Iterable<Integer> {
        private final Tokenizer tokenizer;
        private int pos = 0;

        public Parser(Tokenizer tokenizer) {
            this.tokenizer = tokenizer;
        }

        @Override
        public Iterator<Integer> iterator() {
            while (pos < tokenizer.iterator().iterator().next().length()) {
                if (Character.isDigit(tokenizer.iterator().next().charAt(pos))) {
                    StringBuilder sb = new StringBuilder();
                    while (pos < tokenizer.iterator().next().length() && Character.isDigit(tokenizer.iterator().next().charAt(pos))) {
                        sb.append(tokenizer.iterator().next().charAt(pos));
                        pos++;
                    }
                    yield Integer.parseInt(sb.toString());
                } else if (tokenizer.iterator().next().charAt(pos) == '(') {
                    yield 1;
                    pos++;
                } else if (tokenizer.iterator().next().charAt(pos) == ')') {
                    yield -1;
                    pos++;
                } else if (tokenizer.iterator().next().charAt(pos) == '+' || tokenizer.iterator().next().charAt(pos) == '-' || tokenizer.iterator().next().charAt(pos) == '*' || tokenizer.iterator().next().charAt(pos) == '/') {
                    yield getPrecedence(tokenizer.iterator().next().charAt(pos));
                    pos++;
                }
            }
        }

        private int getPrecedence(char operator) {
            if (operator == '+' || operator == '-') return 1;
            if (operator == '*' || operator == '/') return 2;
            throw new RuntimeException("Invalid operator");
        }
    }

    private static class Evaluator implements Iterable<Integer> {
        private final Parser parser;

        public Evaluator(Parser parser) {
            this.parser = parser;
        }

        @Override
        public Iterator<Integer> iterator() {
            Stack<Integer> stack = new Stack<>();
            for (int token : parser) {
                if (token == 1) {
                    // '(' encountered, push onto stack
                    stack.push(token);
                } else if (token == -1) {
                    // ')' encountered, pop from stack
                    stack.pop();
                } else {
                    // operand or operator encountered
                    if (!stack.isEmpty()) {
                        int operand2 = stack.pop();
                        int operand1 = stack.pop();
                        int result = applyOperation(operand1, operand2, token);
                        stack.push(result);
                    } else {
                        throw new RuntimeException("Invalid expression");
                    }
                }
            }
            return stack.iterator();
        }

        private int applyOperation(int operand1, int operand2, int operator) {
            switch (operator) {
                case '+':
                    return operand1 + operand2;
                case '-':
                    return operand1 - operand2;
                case '*':
                    return operand1 * operand2;
                case '/':
                    return operand1 / operand2;
                default:
                    throw new RuntimeException("Invalid operator");
            }
        }
    }

    public static int evaluate(String expression) {
        Tokenizer tokenizer = new Tokenizer(expression);
        Parser parser = new Parser(tokenizer);
        Evaluator evaluator = new Evaluator(parser);
        return evaluator.iterator().next();
    }
}