import java.util.*;
import java.util.regex.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // Expected: 3
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

    public List<Object> tokenize() {
        List<Object> tokens = new ArrayList<>();
        while (pos < input.length()) {
            char ch = input.charAt(pos);
            if (Character.isDigit(ch)) {
                int start = pos;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                    pos++;
                }
                tokens.add(Integer.parseInt(input.substring(start, pos)));
            } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/') {
                tokens.add(ch);
                pos++;
            } else if (ch == '(') {
                tokens.add('(');
                pos++;
            } else if (ch == ')') {
                tokens.add(')');
                pos++;
            } else {
                throw new IllegalArgumentException("Unexpected character: " + ch);
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
        return expression();
    }

    private int expression() {
        int result = term();
        while (pos < tokens.size()) {
            Object token = tokens.get(pos);
            if (token == '+' || token == '-') {
            pos++;
            int nextTerm = term();
            if ((char) token == '+') {
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
            Object token = tokens.get(pos);
            if (token == '*' || token == '/') {
                pos++;
                int nextFactor = factor();
                if ((char) token == '*') {
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
        Object token = tokens.get(pos);
        if (token instanceof Integer) {
            pos++;
            return (Integer) token;
        } else if (token == '(') {
            pos++;
            int result = expression();
            if (pos < tokens.size() && tokens.get(pos) == ')') {
                pos++;
                return result;
            } else if ((char) token != ')') {
                throw new IllegalArgumentException("Expected closing parenthesis");
            }
        } else if (token == '-') {
            pos++;
            return -factor();
        } else {
            throw new IllegalArgumentException("Unexpected token: " + token);
        }
    }
}
