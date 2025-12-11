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

    private static class Parser {
        List<Token> tokens;
        int pos;

        public Parser(List<Token> tokens) {
            this.tokens = tokens;
            this.pos = 0;
        }

        Token parse() {
            if (pos >= tokens.size()) {
                throw new RuntimeException("Unexpected end of input");
            }
            return tokens.get(pos++);
        }

        Token parseTerm() {
            Token term = parse();
            while (term.type.equals("MUL") || term.type.equals("DIV")) {
                String op = term.type;
                term = parse();
                if (op.equals("MUL")) {
                    term = new Token(op, (int) term.value * (int) term.value);
                } else if (op.equals("DIV")) {
                    term = new Token(op, (int) term.value / (int) term.value);
                }
            }
            return term;
        }

        Token parseExpr() {
            Token expr = parseTerm();
            while (expr.type.equals("ADD") || expr.type.equals("SUB")) {
                String op = expr.type;
                expr = parse();
                if (op.equals("ADD")) {
                    expr = new Token(op, (int) expr.value + (int) expr.value);
                } else if (op.equals("SUB")) {
                    expr = new Token(op, (int) expr.value - (int) expr.value);
                }
            }
            return expr;
        }

        Token parse() {
            if (pos >= tokens.size()) {
                throw new RuntimeException("Unexpected end of input");
            }
            String type = tokens.get(pos).type;
            Object value = tokens.get(pos++).value;
            return new Token(type, value);
        }
    }

    private static class Evaluator {
        public int evaluate(Token expr) {
            if (expr.type.equals("NUM")) {
                return (int) expr.value;
            } else if (expr.type.equals("MUL") || expr.type.equals("DIV")) {
                Object left = ((Token) parseTerm()).value;
                Object right = ((Token) parseTerm()).value;
                if (expr.type.equals("MUL")) {
                    return (int) left * (int) right;
                } else if (expr.type.equals("DIV")) {
                    return (int) left / (int) right;
                }
            } else if (expr.type.equals("ADD") || expr.type.equals("SUB")) {
                Object left = ((Token) parseExpr()).value;
                Object right = ((Token) parseExpr()).value;
                if (expr.type.equals("ADD")) {
                    return (int) left + (int) right;
                } else if (expr.type.equals("SUB")) {
                    return (int) left - (int) right;
                }
            } else if (expr.type.equals("UMINUS")) {
                Object value = ((Token) parseExpr()).value;
                return -(int) value;
            } else {
                throw new RuntimeException("Unexpected token type");
            }
        }

        private Token parseTerm() {
            return new Parser(tokens).parseTerm();
        }

        private Token parseExpr() {
            return new Parser(tokens).parseExpr();
        }
    }

    public static int evaluate(String expression) {
        List<Token> tokens = tokenize(expression);
        if (tokens.isEmpty()) {
            throw new RuntimeException("Empty input");
        }
        Evaluator evaluator = new Evaluator();
        return evaluator.evaluate(new Token("NUM", 0));
    }

    private static List<Token> tokenize(String expression) {
        // Simple lexer that only handles numbers, +, -, *, /, and parentheses
        List<Token> tokens = new ArrayList<>();
        StringBuilder currentNumber = new StringBuilder();
        char prevChar = '\0';
        for (char c : expression.toCharArray()) {
            if (Character.isDigit(c)) {
                currentNumber.append(c);
            } else if (c == '(') {
                if (prevChar != '*') {
                    tokens.add(new Token("NUM", 0));
                }
                tokens.add(new Token("LPAREN", null));
                prevChar = c;
            } else if (c == ')') {
                if (prevChar != '*') {
                    tokens.add(new Token("NUM", 0));
                }
                tokens.add(new Token("RPAREN", null));
                prevChar = c;
            } else if (c == '+' || c == '-') {
                if (!currentNumber.toString().isEmpty()) {
                    tokens.add(new Token("NUM", Integer.parseInt(currentNumber.toString())));
                    currentNumber.setLength(0);
                }
                tokens.add(new Token(c + "", 0));
                prevChar = c;
            } else if (c == '*' || c == '/') {
                if (!currentNumber.toString().isEmpty()) {
                    tokens.add(new Token("NUM", Integer.parseInt(currentNumber.toString())));
                    currentNumber.setLength(0);
                }
                tokens.add(new Token(c + "", 0));
                prevChar = c;
            } else {
                throw new RuntimeException("Unexpected character: " + c);
            }
        }
        if (!currentNumber.toString().isEmpty()) {
            tokens.add(new Token("NUM", Integer.parseInt(currentNumber.toString())));
        }
        return tokens;
    }
}