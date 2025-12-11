import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Output: 7
        System.out.println(evaluate("2 * 3 + 4")); // Output: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Output: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Output: 16
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
            char c = input.charAt(pos);
            if (Character.isDigit(c)) {
                int value = 0;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                    value = value * 10 + (input.charAt(pos) - '0');
                    pos++;
                }
                tokens.add(new Token(TokenType.NUMBER, value));
            } else if (c == '+' || c == '-' || c == '*' || c == '/') {
                tokens.add(new Token(TokenType.OPERATOR, c));
                pos++;
            } else if (c == '(') {
                tokens.add(new Token(TokenType.LPAREN, null));
                pos++;
            } else if (c == ')') {
                tokens.add(new Token(TokenType.RPAREN, null));
                pos++;
            } else if (Character.isWhitespace(c)) {
                pos++;
            } else {
                throw new IllegalArgumentException("Unexpected character: " + c);
            }
        }
        return tokens;
    }
}

class Parser {
    private final List<Token> tokens;
    private int pos = 0;

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
    }

    public int parse() {
        return expression();
    }

    private int expression() {
        int result = term();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if (token.type == TokenType.OPERATOR && (token.value == '+' || token.value == '-')) {
                pos++;
                int nextTerm = term();
                if (token.value == '+') {
                    result += nextTerm;
                } else {
                    result -= nextTerm;
                }
            } else {
                break;
            }
        }
        return result;
    }

    private int term() {
        int result = factor();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if (token.type == TokenType.OPERATOR && (token.value == '*' || token.value == '/')) {
                pos++;
                int nextFactor = factor();
                if (token.value == '*') {
                    result *= nextFactor;
                } else {
                    result /= nextFactor;
                }
            } else {
                break;
            }
        }
        return result;
    }

    private int factor() {
        Token token = tokens.get(pos);
        pos++;
        if (token.type == TokenType.NUMBER) {
            return (int) token.value;
        } else if (token.type == TokenType.LPAREN) {
            int result = expression();
            token = tokens.get(pos);
            if (token.type != TokenType.RPAREN) {
                throw new IllegalArgumentException("Expected ')'");
            }
            pos++;
            return result;
        } else if (token.type == TokenType.OPERATOR && token.value == '-') {
            return -factor();
        } else {
            throw new IllegalArgumentException("Unexpected token: " + token);
        }
    }
}

enum TokenType {
    NUMBER,
    OPERATOR,
    LPAREN,
    RPAREN
}

class Token {
    final TokenType type;
    final Object value;

    public Token(TokenType type, Object value) {
        this.type = type;
        this.value = value;
    }

    @Override
    public String toString() {
        return "Token{" +
                "type=" + type +
                ", value=" + value +
                '}';
    }
}