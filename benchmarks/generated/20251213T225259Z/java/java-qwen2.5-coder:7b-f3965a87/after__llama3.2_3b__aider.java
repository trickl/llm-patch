import java.util.*;
import java.util.function.BiFunction;

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

    public List<Object> tokenize() {
        List<Object> tokens = new ArrayList<>();
        while (pos < input.length()) {
            char c = input.charAt(pos);
            if (Character.isDigit(c)) {
                int numStart = pos;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                    pos++;
                }
                tokens.add(Integer.parseInt(input.substring(numStart, pos)));
            } else if (c == '+' || c == '-' || c == '*' || c == '/') {
                tokens.add(c);
                pos++;
            } else if (c == '(') {
                tokens.add('(');
                pos++;
            } else if (c == ')') {
                tokens.add(')');
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
    private final List<Object> tokens;
    private int pos = 0;

    public Parser(List<Object> tokens) {
        this.tokens = tokens;
    }

    public int parse() {
        return parseExpression();
    }

    private int parseExpression() {
        int result = parseTerm();
        while (pos < tokens.size()) {
            Object token = tokens.get(pos);
            if (!(token instanceof Character)) {
                break;
            }
            char op = (Character) token;
            if (op != '+' && op != '-') {
                break;
            }
            pos++;
            int right = parseTerm();
            result += op == '+' ? right : -right;
        }
        return result;
    }

    private int parseTerm() {
        int result = parseFactor();
        while (pos < tokens.size()) {
            Object token = tokens.get(pos);
            if (!(token instanceof Character)) {
                break;
            }
            char op = (Character) token;
            if (op != '*' && op != '/') {
                break;
            }
            pos++;
            int right = parseFactor();
            result += op == '*' ? right : result / right;
        }
        return result;
    }

    private int parseFactor() {
        Object token = tokens.get(pos);
        if (token instanceof Integer) {
            pos++;
            return (Integer) token;
        } else if (token instanceof Character && (Character) token == '-') {
            pos++;
            return -parseFactor();
        } else if (token instanceof Character && (Character) token == '(') {
            pos++;
            int result = parseExpression();
            if (!(tokens.get(pos++) instanceof Character) || tokens.get(pos - 1) != ')') {
                throw new IllegalArgumentException("Unexpected token: '('");
            }
            return result;
        } else {
            throw new IllegalArgumentException("Unexpected token: " + token);
        }
    }
}
