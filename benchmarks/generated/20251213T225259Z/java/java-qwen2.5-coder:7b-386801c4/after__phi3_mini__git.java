import java.util.*;
import java.util.function.BiFunction;

public class ExpressionEvaluator {
    private static final Map<String, Integer> PRECEDENCE = new HashMap<>();
    private static final Set<String> OPERATORS = new HashSet<>();

    static {
        PRECEDENCE.put("+", 1);
        PRECEDENCE.put("-", 1);
        PRECEDENCE.put("*", 2);
        PRECEDENCE.put("/", 2);
        OPERATORS.addAll(PRECEDENCE.keySet());
    }

    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Should print 7
        System.out.println(evaluate("2 * 3 + 4")); // Should print 10
        System.out.println(evaluate("2 * (3 + 4)")); // Should print 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Should print 16
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
                if (OPERATORS.contains(String.valueOf(c)) || c == '(' || c == ')') {
                    tokens.add(String.valueOf(c));
                } else if (c == '-') {
                    if (tokens.isEmpty() || OPERATORS.contains(tokens.get(tokens.size() - 1))) {
                        sb.append(c);
                    } else {
                        tokens.add(sb.toString());
                        sb.setLength(0);
                        sb.append(c);
                    }
                }
            }
        }
        if (inNumber) {
            tokens.add(sb.toString());
        }
        return tokens;
    }

    private static Node parse(List<String> tokens) {
        Deque<Node> values = new ArrayDeque<>();
        Deque<String> ops = new ArrayDeque<>();
        for (String token : tokens) {
            if (Character.isDigit(token.charAt(0))) {
                values.push(new NumberNode(Integer.parseInt(token)));
            } else if (token.equals("(")) {
                ops.push(token);
            } else if (token.equals(")")) {
                while (!ops.peek().equals("(")) {
                    values.push(applyOp(ops.pop(), values.pop(), values.pop()));
                }
                ops.pop();
            } else {
                while (!ops.isEmpty() && PRECEDENCE.get(ops.peek()) >= PRECEDENCE.get(token)) {
                    values.push(applyOp(ops.pop(), values.pop(), values.pop()));
                }
                ops.push(token);
            }
        }
        while (!ops.isEmpty()) {
            values.push(applyOp(ops.pop(), values.pop(), values.pop()));
        }
        return values.pop();
    }

    private static Node applyOp(String op, Node b, Node a) {
        BiFunction<Integer, Integer, Integer> func;
        switch (op) {
            case "+":
                func = Integer::sum;
                break;
            case "-":
                func = (x, y) -> x - y;
                break;
            case "*":
                func = (x, y) -> x * y;
                break;
            case "/":
                func = (x, y) -> x / y;
                break;
            default:
                throw new IllegalArgumentException("Unknown operator: " + op);
        }
        return new NumberNode(func.apply(a.getValue(), b.getValue()));
    }

    private static abstract class Node {
        public abstract int evaluate();
    }

    private static class NumberNode extends Node {
        private final int value;

        public NumberNode(int value) {
            this.value = value;
        }

        @Override
        public int evaluate() {
            return value;
        }
    }
}