import java.util.*;
import java.util.function.BiFunction;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // Expected: 3
        System.out.println(evaluate("2 * 3 + 4")); // Expected: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Expected: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Expected: 16
    }

    public static int evaluate(String expression) {
        return parse(expression).evaluate();
    }

    private static Node parse(String expression) {
        Tokenizer tokenizer = new Tokenizer(expression);
        Parser parser = new Parser(tokenizer);
        return parser.parse();
    }
}

class Tokenizer {
    private final String input;
    private int pos;

    public Tokenizer(String input) {
        this.input = input;
        this.pos = 0;
    }

    public Token nextToken() {
        skipWhitespace();
        if (pos >= input.length()) {
            return new Token(TokenType.EOF, null);
        }
        char ch = input.charAt(pos++);
        switch (ch) {
            case '+':
                return new Token(TokenType.PLUS, "+");
            case '-':
                return new Token(TokenType.MINUS, "-");
            case '*':
                return new Token(TokenType.MUL, "*");
            case '/':
                return new Token(TokenType.DIV, "/");
            case '(':
                return new Token(TokenType.LPAREN, "(");
            case ')':
                return new Token(TokenType.RPAREN, ")");
            default:
                if (Character.isDigit(ch)) {
                    int start = pos - 1;
                    while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                        pos++;
                    }
                    String value = input.substring(start, pos);
                    return new Token(TokenType.NUMBER, Integer.parseInt(value));
                } else {
                    throw new IllegalArgumentException("Unexpected character: " + ch);
                }
        }
    }

    private void skipWhitespace() {
        while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) {
            pos++;
        }
    }
}

enum TokenType {
    PLUS("+"),
    MINUS("-"),
    MUL("*"),
    DIV("/"),
    LPAREN("("),
    RPAREN(")"),
    NUMBER(null),
    EOF(null);

    private final String literal;

    TokenType(String literal) {
        this.literal = literal;
    }

    public String getLiteral() {
        return literal;
    }
}

class Token {
    private final TokenType type;
    private final Object value;

    public Token(TokenType type, Object value) {
        this.type = type;
        this.value = value;
    }

    public TokenType getType() {
        return type;
    }

    public Object getValue() {
        return value;
    }
}

abstract class Node {
    abstract int evaluate();
}

class NumberNode extends Node {
    private final int value;

    public NumberNode(int value) {
        this.value = value;
    }

    @Override
    int evaluate() {
        return value;
    }
}

class BinaryOpNode extends Node {
    private final Node left;
    private final Node right;
    private final BiFunction<Integer, Integer, Integer> operator;

    public BinaryOpNode(Node left, Node right, BiFunction<Integer, Integer, Integer> operator) {
        this.left = left;
        this.right = right;
        this.operator = operator;
    }

    @Override
    int evaluate() {
        return operator.apply(left.evaluate(), right.evaluate());
    }
}

class UnaryMinusNode extends Node {
    private final Node operand;

    public UnaryMinusNode(Node operand) {
        this.operand = operand;
    }

    @Override
    int evaluate() {
        return -operand.evaluate();
    }
}

class Parser {
    private final Tokenizer tokenizer;
    private Token currentToken;

    public Parser(Tokenizer tokenizer) {
        this.tokenizer = tokenizer;
        this.currentToken = tokenizer.nextToken();
    }

    Node parse() {
        Node node = expression();
        if (currentToken.getType() != TokenType.EOF) {
            throw new IllegalArgumentException("Unexpected token: " + currentToken.getLiteral());
        }
        return node;
    }

    private Node expression() {
        Node left = term();
        while (currentToken.getType() == TokenType.PLUS || currentToken.getType() == TokenType.MINUS) {
            Token op = currentToken;
            moveNext();
            Node right = term();
            if (op.getType() == TokenType.PLUS) {
                left = new BinaryOpNode(left, right, Integer::sum);
            } else {
                left = new BinaryOpNode(left, right, (a, b) -> a - b);
            }
        }
        return left;
    }

    private Node term() {
        Node left = factor();
        while (currentToken.getType() == TokenType.MUL || currentToken.getType() == TokenType.DIV) {
            Token op = currentToken;
            moveNext();
            Node right = factor();
            if (op.getType() == TokenType.MUL) {
                left = new BinaryOpNode(left, right, Integer::multiplyExact);
            } else {
                left = new BinaryOpNode(left, right, Integer::divideUnsigned);
            }
        }
        return left;
    }

    private Node factor() {
        Token token = currentToken;
        moveNext();
        switch (token.getType()) {
            case NUMBER:
                return new NumberNode((Integer) token.getValue());
            case MINUS:
                if (currentToken.getType() == TokenType.NUMBER) {
                    token = currentToken;
                    moveNext();
                    return new UnaryMinusNode(new NumberNode((Integer) token.getValue()));
                } else {
                    throw new IllegalArgumentException("Unexpected token after unary minus: " + currentToken.getLiteral());
                }
            case LPAREN:
                Node node = expression();
                if (currentToken.getType() != TokenType.RPAREN) {
                    throw new IllegalArgumentException("Expected closing parenthesis, but got: " + currentToken.getLiteral());
                }
                moveNext();
                return node;
            default:
                throw new IllegalArgumentException("Unexpected token: " + token.getLiteral());
        }
    }

    private void moveNext() {
        currentToken = tokenizer.nextToken();
    }
}