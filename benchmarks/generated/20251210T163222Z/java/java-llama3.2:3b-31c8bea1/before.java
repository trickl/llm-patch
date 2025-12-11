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
                        }
                        if (expression.charAt(pos) == '(' || expression.charAt(pos) == ')') {
                            int endPos = pos + 1;
                            while (endPos < expression.length() && (expression.charAt(endPos) != '(' && expression.charAt(endPos) != ')'))
                                ++endPos;
                            yield(expression.substring(pos, endPos));
                            pos = endPos;
                            break;
                        }
                        if (expression.charAt(pos) == '+' || expression.charAt(pos) == '-' || expression.charAt(pos) == '*' || expression.charAt(pos) == '/') {
                            int endPos = pos + 1;
                            while (endPos < expression.length() && (expression.charAt(endPos) != '+' && expression.charAt(endPos) != '-' && expression.charAt(endPos) != '*' && expression.charAt(endPos) != '/'))
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

    private static class Parser implements Iterable<Token> {

        private final Tokenizer tokenizer;
        private int pos = 0;

        public Parser(Tokenizer tokenizer) {
            this.tokenizer = tokenizer;
        }

        @Override
        public Iterator<Token> iterator() {
            return new Iterator<>() {
                @Override
                public boolean hasNext() {
                    while (pos < tokenizer.iterator().iterator().hasNext()) {
                        Token token = tokenizer.iterator().next();
                        if (token.matches("number")) {
                            pos++;
                            continue;
                        }
                        if (token.matches("(")) {
                            pos++;
                            continue;
                        }
                        yield(token);
                        pos++;
                        return true;
                    }
                    return false;
                }

                @Override
                public Token next() {
                    throw new NoSuchElementException();
                }
            };
        }
    }

    private static class Evaluator {

        private final Parser parser;

        public Evaluator(Parser parser) {
            this.parser = parser;
        }

        public int evaluate() {
            Stack<Integer> stack = new Stack<>();
            while (parser.iterator().hasNext()) {
                Token token = parser.next();
                if (token.matches("number")) {
                    stack.push(Integer.parseInt(token.value()));
                } else if (token.matches("+") || token.matches("-") || token.matches("*") || token.matches("/")) {
                    int operand2 = stack.pop();
                    int operand1 = stack.pop();
                    switch (token.value()) {
                        case "+":
                            stack.push(operand1 + operand2);
                            break;
                        case "-":
                            stack.push(operand1 - operand2);
                            break;
                        case "*":
                            stack.push(operand1 * operand2);
                            break;
                        case "/":
                            if (operand2 == 0) {
                                throw new ArithmeticException("Division by zero");
                            }
                            stack.push(operand1 / operand2);
                            break;
                    }
                } else if (token.matches("(")) {
                    Parser subParser = new Parser(tokenizer);
                    Token resultToken = subParser.next();
                    if (!resultToken.matches("+") && !resultToken.matches("-")) {
                        throw new RuntimeException("Expected a number or an operator after '('");
                    }
                    int operand2 = stack.pop();
                    int operand1 = stack.pop();
                    switch (resultToken.value()) {
                        case "+":
                            stack.push(operand1 + operand2);
                            break;
                        case "-":
                            stack.push(operand1 - operand2);
                            break;
                    }
                } else if (token.matches("-")) {
                    stack.push(-stack.pop());
                }
            }
            return stack.pop();
        }
    }

    private static class Token {

        public enum Type {
            NUMBER,
            OPERATOR,
            PARENTHESIS
        }

        private final Type type;
        private final String value;

        public Token(Type type, String value) {
            this.type = type;
            this.value = value;
        }

        public boolean matches(String regex) {
            return type == Type.NUMBER && value.matches(regex) ||
                   type == Type.OPERATOR && value.equals(regex);
        }
    }

}