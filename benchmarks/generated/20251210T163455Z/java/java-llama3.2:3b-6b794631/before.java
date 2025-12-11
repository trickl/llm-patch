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
            return new Iterator<>() {
                @Override
                public boolean hasNext() {
                    while (pos < expression.length()) {
                        if (Character.isDigit(expression.charAt(pos))) {
                            pos++;
                            return true;
                        }
                        if (expression.charAt(pos) == '(' || expression.charAt(pos) == ')') {
                            pos++;
                            return true;
                        }
                        if (expression.charAt(pos) == '+' || expression.charAt(pos) == '-' || expression.charAt(pos) == '*' || expression.charAt(pos) == '/') {
                            int endPos = findNextNonDigit(expression, pos);
                            String token = expression.substring(pos, endPos + 1);
                            pos = endPos + 1;
                            return true;
                        }
                    }
                    return false;
                }

                @Override
                public String next() {
                    throw new NoSuchElementException();
                }
            };
        }

        private int findNextNonDigit(String expression, int pos) {
            for (int i = pos; i < expression.length(); i++) {
                if (!Character.isDigit(expression.charAt(i))) {
                    return i;
                }
            }
            throw new RuntimeException("Invalid input");
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
            return new Iterator<>() {
                @Override
                public boolean hasNext() {
                    while (pos < tokenizer.iterator().iterator().next().length()) {
                        if (Character.isDigit(tokenizer.expression.charAt(pos))) {
                            pos++;
                            return true;
                        }
                        if (tokenizer.expression.charAt(pos) == '(' || tokenizer.expression.charAt(pos) == ')') {
                            pos++;
                            return true;
                        }
                        if (tokenizer.expression.charAt(pos) == '+' || tokenizer.expression.charAt(pos) == '-' || tokenizer.expression.charAt(pos) == '*' || tokenizer.expression.charAt(pos) == '/') {
                            int endPos = findNextNonDigit(tokenizer.expression, pos);
                            String token = tokenizer.expression.substring(pos, endPos + 1);
                            pos = endPos + 1;
                            return true;
                        }
                    }
                    return false;
                }

                @Override
                public Integer next() {
                    throw new NoSuchElementException();
                }
            };
        }

        private int findNextNonDigit(String expression, int pos) {
            for (int i = pos; i < expression.length(); i++) {
                if (!Character.isDigit(expression.charAt(i))) {
                    return i;
                }
            }
            throw new RuntimeException("Invalid input");
        }
    }

    private static class Evaluator {

        public int evaluate(Tokenizer tokenizer) {
            Parser parser = new Parser(tokenizer);
            List<Integer> numbers = new ArrayList<>();
            Stack<Integer> operators = new Stack<>();

            while (parser.iterator().hasNext()) {
                String token = parser.next();
                if (!Character.isDigit(token.charAt(0))) {
                    switch (token) {
                        case "+":
                            int num2 = numbers.remove(numbers.size() - 1);
                            int num1 = numbers.remove(numbers.size() - 1);
                            numbers.add(num1 + num2);
                            break;
                        case "-":
                            int num3 = numbers.remove(numbers.size() - 1);
                            int num4 = numbers.remove(numbers.size() - 1);
                            numbers.add(num4 - num3);
                            break;
                        case "*":
                            int num5 = numbers.remove(numbers.size() - 1);
                            int num6 = numbers.remove(numbers.size() - 1);
                            numbers.add(num5 * num6);
                            break;
                        case "/":
                            int num7 = numbers.remove(numbers.size() - 1);
                            int num8 = numbers.remove(numbers.size() - 1);
                            if (num8 == 0) {
                                throw new RuntimeException("Division by zero");
                            }
                            numbers.add(num7 / num8);
                            break;
                        case "(":
                            operators.push(Integer.parseInt(token));
                            break;
                        default:
                            numbers.add(Integer.parseInt(token));
                    }
                } else {
                    numbers.add(Integer.parseInt(token));
                }
            }

            while (!operators.isEmpty()) {
                int operator = operators.pop();
                int operand2 = numbers.remove(numbers.size() - 1);
                int operand1 = numbers.remove(numbers.size() - 1);

                switch (operator) {
                    case '+':
                        numbers.add(operand1 + operand2);
                        break;
                    case '-':
                        numbers.add(operand2 - operand1);
                        break;
                    case '*':
                        numbers.add(operand1 * operand2);
                        break;
                    case '/':
                        if (operand2 == 0) {
                            throw new RuntimeException("Division by zero");
                        }
                        numbers.add(operand1 / operand2);
                        break;
                }
            }

            return numbers.get(0);
        }
    }

}