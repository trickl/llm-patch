import java.util.*;
import java.util.stream.Collectors;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // Expected: 3
        System.out.println(evaluate("2 * 3 + 4")); // Expected: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Expected: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Expected: 16
    }

    public static int evaluate(String expression) {
        List<String> tokens = tokenize(expression);
        return parse(tokens).evaluate();
    }

    private static List<String> tokenize(String expression) {
        return Arrays.stream(expression.split(" "))
                .filter(s -> !s.trim().isEmpty())
                .collect(Collectors.toList());
    }

    private static Node parse(List<String> tokens) {
        Deque<Node> values = new ArrayDeque<>();
        Deque<Character> ops = new ArrayDeque<>();

        for (String token : tokens) {
            if (token.matches("-?\\d+")) {
                values.push(new ValueNode(Integer.parseInt(token)));
            } else if ("+-*/".indexOf(token.charAt(0)) != -1) {
                while (!ops.isEmpty() && hasPrecedence(ops.peek(), token.charAt(0))) {
                    values.push(applyOp(ops.pop(), values.pop(), values.pop()));
                }
                ops.push(token.charAt(0));
            } else if (token.equals("(")) {
                ops.push(token.charAt(0));
            } else if (token.equals(")")) {
                while (!ops.peek().equals('(')) {
                    values.push(applyOp(ops.pop(), values.pop(), values.pop()));
                }
                ops.pop();
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
                return new BinaryNode('+', a, b);
            case '-':
                return new BinaryNode('-', a, b);
            case '*':
                return new BinaryNode('*', a, b);
            case '/':
                return new BinaryNode('/', a, b);
            default:
                throw new IllegalArgumentException("Unsupported operator: " + op);
        }
    }

    private static class Node {
        abstract int evaluate();
    }

    private static class ValueNode extends Node {
        final int value;

        ValueNode(int value) {
            this.value = value;
        }

        @Override
        int evaluate() {
            return value;
        }
    }

    private static class BinaryNode extends Node {
        final char op;
        final Node left, right;

        BinaryNode(char op, Node left, Node right) {
            this.op = op;
            this.left = left;
            this.right = right;
        }

        @Override
        int evaluate() {
            switch (op) {
                case '+':
                    return left.evaluate() + right.evaluate();
                case '-':
                    return left.evaluate() - right.evaluate();
                case '*':
                    return left.evaluate() * right.evaluate();
                case '/':
                    return left.evaluate() / right.evaluate();
                default:
                    throw new IllegalArgumentException("Unsupported operator: " + op);
            }
        }
    }
}