import java.util.*;
import java.util.function.BiFunction;
import java.util.stream.Collectors;

public class ExpressionEvaluator {
    private static final Map<String, BiFunction<Integer, Integer, Integer>> OPERATORS = new HashMap<>();
    private static final Set<String> UNARY_OPERATORS = new HashSet<>();

    static {
        OPERATORS.put("+", (a, b) -> a + b);
        OPERATORS.put("-", (a, b) -> a - b);
        OPERATORS.put("*", (a, b) -> a * b);
        OPERATORS.put("/", (a, b) -> a / b);
        UNARY_OPERATORS.add("-");
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
       .filter(token -> !(token instanceof String) || !token.isEmpty())
        .collect(Collectors.toList());
    }

    private static Node parse(List<String> tokens) {
        Deque<Node> values = new ArrayDeque<>();
        Deque<String> ops = new ArrayDeque<>();

        for (String token : tokens) {
            if (token.matches("-?\\d+")) {
                values.push(new ValueNode(Integer.parseInt(token)));
            } else if (UNARY_OPERATORS.contains(token)) {
                ops.push(token);
            } else if (OPERATORS.containsKey(token)) {
                while (!ops.isEmpty() && hasPrecedence(ops.peek(), token)) {
                    applyOp(values, ops.pop());
                }
                ops.push(token);
            } else if (token.equals("(")) {
                ops.push(token);
            } else if (token.equals(")")) {
                while (!ops.peek().equals("(")) {
                    applyOp(values, ops.pop());
                }
                ops.pop();
            }
        }

        while (!ops.isEmpty()) {
            applyOp(values, ops.pop());
        }

        return values.pop();
    }

    private static boolean hasPrecedence(String op1, String op2) {
        if (op2.equals("(") || op2.equals(")")) {
            return false;
        }
        return OPERATORS.get(op1).hashCode() > OPERATORS.get(op2).hashCode();
    }

    private static void applyOp(Deque<Node> values, String op) {
        Node b = values.pop();
        Node a = values.pop();

        if (op.equals("-") && a instanceof ValueNode && b instanceof ValueNode) {
            values.push(new ValueNode(-(a.getValue() - b.getValue())));
        } else {
            values.push(new OperatorNode(a, b, OPERATORS.get(op)));
        }
    }

    private static abstract class Node {
        public abstract int evaluate();
    }

    private static class ValueNode extends Node {
        private final int value;

        public ValueNode(int value) {
            this.value = value;
        }

        @Override
        public int evaluate() {
            return value;
        }
    }

    private static class OperatorNode extends Node {
        private final Node left;
        private final Node right;
        private final BiFunction<Integer, Integer, Integer> operation;

        public OperatorNode(Node left, Node right, BiFunction<Integer, Integer, Integer> operation) {
            this.left = left;
            this.right = right;
            this.operation = operation;
        }

        @Override
        public int evaluate() {
            return operation.apply(left.evaluate(), right.evaluate());
        }
    }
}
