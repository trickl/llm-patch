import java.util.*;

public class ExpressionEvaluator {

    public static int evaluate(String expression) {
        return new Tokenizer().tokenize(expression).parse().evaluate();
    }

    private static class Tokenizer {
        List<Token> tokens = tokenize(expression);

        private List<Token> tokenize(String expression) {
            List<String> operators = Arrays.asList("+", "-", "*", "/");
            List<String> operands = new ArrayList<>();
            StringBuilder currentOperand = new StringBuilder();

            for (char c : expression.toCharArray()) {
                if (Character.isDigit(c)) {
                    currentOperand.append(c);
                } else if (operators.contains(String.valueOf(c))) {
                    if (!currentOperand.isEmpty()) {
                        operands.add(currentOperand.toString());
                        currentOperand.setLength(0);
                    }
                    operands.add(new Token(c, Token.Type.OPERATOR));
                }
            }

            if (!currentOperand.isEmpty()) {
                operands.add(currentOperand.toString());
            }

            List<Token> result = new ArrayList<>();
            for (String operand : operands) {
                if (operand.startsWith("-")) {
                    result.add(new Token(operand.substring(1), Token.Type.UNARY_MINUS));
                } else {
                    result.add(new Token(operand, Token.Type.OPERAND));
                }
            }

            return result;
        }
    }

    private static class Parser {
        List<Token> tokens = new ArrayList<>();
        int index = 0;

        boolean parse() {
            if (index >= tokens.size()) {
                throw new RuntimeException("Malformed expression");
            }

            Token token = tokens.get(index);
            index++;

            switch (token.type) {
                case OPERAND:
                    return evaluateOperand();
                case UNARY_MINUS:
                    return evaluateUnaryMinus();
                default:
                    throw new RuntimeException("Unsupported token type: " + token.type);
            }
        }

        private boolean evaluateOperand() {
            if (!tokens.get(index).type.equals(Token.Type.OPERATOR)) {
                throw new RuntimeException("Malformed expression");
            }

            index++;
            Token operator = tokens.get(index);
            index++;

            return parse() * parse();
        }

        private boolean evaluateUnaryMinus() {
            if (!tokens.get(index).type.equals(Token.Type.OPERAND)) {
                throw new RuntimeException("Malformed expression");
            }

            index++;
            int operand = Integer.parseInt(tokens.get(index).value);

            switch (operator) {
                case '+':
                    return -operand;
                case '-':
                    return operand;
                default:
                    throw new RuntimeException("Unsupported operator: " + operator);
            }
        }

        private Token getOperator() {
            if (!tokens.get(index).type.equals(Token.Type.OPERATOR)) {
                throw new RuntimeException("Malformed expression");
            }

            index++;
            return tokens.get(index);
        }

        private int parse() {
            if (index >= tokens.size()) {
                throw new RuntimeException("Malformed expression");
            }

            Token token = tokens.get(index);
            index++;

            switch (token.type) {
                case OPERAND:
                    return Integer.parseInt(token.value);
                case UNARY_MINUS:
                    return evaluateUnaryMinus();
                default:
                    throw new RuntimeException("Unsupported token type: " + token.type);
            }
        }
    }

    private static class Evaluator {
        int result = 0;

        void apply(Token token) {
            switch (token.type) {
                case OPERATOR:
                    switch (token.value) {
                        case '+':
                            result += parse();
                            break;
                        case '-':
                            result -= parse();
                            break;
                        case '*':
                            result *= parse();
                            break;
                        case '/':
                            if (parse() == 0) {
                                throw new ArithmeticException("Division by zero");
                            }
                            result /= parse();
                            break;
                    }
            }
        }

        int parse() {
            if (index >= tokens.size()) {
                return result;
            }

            Token token = tokens.get(index);
            index++;

            switch (token.type) {
                case OPERAND:
                    return Integer.parseInt(token.value);
                case UNARY_MINUS:
                    apply(new Token(token.value, Token.Type.UNARY_MINUS));
                    return parse();
                default:
                    throw new RuntimeException("Unsupported token type: " + token.type);
            }
        }

        void evaluate() {
            while (index < tokens.size()) {
                apply(tokens.get(index++));
            }
        }
    }

    private static class Token {
        String value;
        Token.Type type;

        public enum Type { OPERAND, OPERATOR, UNARY_MINUS };

        Token(String value, Type type) {
            this.value = value;
            this.type = type;
        }
    }

    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }
}