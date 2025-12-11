import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2"));
        System.out.println(evaluate("2 * 3 + 4"));
        System.out.println(evaluate("2 * (3 + 4)"));
        System.out.println(evaluate("8 / 2 * (2 + 2)"));
    }

    public static int evaluate(String expression) {
        Tokenizer tokenizer = new Tokenizer(expression);
        Parser parser = new Parser(tokenizer);
        return parser.parse().evaluate();
    }
}

class Tokenizer {
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
                    tokens.add(new Token(TokenType.STRING, currentToken.toString()));
                    currentToken.setLength(0);
                }
            } else {
                currentToken.append(c);
            }
        }
        if (!currentToken.isEmpty()) {
            tokens.add(new Token(TokenType.STRING, currentToken.toString()));
        }
        return tokens;
    }

    public List<Token> getTokens() {
        return tokens;
    }
}

enum TokenType {
    STRING,
    NUMBER,
    LPAREN,
    RPAREN,
    PLUS,
    MINUS,
    TIMES,
    DIVIDE
}

class Token {
    private final TokenType type;
    private final String value;

    public Token(TokenType type, String value) {
        this.type = type;
        this.value = value;
    }

    public TokenType getType() {
        return type;
    }

    public String getValue() {
        return value;
    }
}

class Parser {
    private final List<Token> tokens;
    private int index;

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
        this.index = 0;
    }

    public Expression parse() {
        return parseExpression();
    }

    private Expression parseExpression() {
        Expression left = parseTerm();
        while (index < tokens.size()) {
            Token token = tokens.get(index);
            switch (token.getType()) {
                case PLUS:
                    index++;
                    Expression right = parseTerm();
                    if (right == null) {
                        throw new RuntimeException("Malformed expression");
                    }
                    return new BinaryExpression(left, token.getValue(), right);
                case MINUS:
                    index++;
                    Expression right = parseTerm();
                    if (right == null) {
                        throw new RuntimeException("Malformed expression");
                    }
                    return new BinaryExpression(left, "-", right);
                default:
                    break;
            }
        }
        return left;
    }

    private Expression parseTerm() {
        Expression left = parseFactor();
        while (index < tokens.size()) {
            Token token = tokens.get(index);
            switch (token.getType()) {
                case TIMES:
                    index++;
                    Expression right = parseFactor();
                    if (right == null) {
                        throw new RuntimeException("Malformed expression");
                    }
                    return new BinaryExpression(left, token.getValue(), right);
                case DIVIDE:
                    index++;
                    Expression right = parseFactor();
                    if (right == null) {
                        throw new RuntimeException("Malformed expression");
                    }
                    return new BinaryExpression(left, "/", right);
                default:
                    break;
            }
        }
        return left;
    }

    private Expression parseFactor() {
        if (tokens.get(index).getType() == TokenType.MINUS) {
            index++;
            return parseFactor();
        } else if (tokens.get(index).getType() == TokenType.LPAREN) {
            index++;
            Expression expression = parseExpression();
            if (expression == null) {
                throw new RuntimeException("Malformed expression");
            }
            index++; // consume RPAREN
            return expression;
        } else if (tokens.get(index).getType() == TokenType.NUMBER) {
            index++;
            return new LiteralExpression(tokens.get(index - 1).getValue());
        } else if (tokens.get(index).getType() == TokenType.STRING) {
            index++;
            return new LiteralExpression(tokens.get(index - 1).getValue());
        }
        return null;
    }

    private Expression parseLiteral() {
        if (tokens.get(index).getType() == TokenType.NUMBER) {
            index++;
            return new LiteralExpression(tokens.get(index - 1).getValue());
        } else if (tokens.get(index).getType() == TokenType.STRING) {
            index++;
            return new LiteralExpression(tokens.get(index - 1).getValue());
        }
        throw new RuntimeException("Malformed expression");
    }

    private Expression parseUnaryMinus() {
        if (tokens.get(index).getType() == TokenType.MINUS) {
            index++;
            return parseUnaryMinus();
        } else if (tokens.get(index).getType() == TokenType.NUMBER || tokens.get(index).getType() == TokenType.STRING) {
            index++;
            return new UnaryExpression("-", parseLiteral());
        }
        throw new RuntimeException("Malformed expression");
    }

    private Expression parseBinaryExpression(String operator, Expression left, Expression right) {
        if (left == null || right == null) {
            throw new RuntimeException("Malformed expression");
        }
        return new BinaryExpression(left, operator, right);
    }

    private class BinaryExpression implements Expression {
        private final Expression left;
        private final String operator;
        private final Expression right;

        public BinaryExpression(Expression left, String operator, Expression right) {
            this.left = left;
            this.operator = operator;
            this.right = right;
        }

        @Override
        public int evaluate() {
            switch (operator) {
                case "+":
                    return left.evaluate() + right.evaluate();
                case "-":
                    return left.evaluate() - right.evaluate();
                case "*":
                    return left.evaluate() * right.evaluate();
                case "/":
                    if (right.evaluate() == 0) {
                        throw new ArithmeticException("Division by zero");
                    }
                    return left.evaluate() / right.evaluate();
            }
        }

        @Override
        public String toString() {
            return "(" + left + " " + operator + " " + right + ")";
        }
    }

    private class UnaryExpression implements Expression {
        private final String operator;
        private final Expression expression;

        public UnaryExpression(String operator, Expression expression) {
            this.operator = operator;
            this.expression = expression;
        }

        @Override
        public int evaluate() {
            return -expression.evaluate();
        }

        @Override
        public String toString() {
            return "-" + expression;
        }
    }

    private class LiteralExpression implements Expression {
        private final String value;

        public LiteralExpression(String value) {
            this.value = value;
        }

        @Override
        public int evaluate() {
            return Integer.parseInt(value);
        }

        @Override
        public String toString() {
            return value;
        }
    }
}