import java.util.*;

public class ExpressionEvaluator {

    public static int evaluate(String expression) {
        return new Tokenizer().tokenize(expression).parse().evaluate();
    }

    private static class Tokenizer {
        private List<Token> tokens = new ArrayList<>();

        public void tokenize(String expression) {
            String[] parts = expression.split("\\s+");
            for (String part : parts) {
                if (!part.isEmpty()) {
                    if (Character.isDigit(part.charAt(0))) {
                        tokens.add(new NumberToken(Integer.parseInt(part)));
                    } else if (part.equals("+") || part.equals("-")) {
                        tokens.add(new OperatorToken(part));
                    } else if (part.equals("*") || part.equals("/")) {
                        tokens.add(new OperatorToken(part));
                    } else if (part.charAt(0) == '(') {
                        tokens.add(new LeftParenthesisToken());
                    } else if (part.charAt(0) == ')') {
                        tokens.add(new RightParenthesisToken());
                    }
                }
            }
        }

        public Parser parse() {
            return new Parser(tokens);
        }
    }

    private static class Parser {
        private List<Token> tokens;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
        }

        public int evaluate() {
            return evaluateExpression(0, tokens.size());
        }

        private int evaluateExpression(int start, int end) {
            if (start >= end) {
                throw new RuntimeException("Malformed expression");
            }
            Token token = tokens.get(start);
            switch (token.type()) {
                case NUMBER:
                    return (int) token.value();
                case LEFT_PAREN:
                    start++;
                    int result = evaluateExpression(start, end);
                    if (tokens.get(start).type() != RIGHT_PAREN) {
                        throw new RuntimeException("Malformed expression");
                    }
                    start++;
                    return result;
                case MINUS:
                    return -evaluateExpression(start + 1, end);
                default:
                    int left = evaluateExpression(start + 1, end);
                    Token operatorToken = tokens.get(start + 1);
                    switch (operatorToken.type()) {
                        case PLUS:
                            return left + evaluateExpression(start + 2, end);
                        case TIMES:
                            return left * evaluateExpression(start + 2, end);
                        default:
                            throw new RuntimeException("Malformed expression");
                    }
            }
        }
    }

    private static class Token {
        public enum Type { NUMBER, LEFT_PAREN, RIGHT_PAREN, MINUS, PLUS, TIMES };

        private final Type type;
        private Object value;

        public Token(Type type) {
            this.type = type;
        }

        public Token(Number number) {
            this.type = Type.NUMBER;
            this.value = number;
        }

        public Token() {
            this.type = Type.LEFT_PAREN;
        }

        public Token(String s) {
            this.type = Type.RIGHT_PAREN;
            this.value = s;
        }
    }

    private static class OperatorToken extends Token {
        public OperatorToken(String operator) {
            super(Type.PLUS, Type.MINUS, Type.TIMES);
            this.value = operator;
        }
    }

    private static class NumberToken extends Token {
        public NumberToken(Number number) {
            super(Type.NUMBER);
            this.value = number;
        }
    }

    private static class LeftParenthesisToken extends Token {
        public LeftParenthesisToken() {
            super(Type.LEFT_PAREN);
        }
    }

    private static class RightParenthesisToken extends Token {
        public RightParenthesisToken(String s) {
            super(Type.RIGHT_PAREN, s);
        }
    }

    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }
}