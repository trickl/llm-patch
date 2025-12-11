import java.util.*;

public class ExpressionEvaluator {

    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }

    public static int evaluate(String expression) {
        Tokenizer tokenizer = new Tokenizer(expression);
        Parser parser = new Parser(tokenizer);
        return parser.parse();
    }

    private static class Tokenizer {

        private final String expression;
        private final List<Token> tokens;

        public Tokenizer(String expression) {
            this.expression = expression;
            tokens = tokenize(expression);
        }

        private List<Token> tokenize(String expression) {
            List<Token> tokens = new ArrayList<>();
            StringBuilder currentToken = new StringBuilder();
            for (char c : expression.toCharArray()) {
                if (Character.isWhitespace(c)) {
                    if (!currentToken.isEmpty()) {
                        tokens.add(new Token(currentToken.toString(), Token.Type.SPACE));
                        currentToken.setLength(0);
                    }
                } else if ("+-*/()".indexOf(c) != -1) {
                    if (!currentToken.isEmpty()) {
                        tokens.add(new Token(currentToken.toString(), Token.Type.OPERATOR));
                        currentToken.setLength(0);
                    }
                    tokens.add(new Token(String.valueOf(c), Token.Type.OPERATOR));
                } else if (Character.isDigit(c)) {
                    currentToken.append(c);
                } else {
                    throw new RuntimeException("Invalid character '" + c + "' in expression");
                }
            }
            if (!currentToken.isEmpty()) {
                tokens.add(new Token(currentToken.toString(), Token.Type.NUMBER));
            }
            return tokens;
        }

    }

    private static class Parser {

        private final List<Token> tokens;
        private int index;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
            this.index = 0;
        }

        public int parse() {
            return parseExpression();
        }

        private int parseExpression() {
            int result = parseTerm();
            while (index < tokens.size()) {
                Token token = tokens.get(index++);
                if (token.type == Token.Type.OPERATOR) {
                    switch (token.value) {
                        case "+":
                            result += parseTerm();
                            break;
                        case "-":
                            result -= parseTerm();
                            break;
                        case "*":
                            result *= parseTerm();
                            break;
                        case "/":
                            result /= parseTerm();
                            break;
                    }
                } else if (token.type == Token.Type.LPAREN) {
                    int innerResult = parseExpression();
                    if (tokens.get(index).type != Token.Type.RPAREN) {
                        throw new RuntimeException("Unbalanced parentheses");
                    }
                    index++;
                    return innerResult;
                } else {
                    break;
                }
            }
            return result;
        }

        private int parseTerm() {
            int result = parseFactor();
            while (index < tokens.size()) {
                Token token = tokens.get(index++);
                if (token.type == Token.Type.OPERATOR) {
                    switch (token.value) {
                        case "*":
                            result *= parseFactor();
                            break;
                        case "/":
                            result /= parseFactor();
                            break;
                    }
                } else if (token.type == Token.Type.MINUS) {
                    result = -parseFactor();
                } else {
                    break;
                }
            }
            return result;
        }

        private int parseFactor() {
            if (tokens.get(index).type == Token.Type.NUMBER) {
                index++;
                return Integer.parseInt(tokens.get(index - 1).value);
            } else if (tokens.get(index).type == Token.Type.MINUS) {
                index++;
                return -parseFactor();
            } else if (tokens.get(index).type == Token.Type.LPAREN) {
                int innerResult = parseExpression();
                if (tokens.get(index).type != Token.Type.RPAREN) {
                    throw new RuntimeException("Unbalanced parentheses");
                }
                index++;
                return innerResult;
            } else {
                throw new RuntimeException("Invalid token at position " + index);
            }
        }

    }

    private enum TokenType {
        SPACE,
        OPERATOR,
        NUMBER,
        MINUS,
        LPAREN,
        RPAREN
    }

    private static class Token {

        public final String value;
        public final TokenType type;

        public Token(String value, TokenType type) {
            this.value = value;
            this.type = type;
        }
    }
}