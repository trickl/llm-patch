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
        return tokens.stream()
.map(token -> token.equals("-") && (tokens.isEmpty() || tokens.get(tokens.size() - 1).matches("[\\(+-]")) ? "0-" : token)
                .collect(Collectors.toList());
    }

    private static Node parse(List<String> tokens) {
        Deque<Node> values = new ArrayDeque<>();
        Deque<Character> ops = new ArrayDeque<>();

        for (String token : tokens) {
            if (token.matches("[\\d]+")) {
                values.push(new NumberNode(Integer.parseInt(token)));
            } else if ("+-".contains(token)) {
                while (!ops.isEmpty() && precedence(ops.peek()) >= precedence(token.charAt(0))) {
                    applyOp(values, ops);
                }
                ops.push(token.charAt(0));
            } else if (token.equals("(")) {
                ops.push(token.charAt(0));
            } else if (token.equals(")")) {
                while (!ops.isEmpty() && ops.peek() != '(') {
                    applyOp(values, ops);
                }
                ops.pop();
            }
        }

        while (!ops.isEmpty()) {
            applyOp(values, ops);
        }

        return values.pop();
    }

    private static void applyOp(Deque<Node> values, Deque<Character> ops) {
        char op = ops.pop();
        Node b = values.pop();
        Node a = values.pop();
        values.push(new BinaryNode(a, b, op));
    }

    private static int precedence(char op) {
        if (op == '+' || op == '-') return 1;
        if (op == '*' || op == '/') return 2;
        return 0;
    }
}

interface Node {
    int evaluate();
}

class NumberNode implements Node {
    private final int value;

    public NumberNode(int value) {
        this.value = value;
    }

    @Override
    public int evaluate() {
        return value;
    }
}

class BinaryNode implements Node {
    private final Node left;
    private final Node right;
    private final char op;

    public BinaryNode(Node left, Node right, char op) {
        this.left = left;
        this.right = right;
        this.op = op;
    }

    @Override
    public int evaluate() {
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