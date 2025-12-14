import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Expected: 7
        System.out.println(evaluate("2 * 3 + 4")); // Expected: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Expected: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Expected: 16
    }

    public static int evaluate(String expression) {
        return new Parser(new Tokenizer(expression).tokenize()).parse();
    }
}

class Tokenizer {
    private final String input;
    private int pos = 0;

    public Tokenizer(String input) {
        this.input = input;
    }

    public List<Token> tokenize() {
        List<Token> tokens = new ArrayList<>();
        while (pos < input.length()) {
            char ch = input.charAt(pos);
            if (Character.isDigit(ch)) {
                int value = 0;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                    value = value * 10 + (input.charAt(pos) - '0');
                    pos++;
                }
                tokens.add(new Token(TokenType.NUMBER, value));
            } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/') {
                tokens.add(new Token(TokenType.OPERATOR, ch));
                pos++;
            } else if (ch == '(') {
                tokens.add(new Token(TokenType.PARENTHESIS, '('));
                pos++;
            } else if (ch == ')') {
                tokens.add(new Token(TokenType.PARENTHESIS, ')'));
                pos++;
            } else if (Character.isWhitespace(ch)) {
                pos++;
            } else {
                throw new IllegalArgumentException("Unexpected character: " + ch);
            }
        }
        return tokens;
    }

    static class Token {
        final TokenType type;
        final Object value;

        Token(TokenType type, Object value) {
            this.type = type;
            this.value = value;
        }

        @Override
        public String toString() {
            return "(" + type + ", " + value + ")";
        }
    }

    enum TokenType {
        NUMBER,
        OPERATOR,
        PARENTHESIS
    }
}

class Parser {
    private final List<Token> tokens;
    private final List<Token> tokens = new ArrayList<>();
    private int pos = 0;

    public Parser(List<Token> tokens) {
    public Parser(tokens) {
        this.tokens = tokens;
    }

    public int parse() {
        return expression();
    }

    private int expression() {
        int result = term();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
    Token token = new Token(tokens.get(pos));
    Token token = new Token(tokens.get(pos));
    Token token = new Token(tokens.get(pos));
            if (token.type != TokenType.OPERATOR) break;
            if (token.type != TokenType.OPERATOR) break;
            if (token.type != TokenType.OPERATOR) break;
    if (token.type != TokenType.OPERATOR) {
                pos++;
            int right = term();
            switch (op) {
                case '+': result += right; break;
                case '-': result -= right; break;
                default: throw new IllegalArgumentException("Unexpected operator: " + op);
            }
        }
        return result;
    }

    private int term() {
        int result = factor();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if (token.type != TokenType.OPERATOR) break;
            char op = (char) token.value;
            pos++;
            int right = factor();
            switch (op) {
                case '*': result *= right; break;
                case '/': result /= right; break;
                default: throw new IllegalArgumentException("Unexpected operator: " + op);
            }
        }
        return result;
    }

    private int factor() {
        Token token = tokens.get(pos);
        pos++;
        switch (token.type) {
            case NUMBER: return (int) token.value;
            case PARENTHESIS:
                if ((char) token.value == '(') {
                    int result = expression();
                    token = tokens.get(pos);
                    if ((char) token.value != ')') throw new IllegalArgumentException("Expected )");
                    pos++;
                    return result;
                } else {
                    throw new IllegalArgumentException("Unexpected token: " + token);
                }
            case OPERATOR:
                if ((char) token.value == '-') {
                    int right = factor();
                    return -right;
                } else {
                    throw new IllegalArgumentException("Unexpected operator: " + token);
                }
            default:
                throw new IllegalArgumentException("Unexpected token: " + token);
        }
    }
}
