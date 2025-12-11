import java.util.*;
import java.util.function.BiFunction;
import java.util.stream.Collectors;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
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
                tokens.add(new Token(TokenType.PARENTHESIS, '('));
                pos++;
            } else if (c == ')') {
                tokens.add(new Token(TokenType.PARENTHESIS, ')'));
                pos++;
            } else if (Character.isWhitespace(c)) {
                pos++;
            } else {
                throw new IllegalArgumentException("Unexpected character: " + c);
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
            return "Token{" +
                    "type=" + type +
                    ", value=" + value +
                    '}';
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
    private int pos = 0;

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
    }

    public int parse() {
        return evaluateExpression(0);
    }

    private int evaluateExpression(int precedence) {
        int result = evaluateTerm();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if (token.type != TokenType.OPERATOR || ((OperatorToken) token).precedence <= precedence) {
                break;
            }
            pos++;
            int right = evaluateExpression(((OperatorToken) token).precedence + 1);
            result = applyOperation(result, (int) token.value, right);
        }
        return result;
    }

    private int evaluateTerm() {
        if (tokens.get(pos).type == TokenType.PARENTHESIS && ((ParenthesisToken) tokens.get(pos)).value == '(') {
            pos++;
            int result = evaluateExpression(0);
            if (pos < tokens.size() && tokens.get(pos).type == TokenType.PARENTHESIS && ((ParenthesisToken) tokens.get(pos)).value == ')') {
                pos++;
                return result;
            } else {
                throw new IllegalArgumentException("Missing closing parenthesis");
            }
        } else if (tokens.get(pos).type == TokenType.OPERATOR && ((OperatorToken) tokens.get(pos)).value == '-') {
            pos++;
            int right = evaluateTerm();
            return -right;
        } else if (tokens.get(pos).type == TokenType.NUMBER) {
            int value = (int) ((NumberToken) tokens.get(pos)).value;
            pos++;
            return value;
        } else {
            throw new IllegalArgumentException("Unexpected token: " + tokens.get(pos));
        }
    }

    private int applyOperation(int left, int operator, int right) {
        switch ((char) operator) {
            case '+':
                return left + right;
            case '-':
                return left - right;
            case '*':
                return left * right;
            case '/':
                if (right == 0) throw new ArithmeticException("Division by zero");
                return left / right;
            default:
                throw new IllegalArgumentException("Unknown operator: " + operator);
        }
    }

    static class OperatorToken extends Token {
        final int precedence;

        OperatorToken(char value, int precedence) {
            super(TokenType.OPERATOR, value);
            this.precedence = precedence;
        }
    }

    static class ParenthesisToken extends Token {
        ParenthesisToken(char value) {
            super(TokenType.PARENTHESIS, value);
        }
    }

    static class NumberToken extends Token {
        NumberToken(int value) {
            super(TokenType.NUMBER, value);
        }
    }
}