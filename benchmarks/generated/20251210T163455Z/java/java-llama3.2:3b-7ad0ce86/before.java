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
        return parser.parse().getResult();
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

    private static class Parser {
        private final List<Token> tokens;
        private final int precedence;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
            this.precedence = getPrecedence();
        }

        private int getPrecedence() {
            Map<TokenType, Integer> precedenceMap = new HashMap<>();
            precedenceMap.put(TokenType.MUL, 1);
            precedenceMap.put(TokenType.DIV, 1);
            precedenceMap.put(TokenType.ADD, 2);
            precedenceMap.put(TokenType.SUB, 2);
            return precedenceMap.getOrDefault(getOperatorType(tokens.get(0)), 0);
        }

        private TokenType getOperatorType(Token token) {
            if (token.getType() == TokenType.MUL || token.getType() == TokenType.DIV) {
                return TokenType.MUL;
            } else if (token.getType() == TokenType.ADD || token.getType() == TokenType.SUB) {
                return TokenType.ADD;
            }
            return TokenType.IDENTIFIER;
        }

        private Token peekToken() {
            return tokens.get(0);
        }

        public Expression parse() {
            Expression expression = parseExpression();
            while (!tokens.isEmpty()) {
                Token token = peekToken();
                if (token.getType() == TokenType.MUL || token.getType() == TokenType.DIV) {
                    parseMultiplication(token);
                } else if (token.getType() == TokenType.ADD || token.getType() == TokenType.SUB) {
                    parseAddition(token);
                }
            }
            return expression;
        }

        private Expression parseExpression() {
            Expression left = parseTerm();
            while (!tokens.isEmpty()) {
                Token token = peekToken();
                if (token.getType() == TokenType.MUL || token.getType() == TokenType.DIV) {
                    parseMultiplication(token);
                    break;
                }
            }
            return new Expression(left, null);
        }

        private Expression parseTerm() {
            Expression left = parseFactor();
            while (!tokens.isEmpty()) {
                Token token = peekToken();
                if (token.getType() == TokenType.MUL || token.getType() == TokenType.DIV) {
                    parseMultiplication(token);
                    break;
                }
            }
            return new Expression(left, null);
        }

        private Expression parseFactor() {
            if (peekToken().getType() == TokenType.IDENTIFIER) {
                Token token = peekToken();
                tokens.remove(0); // consume the token
                return new Expression(new Term(token), null);
            } else if (peekToken().getType() == TokenType.NEGATION) {
                parseNegation();
                return new Expression(new Term(peekToken()), null);
            } else {
                throw new RuntimeException("Unexpected token: " + peekToken());
            }
        }

        private void parseMultiplication(Token token) {
            Token left = tokens.remove(0); // consume the token
            Expression right = parseExpression();
            return new Multiplication(new Term(left), right);
        }

        private void parseAddition(Token token) {
            Token left = tokens.remove(0); // consume the token
            Expression right = parseExpression();
            return new Addition(new Term(left), right);
        }

        private void parseNegation() {
            tokens.remove(0); // consume the negation token
        }
    }

    public static class Expression {
        private final Term left;
        private final Expression right;

        public Expression(Term left, Expression right) {
            this.left = left;
            this.right = right;
        }

        public int getResult() {
            return left.getResult();
        }
    }

    public static class Term {
        private final Token token;

        public Term(Token token) {
            this.token = token;
        }

        public int getResult() {
            if (token.getType() == TokenType.IDENTIFIER) {
                return Integer.parseInt(token.getValue());
            } else if (token.getType() == TokenType.NEGATION) {
                return -Integer.parseInt(token.getValue());
            }
            throw new RuntimeException("Unexpected token: " + token);
        }
    }

    public static class Multiplication extends Expression {
        private final Term left;
        private final Expression right;

        public Multiplication(Term left, Expression right) {
            super(left, right);
        }

        public int getResult() {
            return (int) left.getResult() * (int) right.getResult();
        }
    }

    public static class Addition extends Expression {
        private final Term left;
        private final Expression right;

        public Addition(Term left, Expression right) {
            super(left, right);
        }

        public int getResult() {
            return (int) left.getResult() + (int) right.getResult();
        }
    }

    public enum TokenType {
        IDENTIFIER,
        MUL,
        DIV,
        ADD,
        SUB,
        NEGATION
    }

    public static class Token {
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
}