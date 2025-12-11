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

    private static class Token {
        String type;
        double value;

        public Token(String type, double value) {
            this.type = type;
            this.value = value;
        }
    }

    private static class Lexer {
        List<Token> tokens;

        public Lexer(String expression) {
            tokens = new ArrayList<>();
            tokenize(expression);
        }

        private void tokenize(String expression) {
            StringBuilder currentToken = new StringBuilder();
            for (char c : expression.toCharArray()) {
                if (Character.isWhitespace(c)) {
                    if (currentToken.length() > 0) {
                        addToken(currentToken.toString());
                        currentToken.setLength(0);
                    }
                } else if ("+-*/(). ".indexOf(c) != -1) {
                    if (currentToken.length() > 0) {
                        addToken(currentToken.toString());
                        currentToken.setLength(0);
                    }
                    tokens.add(new Token(String.valueOf(c), c));
                } else {
                    currentToken.append(c);
                }
            }
            if (currentToken.length() > 0) {
                addToken(currentToken.toString());
            }
        }

        private void addToken(String token) {
            if (!token.isEmpty()) {
                tokens.add(new Token(token, token.charAt(0)));
            }
        }
    }

    private static class Parser {
        List<Token> tokens;
        Stack<Double> stack;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
            stack = new Stack<>();
        }

        public double parse() {
            return parseExpression();
        }

        private double parseExpression() {
            double left = parseTerm();
            while (true) {
                if (tokens.get(0).type.equals("+") || tokens.get(0).type.equals("-")) {
                    Token operator = tokens.remove(0);
                    double right = parseTerm();
                    if (operator.type.equals("+")) {
                        stack.push(left + right);
                    } else {
                        stack.push(left - right);
                    }
                } else {
                    break;
                }
            }
            return stack.pop();
        }

        private double parseTerm() {
            double left = parseFactor();
            while (true) {
                if (tokens.get(0).type.equals("*") || tokens.get(0).type.equals("/")) {
                    Token operator = tokens.remove(0);
                    double right = parseFactor();
                    if (operator.type.equals("*")) {
                        stack.push(left * right);
                    } else {
                        stack.push(left / right);
                    }
                } else {
                    break;
                }
            }
            return stack.pop();
        }

        private double parseFactor() {
            if (tokens.get(0).type.equals("-")) {
                Token operator = tokens.remove(0);
                double value = parseFactor();
                stack.push(-value);
            } else if (!tokens.get(0).type.isEmpty()) {
                return Double.parseDouble(tokens.remove(0).value);
            }
            return 1.0;
        }
    }

    public int evaluate(String expression) {
        Lexer lexer = new Lexer(expression);
        Parser parser = new Parser(lexer.tokens);
        return (int) parser.parse();
    }
}