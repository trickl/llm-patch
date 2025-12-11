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
        return parser.parse().getValue();
    }
}

class Tokenizer {
    private final String expression;
    private final List<Token> tokens;

    public Tokenizer(String expression) {
        this.expression = expression;
        this.tokens = tokenize(expression);
    }

    private List<Token> tokenize(String expression) {
        List<Token> tokens = new ArrayList<>();
        StringBuilder currentToken = new StringBuilder();
        for (char c : expression.toCharArray()) {
            if (Character.isWhitespace(c)) {
                if (!currentToken.isEmpty()) {
                    tokens.add(new Token(TokenType.IDENTIFIER, currentToken.toString()));
                    currentToken.setLength(0);
                }
            } else {
                currentToken.append(c);
            }
        }
        if (!currentToken.isEmpty()) {
            tokens.add(new Token(TokenType.IDENTIFIER, currentToken.toString()));
        }
        return tokens;
    }

    public List<Token> getTokens() {
        return tokens;
    }
}

enum TokenType {
    IDENTIFIER,
    OP,
    LPAREN,
    RPAREN
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
    private int pos;

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
        this.pos = 0;
    }

    public Expression parse() {
        return parseExpression();
    }

    private Expression parseExpression() {
        Expression left = parseTerm();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            pos++;
            if (token.getType() == TokenType.OP) {
                Operator op = getOperator(token.getValue());
                Expression right = parseExpression();
                return new BinaryOp(left, op, right);
            }
        }
        return left;
    }

    private Expression parseTerm() {
        Expression left = parseFactor();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            pos++;
            if (token.getType() == TokenType.OP) {
                Operator op = getOperator(token.getValue());
                Expression right = parseFactor();
                return new BinaryOp(left, op, right);
            }
        }
        return left;
    }

    private Expression parseFactor() {
        if (tokens.get(pos).getType() == TokenType.LPAREN) {
            pos++;
            Expression expr = parseExpression();
            pos++; // consume RPAREN
            return expr;
        } else if (tokens.get(pos).getType() == TokenType.IDENTIFIER && tokens.get(pos + 1).getType() == TokenType.OP) {
            Operator op = getOperator(tokens.get(pos + 1).getValue());
            Expression right = parseFactor();
            pos += 2; // consume OP and value
            return new UnaryOp(op, right);
        } else if (tokens.get(pos).getType() == TokenType.IDENTIFIER) {
            String value = tokens.get(pos).getValue();
            pos++;
            return new Literal(value);
        }
        throw new RuntimeException("Unexpected token: " + tokens.get(pos));
    }

    private Operator getOperator(String op) {
        switch (op) {
            case "+":
                return Operator.ADD;
            case "-":
                return Operator.SUBTRACT;
            case "*":
                return Operator.MULTIPLY;
            case "/":
                return Operator.DIVIDE;
            default:
                throw new RuntimeException("Unknown operator: " + op);
        }
    }

    public class Expression {
        private final Expression left;
        private final Operator op;
        private final Expression right;

        public Expression(Expression left, Operator op, Expression right) {
            this.left = left;
            this.op = op;
            this.right = right;
        }

        public int getValue() {
            switch (op) {
                case ADD:
                    return left.getValue() + right.getValue();
                case SUBTRACT:
                    return left.getValue() - right.getValue();
                case MULTIPLY:
                    return left.getValue() * right.getValue();
                case DIVIDE:
                    if (right.getValue() == 0) {
                        throw new ArithmeticException("Division by zero");
                    }
                    return left.getValue() / right.getValue();
            }
        }

        public static class BinaryOp extends Expression {
            public BinaryOp(Expression left, Operator op, Expression right) {
                super(left, op, right);
            }
        }

        public static class UnaryOp extends Expression {
            public UnaryOp(Operator op, Expression operand) {
                super(null, op, operand);
            }
        }
    }

    public enum Operator {
        ADD,
        SUBTRACT,
        MULTIPLY,
        DIVIDE
    }
}