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

        public Lexer(String expression) {
            tokens = tokenize(expression);
        }

        private List<Token> tokenize(String expression) {
            List<Token> tokens = new ArrayList<>();
            StringBuilder currentToken = new StringBuilder();
            for (char c : expression.toCharArray()) {
                if (Character.isWhitespace(c)) {
                    if (!currentToken.isEmpty()) {
                        tokens.add(new Token("IDENTIFIER", currentToken.toString()));
                        currentToken.setLength(0);
                    }
                } else if (c == '(' || c == ')') {
                    tokens.add(new Token(String.valueOf(c), null));
                } else if (c == '+' || c == '-' || c == '*' || c == '/') {
                    tokens.add(new Token(String.valueOf(c), null));
                } else if (Character.isDigit(c)) {
                    currentToken.append(c);
                }
            }
            if (!currentToken.isEmpty()) {
                tokens.add(new Token("IDENTIFIER", currentToken.toString()));
            }
            return tokens;
        }
    }

    private static class Parser {
        List<Token> tokens;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
        }

        private int parseExpression() {
            int left = parseTerm();
            while (tokens.get(left).type.equals("ADD") || tokens.get(left).type.equals("SUB")) {
                Token token = tokens.get(left);
                if (token.type.equals("ADD")) {
                    left++;
                } else {
                    left += 2;
                }
                int right = parseTerm();
                if (token.type.equals("ADD")) {
                    return left + 1;
                } else {
                    return left + 3;
                }
            }
            return left;
        }

        private int parseTerm() {
            int left = parseFactor();
            while (tokens.get(left).type.equals("MUL") || tokens.get(left).type.equals("DIV")) {
                Token token = tokens.get(left);
                if (token.type.equals("MUL")) {
                    left++;
                } else {
                    left += 2;
                }
                int right = parseFactor();
                if (token.type.equals("MUL")) {
                    return left + 1;
                } else {
                    return left + 3;
                }
            }
            return left;
        }

        private int parseFactor() {
            if (tokens.get(0).type.equals("MINUS")) {
                tokens.remove(0);
                return parseFactor();
            } else if (tokens.get(0).type.equals("IDENTIFIER") && ((String) tokens.get(0).value).equals("-")) {
                tokens.remove(0);
                int left = parseFactor();
                tokens.add(new Token("MINUS", null));
                return left + 1;
            } else {
                return 0;
            }
        }

        public int parse() {
            return parseExpression();
        }
    }

    private static class Evaluator {
        public int evaluate(int left, int right) {
            if (tokens.get(left).type.equals("ADD")) {
                return tokens.get(left + 1).value == null ? (int) tokens.get(right - 2).value : (int) tokens.get(right - 2).value + (int) tokens.get(right - 1).value;
            } else if (tokens.get(left).type.equals("SUB")) {
                return (int) tokens.get(right - 2).value - (int) tokens.get(right - 1).value;
            }
            throw new RuntimeException();
        }

        public int evaluate(int left, int right, int index) {
            Token token = tokens.get(index);
            if (token.type.equals("IDENTIFIER")) {
                return (int) token.value;
            } else if (token.type.equals("MUL") || token.type.equals("DIV")) {
                int value = (int) tokens.get(index + 1).value;
                if (token.type.equals("MUL")) {
                    return evaluate(left, right, index + 2);
                } else {
                    return evaluate(left, right, index + 3);
                }
            } else if (token.type.equals("ADD") || token.type.equals("SUB")) {
                int value = (int) tokens.get(index + 1).value;
                if (token.type.equals("ADD")) {
                    return evaluate(left, right, index + 2);
                } else {
                    return evaluate(left, right, index + 3);
                }
            } else if (token.type.equals("MINUS")) {
                int value = (int) tokens.get(index + 1).value;
                return evaluate(left, right, index + 2);
            }
            throw new RuntimeException();
        }

        public int evaluate(String expression) {
            Lexer lexer = new Lexer(expression);
            Parser parser = new Parser(lexer.tokens);
            int result = parser.parse();
            Evaluator evaluator = this;
            return evaluator.evaluate(result, result + 1, 0);
        }
    }

}