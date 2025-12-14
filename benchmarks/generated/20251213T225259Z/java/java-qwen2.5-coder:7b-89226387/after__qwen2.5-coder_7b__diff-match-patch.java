import java.util.*;
import java.util.stream.Collectors;

public class ExpressionEvaluator {
    import java.util.function.BiFunction;    public static void main(String[] args) {
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
        return Arrays.stream(expression.split("(?<=\\D)(?=\\d)|(?<=\\d)(?=\\D)"))
                .map(s -> s.matches("-\\d+") ? "-" + s.substring(1) : s)
                .collect(Collectors.toList());
    }

    private static Node parse(List<String> tokens) {
        Stack<Node> values = new Stack<>();
        Stack<Character> ops = new Stack<>();

        for (String token : tokens) {
            if (token.matches("\\d+")) {
                values.push(new ValueNode(Integer.parseInt(token)));
            } else if (token.equals("(")) {
                ops.push('(');
            } else if (token.equals(")")) {
                while (!ops.peek().equals('(')) {
                    values.push(applyOp(ops.pop(), values.pop(), values.pop()));
                }
                ops.pop();
            } else {
                while (!ops.isEmpty() && hasPrecedence(token.charAt(0), ops.peek())) {
                    values.push(applyOp(ops.pop(), values.pop(), values.pop()));
                }
                ops.push(token.charAt(0));
            }
        }

        while (!ops.isEmpty()) {
            values.push(applyOp(ops.pop(), values.pop(), values.pop()));
        }

        return values.pop();
    }

    private static boolean hasPrecedence(char op1, char op2) {
        if (op2 == '(' || op2 == ')') {
            return false;
        }
        if ((op1 == '*' || op1 == '/') && (op2 == '+' || op2 == '-')) {
            return false;
        }
        return true;
    }

    private static Node applyOp(char op, Node b, Node a) {
        switch (op) {
            case '+':
                return new BinaryNode(a, b, (x, y) -> x + y);
            case '-':
                return new BinaryNode(b, a, (x, y) -> y - x);
            case '*':
                return new BinaryNode(a, b, (x, y) -> x * y);
            case '/':
                return new BinaryNode(b, a, (x, y) -> y / x);
        }
        throw new IllegalArgumentException("Unsupported operation: " + op);
    }

    private interface Node {
        int evaluate();
    }

    private static class ValueNode implements Node {
        private final int value;

        public ValueNode(int value) {
            this.value = value;
        }

        @Override
        public int evaluate() {
            return value;
        }
    }

    private static class BinaryNode implements Node {
        private final Node left;
        private final Node right;
        private final BiFunction<Integer, Integer, Integer> operation;

        public BinaryNode(Node left, Node right, BiFunction<Integer, Integer, Integer> operation) {
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