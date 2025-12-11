import java.util.*;
import java.util.function.BiFunction;
import java.util.stream.Collectors;

public class ExpressionEvaluator {
    private static final Map<String, BiFunction<Integer, Integer, Integer>> OPERATORS = new HashMap<>();
    static {
        OPERATORS.put("+", (a, b) -> a + b);
        OPERATORS.put("-", (a, b) -> a - b);
        OPERATORS.put("*", (a, b) -> a * b);
        OPERATORS.put("/", (a, b) -> a / b);
    }

    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }

    public static int evaluate(String expression) {
        List<String> tokens = tokenize(expression);
        return parse(tokens).evaluate();
    }

    private static List<String> tokenize(String expression) {
        return Arrays.stream(expression.split("\\s+"))
                .flatMap(token -> token.matches("-?\\d+") ? Stream.of(token) : Stream.of(token.split("")))
                .filter(token -> !token.isEmpty())
                .collect(Collectors.toList());
    }

    private static Node parse(List<String> tokens) {
        Deque<Node> values = new ArrayDeque<>();
        Deque<String> ops = new ArrayDeque<>();

        for (String token : tokens) {
            if (isNumber(token)) {
                values.push(new NumberNode(Integer.parseInt(token)));
            } else if (token.equals("(")) {
                ops.push(token);
            } else if (token.equals(")")) {
                while (!ops.peek().equals("(")) {
                    applyOp(ops, values);
                }
                ops.pop();
            } else if (isOperator(token)) {
                while (!ops.isEmpty() && hasPrecedence(ops.peek(), token)) {
                    applyOp(ops, values);
                }
                ops.push(token);
            }
        }

        while (!ops.isEmpty()) {
            applyOp(ops, values);
        }

        return values.pop();
    }

    private static boolean isNumber(String token) {
        try {
            Integer.parseInt(token);
            return true;
        } catch (NumberFormatException e) {
            return false;
        }
    }

    private static boolean isOperator(String token) {
        return OPERATORS.containsKey(token);
    }

    private static boolean hasPrecedence(String op1, String op2) {
        int precedence1 = getPrecedence(op1);
        int precedence2 = getPrecedence(op2);
        return precedence1 >= precedence2;
    }

    private static int getPrecedence(String op) {
        switch (op) {
            case "+":
            case "-":
                return 1;
            case "*":
            case "/":
                return 2;
            default:
                return -1;
        }
    }

    private static void applyOp(Deque<String> ops, Deque<Node> values) {
        String op = ops.pop();
        Node b = values.pop();
        Node a = values.pop();
        values.push(new OperatorNode(op, a, b));
    }

    private interface Node {
        int evaluate();
    }

    private static class NumberNode implements Node {
        private final int value;

        public NumberNode(int value) {
            this.value = value;
        }

        @Override
        public int evaluate() {
            return value;
        }
    }

    private static class OperatorNode implements Node {
        private final String operator;
        private final Node left;
        private final Node right;

        public OperatorNode(String operator, Node left, Node right) {
            this.operator = operator;
            this.left = left;
            this.right = right;
        }

        @Override
        public int evaluate() {
            return OPERATORS.get(operator).apply(left.evaluate(), right.evaluate());
        }
    }
}