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
        return parse(tokens);
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
                .map(token -> token.equals("-") && (tokens.isEmpty() || tokens.get(tokens.size() - 1).matches("[\\d)]")))
                        ? "(-1)" : token)
                .collect(Collectors.toList());
    }

    private static int parse(List<String> tokens) {
        Deque<Integer> values = new ArrayDeque<>();
        Deque<Character> ops = new ArrayDeque<>();
        for (String token : tokens) {
            if (token.matches("\\d+")) {
                values.push(Integer.parseInt(token));
            } else if (token.equals("(")) {
                ops.push(token.charAt(0));
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

    private static int applyOp(char op, int b, int a) {
        switch (op) {
            case '+':
                return a + b;
            case '-':
                return a - b;
            case '*':
                return a * b;
            case '/':
                if (b == 0) throw new ArithmeticException("Cannot divide by zero");
                return a / b;
        }
        return 0;
    }

    private static class Tokenizer {
        // Helper class for tokenization can be added here if needed
    }

    private static class Parser {
        // Helper class for parsing can be added here if needed
    }

    private static class Evaluator {
        // Helper class for evaluation can be added here if needed
    }
}