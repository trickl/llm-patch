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
                            int endPos = pos + 1;
                            while (endPos < expression.length() && Character.isDigit(expression.charAt(endPos)))
                                ++endPos;
                            yield(expression.substring(pos, endPos));
                            pos = endPos;
                            break;
                        } else if ("+-*/(). ".indexOf(expression.charAt(pos)) != -1) {
                            int endPos = pos + 1;
                            while (endPos < expression.length() && "+-*/(). ".indexOf(expression.charAt(endPos)) == -1)
                                ++endPos;
                            yield(expression.substring(pos, endPos));
                            pos = endPos;
                            break;
                        }
                        ++pos;
                    }
                    return false;
                }

                @Override
                public String next() {
                    throw new NoSuchElementException();
                }
            };
        }
    }

    private static class Parser implements Iterable<Operator> {

        private final Tokenizer tokenizer;
        private int pos = 0;

        public Parser(Tokenizer tokenizer) {
            this.tokenizer = tokenizer;
        }

        @Override
        public Iterator<Operator> iterator() {
            return new Iterator<>() {
                @Override
                public boolean hasNext() {
                    while (pos < tokenizer.iterator().iterator().nextLength()) {
                        if ("+-*/(). ".indexOf(tokenizer.iterator().iterator().next().charAt(0)) != -1) {
                            int endPos = pos + 1;
                            while (endPos < tokenizer.iterator().iterator().nextLength() && "+-*/(). ".indexOf(tokenizer.iterator().iterator().next().charAt(endPos)) == -1)
                                ++endPos;
                            yield(new Operator(tokenizer.iterator().iterator().next(), endPos - pos));
                            pos = endPos;
                            break;
                        } else if (Character.isDigit(tokenizer.iterator().iterator().next().charAt(0))) {
                            int endPos = pos + 1;
                            while (endPos < tokenizer.iterator().iterator().nextLength() && Character.isDigit(tokenizer.iterator().iterator().next().charAt(endPos)))
                                ++endPos;
                            yield(new Number(tokenizer.iterator().iterator().next(), endPos - pos));
                            pos = endPos;
                        }
                        ++pos;
                    }
                    return false;
                }

                @Override
                public Operator next() {
                    throw new NoSuchElementException();
                }
            };
        }
    }

    private static class Evaluator {

        private final Map<Operator, Operation> operations;

        public Evaluator() {
            operations = new HashMap<>();
            operations.put(new Operator("+", 1), (a, b) -> a + b);
            operations.put(new Operator("-", 1), (a, b) -> a - b);
            operations.put(new Operator("*", 2), (a, b) -> a * b);
            operations.put(new Operator("/", 2), (a, b) -> a / b);
        }

        public int evaluate(Operator operator) {
            return operations.get(operator).apply();
        }
    }

    private enum Operator {
        PLUS("+"),
        MINUS("-"),
        STAR("*"),
        DIVIDE("/");

        private final char symbol;
        private final int precedence;

        Operator(char symbol, int precedence) {
            this.symbol = symbol;
            this.precedence = precedence;
        }

        public char getSymbol() {
            return symbol;
        }
    }

    private enum Operation {

        ADDITION((a, b) -> a + b),
        SUBTRACTION((a, b) -> a - b),
        MULTIPLICATION((a, b) -> a * b),
        DIVISION((a, b) -> a / b);

        private final BinaryOperator operation;

        Operation(BinaryOperator operation) {
            this.operation = operation;
        }

        public int apply() {
            return (int) operation.apply(0, 0);
        }
    }

    private interface BinaryOperator {

        int apply(int a, int b);
    }
}