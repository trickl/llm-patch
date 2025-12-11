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
        Object value;

        Token(String type, Object value) {
            this.type = type;
            this.value = value;
        }
    }

    private static class Lexer {
        List<Token> tokens;

        Lexer(String expression) {
            tokens = new ArrayList<>();
            tokenize(expression);
        }

        void tokenize(String expression) {
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

        void addToken(String token) {
            if (!token.isEmpty()) {
                tokens.add(new Token("NUMBER", Integer.parseInt(token)));
            }
        }
    }

    private static class Parser {
        List<Token> tokens;
        Stack<Integer> stack;

        Parser(List<Token> tokens) {
            this.tokens = tokens;
            this.stack = new Stack<>();
        }

        int parse() {
            return parseExpression();
        }

        int parseExpression() {
            int left = parseTerm();
            while (true) {
                if (tokens.get(0).type.equals("PLUS")) {
                    tokens.remove(0);
                    int right = parseTerm();
                    if (right == Integer.MIN_VALUE) {
                        throw new RuntimeException("Malformed expression");
                    }
                    return left + right;
                } else if (tokens.get(0).type.equals("MINUS")) {
                    tokens.remove(0);
                    int right = parseTerm();
                    if (right == Integer.MIN_VALUE) {
                        throw new RuntimeException("Malformed expression");
                    }
                    return left - right;
                } else {
                    break;
                }
            }
            return left;
        }

        int parseTerm() {
            int left = parseFactor();
            while (true) {
                if (tokens.get(0).type.equals("MULTIPLY")) {
                    tokens.remove(0);
                    int right = parseFactor();
                    if (right == Integer.MIN_VALUE) {
                        throw new RuntimeException("Malformed expression");
                    }
                    return left * right;
                } else if (tokens.get(0).type.equals("DIVIDE")) {
                    tokens.remove(0);
                    int right = parseFactor();
                    if (right == Integer.MIN_VALUE) {
                        throw new RuntimeException("Malformed expression");
                    }
                    if (right == 0) {
                        return Integer.MIN_VALUE;
                    }
                    return left / right;
                } else {
                    break;
                }
            }
            return left;
        }

        int parseFactor() {
            if (tokens.get(0).type.equals("MINUS")) {
                tokens.remove(0);
                int value = parseFactor();
                if (value == Integer.MIN_VALUE) {
                    throw new RuntimeException("Malformed expression");
                }
                return -value;
            } else if (!tokens.get(0).type.equals("NUMBER")) {
                throw new RuntimeException("Malformed expression");
            }
            return tokens.remove(0).value.intValue();
        }
    }

    private static class Evaluator {
        int evaluate(int left, int right) {
            return left + right;
        }

        int evaluate(int left, int right, int divisor) {
            if (divisor == 0) {
                return Integer.MIN_VALUE;
            }
            return (int) ((long) left * right / divisor);
        }
    }

    private int evaluate(String expression) {
        Lexer lexer = new Lexer(expression);
        Parser parser = new Parser(lexer.tokens);
        Evaluator evaluator = new Evaluator();
        return parser.parse();
    }
}