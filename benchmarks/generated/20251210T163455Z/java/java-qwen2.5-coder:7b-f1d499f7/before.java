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
        List<String> tokens = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean inNumber = false;
        for (char c : expression.toCharArray()) {
            if (Character.isDigit(c)) {
                sb.append(c);
                inNumber = true;
            } else if (c == ' ') {
                continue;
            } else {
                if (inNumber) {
                    tokens.add(sb.toString());
                    sb.setLength(0);
                    inNumber = false;
                }
                tokens.add(String.valueOf(c));
            }
        }
        if (inNumber) {
            tokens.add(sb.toString());
        }
        return tokens;
    }

    private static Node parse(List<String> tokens) {
        Deque<Node> values = new ArrayDeque<>();
        Deque<Character> ops = new ArrayDeque<>();
        for (String token : tokens) {
            char c = token.charAt(0);
            if (Character.isDigit(c)) {
                values.push(new NumberNode(Integer.parseInt(token)));
            } else if (c == '(') {
                ops.push(c);
            } else if (c == ')') {
                while (!ops.peek().equals('(')) {
                    applyOp(values, ops.pop());
                }
                ops.pop();
            } else {
                while (!ops.isEmpty() && hasPrecedence(ops.peek(), c)) {
                    applyOp(values, ops.pop());
                }
                ops.push(c);
            }
        }
        while (!ops.isEmpty()) {
            applyOp(values, ops.pop());
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

    private static void applyOp(Deque<Node> values, char op) {
        Node b = values.pop();
        Node a = values.pop();
        switch (op) {
            case '+':
                values.push(new BinaryNode('+', a, b));
                break;
            case '-':
                values.push(new BinaryNode('-', a, b));
                break;
            case '*':
                values.push(new BinaryNode('*', a, b));
                break;
            case '/':
                values.push(new BinaryNode('/', a, b));
                break;
        }
    }

    private static class Node {
        abstract int evaluate();
    }

    private static class NumberNode extends Node {
        final int value;

        NumberNode(int value) {
            this.value = value;
        }

        @Override
        int evaluate() {
            return value;
        }
    }

    private static class BinaryNode extends Node {
        final char op;
        final Node left;
        final Node right;

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
                    throw new IllegalArgumentException("Unsupported operation: " + op);
            }
        }
    }
}