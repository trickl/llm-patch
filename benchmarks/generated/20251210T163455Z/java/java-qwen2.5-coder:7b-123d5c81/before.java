import java.util.*;
import java.util.function.BiFunction;
import java.util.stream.Collectors;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }

    public static int evaluate(String expression) {
        List<String> tokens = tokenize(expression);
        return parseAndEvaluate(tokens);
    }

    private static List<String> tokenize(String expression) {
        return Arrays.stream(expression.split("\\s+"))
                .flatMap(token -> token.matches("-?\\d+") ? Stream.of(token) : Stream.of(token.split("(?<=[-+*/()])|(?=[-+*/()])")))
                .collect(Collectors.toList());
    }

    private static int parseAndEvaluate(List<String> tokens) {
        Deque<Integer> values = new ArrayDeque<>();
        Deque<Character> operators = new ArrayDeque<>();

        for (String token : tokens) {
            if (token.matches("-?\\d+")) {
                values.push(Integer.parseInt(token));
            } else if ("(".equals(token)) {
                operators.push('(');
            } else if (")".equals(token)) {
                while (!operators.peek().equals('(')) {
                    applyOperation(values, operators.pop());
                }
                operators.pop();
            } else {
                while (!operators.isEmpty() && precedence(operators.peek()) >= precedence(token.charAt(0))) {
                    applyOperation(values, operators.pop());
                }
                operators.push(token.charAt(0));
            }
        }

        while (!operators.isEmpty()) {
            applyOperation(values, operators.pop());
        }

        return values.pop();
    }

    private static void applyOperation(Deque<Integer> values, char operator) {
        int b = values.pop();
        int a = values.pop();
        values.push(apply(a, b, operator));
    }

    private static int apply(int a, int b, char operator) {
        switch (operator) {
            case '+': return a + b;
            case '-': return a - b;
            case '*': return a * b;
            case '/': return a / b;
            default: throw new IllegalArgumentException("Unsupported operator: " + operator);
        }
    }

    private static int precedence(char operator) {
        switch (operator) {
            case '+':
            case '-': return 1;
            case '*':
            case '/': return 2;
            default: return -1;
        }
    }
}