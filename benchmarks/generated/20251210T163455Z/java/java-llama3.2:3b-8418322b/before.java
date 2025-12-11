import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }

    public static int evaluate(String expression) {
        return new ExpressionEvaluatorImpl().evaluate(expression);
    }

    private static class ExpressionEvaluatorImpl implements ExpressionEvaluatorInterface {
        @Override
        public int evaluate(String expression) {
            Tokenizer tokenizer = new Tokenizer();
            List<Token> tokens = tokenizer.tokenize(expression);

            Parser parser = new Parser(tokens);
            return parser.parse();
        }
    }

    private interface ExpressionEvaluatorInterface {
        int evaluate(String expression);
    }

    private static class Tokenizer implements ExpressionTokenizerInterface {
        @Override
        public List<Token> tokenize(String expression) {
            List<Token> tokens = new ArrayList<>();
            StringBuilder currentNumber = new StringBuilder();

            for (char c : expression.toCharArray()) {
                if (Character.isDigit(c)) {
                    currentNumber.append(c);
                } else if (c == '(' || c == ')') {
                    tokens.add(new Token(c, Token.Type.LEFT_PAREN));
                    tokens.add(new Token(c, Token.Type.RIGHT_PAREN));
                } else if (c == '+' || c == '-' || c == '*' || c == '/') {
                    tokens.add(new Token(c, Token.Type.OPERATOR));
                }
            }

            if (!currentNumber.isEmpty()) {
                tokens.add(new Token(currentNumber.toString(), Token.Type.NUMBER));
            }

            return tokens;
        }
    }

    private static class Parser implements ExpressionParserInterface {
        private List<Token> tokens;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
        }

        @Override
        public int parse() {
            return parseExpression();
        }

        private int parseExpression() {
            int leftOperand = parseTerm();

            while (true) {
                if (tokens.get(0).type == Token.Type.OPERATOR && tokens.get(0).value.equals("+") || tokens.get(0).type == Token.Type.OPERATOR && tokens.get(0).value.equals("-")) {
                    tokens.remove(0);
                    int rightOperand = parseTerm();
                    return leftOperand + rightOperand;
                } else if (tokens.get(0).type == Token.Type.OPERATOR && tokens.get(0).value.equals("*") || tokens.get(0).type == Token.Type.OPERATOR && tokens.get(0).value.equals("/")) {
                    tokens.remove(0);
                    int rightOperand = parseTerm();
                    return leftOperand * rightOperand;
                } else {
                    break;
                }
            }

            return leftOperand;
        }

        private int parseTerm() {
            int leftOperand = parseFactor();

            while (true) {
                if (tokens.get(0).type == Token.Type.OPERATOR && tokens.get(0).value.equals("*") || tokens.get(0).type == Token.Type.OPERATOR && tokens.get(0).value.equals("/")) {
                    tokens.remove(0);
                    int rightOperand = parseFactor();
                    return leftOperand * rightOperand;
                } else if (tokens.get(0).type == Token.Type.OPERATOR && tokens.get(0).value.equals("-") && tokens.size() > 1) {
                    tokens.remove(0);
                    int rightOperand = parseFactor();
                    return -leftOperand + rightOperand;
                } else {
                    break;
                }
            }

            return leftOperand;
        }

        private int parseFactor() {
            if (tokens.get(0).type == Token.Type.LEFT_PAREN) {
                tokens.remove(0);
                int result = parseExpression();
                tokens.add(new Token("(", Token.Type.LEFT_PAREN));
                return result;
            } else if (tokens.get(0).type == Token.Type.NUMBER) {
                tokens.remove(0);
                return Integer.parseInt(tokens.get(0).value);
            } else if (tokens.get(0).type == Token.Type.MINUS && tokens.size() > 1) {
                tokens.remove(0);
                int result = parseFactor();
                tokens.add(new Token("-", Token.Type.MINUS));
                return -result;
            }

            throw new RuntimeException("Invalid token");
        }
    }

    private static class Token implements Comparable<Token> {
        String value;
        Type type;

        public Token(String value, Type type) {
            this.value = value;
            this.type = type;
        }

        @Override
        public int compareTo(Token other) {
            return value.compareTo(other.value);
        }
    }

    private enum Type {
        NUMBER,
        OPERATOR,
        LEFT_PAREN,
        RIGHT_PAREN,
        MINUS
    }
}