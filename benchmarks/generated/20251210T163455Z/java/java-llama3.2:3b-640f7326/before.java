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

    private static class Tokenizer {
        private final List<String> tokens;

        public Tokenizer(String expression) {
            this.tokens = tokenize(expression);
        }

        private List<String> tokenize(String expression) {
            List<String> tokens = new ArrayList<>();
            StringBuilder currentToken = new StringBuilder();

            for (char c : expression.toCharArray()) {
                if (Character.isWhitespace(c)) {
                    if (!currentToken.isEmpty()) {
                        tokens.add(currentToken.toString());
                        currentToken.setLength(0);
                    }
                } else {
                    currentToken.append(c);
                }
            }

            if (!currentToken.isEmpty()) {
                tokens.add(currentToken.toString());
            }

            return tokens;
        }

        public List<String> getTokens() {
            return tokens;
        }
    }

    private static class Parser {
        private final List<String> tokens;

        public Parser(List<String> tokens) {
            this.tokens = tokens;
        }

        public Expression parseExpression() {
            return parseExpression(0);
        }

        private Expression parseExpression(int index) {
            Expression left = parseTerm(index);

            while (index < tokens.size()) {
                char op = tokens.get(index).charAt(0);

                if (op == '(') {
                    index++;
                    Expression right = parseExpression(index);
                    index++; // consume ')'
                    return new BinaryOp(left, op, right);
                } else if (op == '-') {
                    index++;
                    return new UnaryOp(tokens.get(index), left);
                } else if (isOperator(op)) {
                    break;
                }
            }

            return left;
        }

        private Expression parseTerm(int index) {
            Expression left = parseFactor(index);

            while (index < tokens.size()) {
                char op = tokens.get(index).charAt(0);

                if (op == '*' || op == '/') {
                    index++;
                    return new BinaryOp(left, op, parseFactor(index));
                } else if (isOperator(op)) {
                    break;
                }
            }

            return left;
        }

        private Expression parseFactor(int index) {
            if (!Character.isDigit(tokens.get(index).charAt(0))) {
                throw new RuntimeException("Invalid token: " + tokens.get(index));
            }

            int end = index + 1;

            while (end < tokens.size() && Character.isDigit(tokens.get(end).charAt(0))) {
                end++;
            }

            return new Literal(Integer.parseInt(tokens.get(index), 10));
        }

        private boolean isOperator(char op) {
            return op == '+' || op == '-';
        }
    }

    private static class Evaluator {
        public int evaluate(Expression expression) {
            return evaluate(expression, 0);
        }

        private int evaluate(Expression expression, int index) {
            Expression left = expression.getLeft();

            if (left instanceof BinaryOp binaryOp) {
                char op = binaryOp.getOperator();
                Expression right = binaryOp.getRight();

                switch (op) {
                    case '+':
                        return evaluate(right, index + 1) + evaluate(left, index);
                    case '-':
                        return evaluate(right, index + 1) - evaluate(left, index);
                    case '*':
                        return evaluate(right, index + 1) * evaluate(left, index);
                    case '/':
                        int rightValue = evaluate(right, index + 1);
                        if (rightValue == 0) {
                            throw new RuntimeException("Division by zero");
                        }
                        return evaluate(left, index) / rightValue;
                }
            } else if (left instanceof UnaryOp unaryOp) {
                char op = unaryOp.getOperator();
                Expression right = unaryOp.getRight();

                switch (op) {
                    case '-':
                        return -evaluate(right, index + 1);
                }
            }

            throw new RuntimeException("Invalid expression");
        }
    }

    private static class Literal implements Expression {
        private final int value;

        public Literal(int value) {
            this.value = value;
        }

        @Override
        public Object getLeft() {
            return value;
        }

        @Override
        public Object getRight() {
            return null;
        }
    }

    private static class BinaryOp implements Expression {
        private final Expression left;
        private final char operator;
        private final Expression right;

        public BinaryOp(Expression left, char operator, Expression right) {
            this.left = left;
            this.operator = operator;
            this.right = right;
        }

        @Override
        public Object getLeft() {
            return left;
        }

        @Override
        public Object getRight() {
            return right;
        }
    }

    private static class UnaryOp implements Expression {
        private final char operator;
        private final Expression right;

        public UnaryOp(char operator, Expression right) {
            this.operator = operator;
            this.right = right;
        }

        @Override
        public Object getLeft() {
            return null;
        }

        @Override
        public Object getRight() {
            return right;
        }
    }
}