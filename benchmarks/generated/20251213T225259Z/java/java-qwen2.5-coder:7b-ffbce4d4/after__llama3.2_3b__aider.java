import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Should print 7
        System.out.println(evaluate("2 * 3 + 4")); // Should print 10
        System.out.println(evaluate("2 * (3 + 4)")); // Should print 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Should print 16
    }

    public static int evaluate(String expression) {
        return new Parser(new Tokenizer(expression).tokenize()).parse();
    }
}

class Tokenizer {
    private final String input;
    private int pos;

    public Tokenizer(String input) {
        this.input = input;
        this.pos = 0;
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
                tokens.add(new Token(TokenType.LPAREN, null));
                pos++;
            } else if (ch == ')') {
                tokens.add(new Token(TokenType.RPAREN, null));
                pos++;
            } else if (Character.isWhitespace(ch)) {
                pos++;
            } else {
                throw new IllegalArgumentException("Unexpected character: " + ch);
            }
        }
        return tokens;
    }

import java.util.*;
public class Token {
    final TokenType type;
    final Object value;
    Token(TokenType type, Object value) {
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

    enum TokenType {
        NUMBER,
        OPERATOR,
        LPAREN,
        RPAREN
    }
}

class Parser {
    private final List<Token> tokens;
    private int pos;

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
        this.pos = 0;
    }

    public int parse() {
        return expression();
    }

    private int expression() {
        int result = term();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if (token.type == Token.TokenType.OPERATOR && (token.value.equals("+") || token.value.equals("-"))) {
                pos++;
                int nextTerm = term();
                if (token.value.equals("+")) {
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
            if (token.type == Token.TokenType.OPERATOR && (token.value.equals("*") || token.value.equals("/"))) {
                pos++;
                int nextFactor = factor();
                if (token.value.equals("*")) {
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
        if (token.type == Token.TokenType.NUMBER) {
            return (int) token.value;
        } else if (token.type == Token.TokenType.OPERATOR && token.value.equals("-")) {
            return -factor();
        } else if (token.type == Token.TokenType.LPAREN) {
            int result = expression();
            if (pos < tokens.size() && tokens.get(pos).type == Token.TokenType.RPAREN) {
                pos++;
                return result;
            } else {
                throw new IllegalArgumentException("Expected ) but found " + tokens.get(pos));
            }
        } else {
            throw new IllegalArgumentException("Unexpected token: " + token);
        }
    }
}
