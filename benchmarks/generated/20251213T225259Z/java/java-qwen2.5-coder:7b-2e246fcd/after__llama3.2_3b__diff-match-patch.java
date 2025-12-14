import java.util.*;

public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Expected: 7
        System.out.println(evaluate("2 * 3 + 4")); // Expected: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Expected: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Expected: 16
    }

    public static int evaluate(String expression) {
        return new Parser(new Tokenizer(expression)).parse();
    }
}class Tokenizer {
    private final String input;
    private int pos = 0;

    public Tokenizer(String input) {
        this.input = input;
    }

      public List<Token> tokenize() {      List<Token> tokens = new ArrayList<>();
        while (pos < input.length()) {
            char ch = input.charAt(pos);
               if (Character.isDigit(ch)) {             int value = 0;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) {
                    value = value * 10 + (input.charAt(pos) - '0');
                    pos++;
                }
                    tokens.add(new Token(TokenType.NUMBER, value));        } else if (ch == '+' || ch == '-' || ch == '*' || ch == '/') {
                     tokens.add(new Token(TokenType.OPERATOR, ch));           pos++;
            } else if (ch == '(') {
                      tokens.add(new Token(TokenType.PARENTHESIS, '('));          pos++;
            } else if (ch == ')') {
                       tokens.add(new Token(TokenType.PARENTHESIS, ')'));         pos++;
            } else if (Character.isWhitespace(ch)) {
                        pos++;    } else {
                         throw new IllegalArgumentException("Unexpected character: " + ch);   }
        }
        re        return tokens;lass Parser {
    private final List<Token> tokens;
    private int pos = 0;

    public     public Parser(List<Token> tokens) {s.tokens = tokens;
    }

    public i    public int parse() {rn expression();
    }

    private i    private int expression() {esult = term();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if            if (token.type == TokenType.OPERATOR && (token.value == '+' || token.value == '-')) {  pos++;
                int nextTerm = term();
                if (token.value == '+') {
                    result += nextTerm;
                } else {
                    result -= nextTerm;
                }
            } else {
                               break;       }
        return r        return result;te int t    private int term() {t = factor();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if (to            if (token.type == TokenType.OPERATOR && (token.value == '*' || token.value == '/')) {s++;
                int nextFactor = factor();
                if (token.value == '*') {
                    result *= nextFactor;
                } else {
                    result /= nextFactor;
                }
            } else {
                bre                break;   }
        return resul        return result;nt facto    private int factor() { tokens.get(pos);
        if (token.type        if (token.type == TokenType.PARENTHESIS && token.value == '(') {         int result = expression();
            if (pos < tokens.size() && tokens.get(pos).type == TokenType.PARENTHESIS && tokens.get(pos).value == ')') {
                pos++;
                return result;
            } else {
                throw n                throw new IllegalArgumentException("Unmatched parenthesis"); else if (toke            pos++;n.    @Override    public Token(TokenType type, int value) {                throw new IllegalArgumentException("Unexpected token: " + token);            pos++;type == TokenType.OPERATOR && token.value == '-') {
            pos++;
            return -factor();
        } else if (token.type == TokenType.NUMBER) {
            pos++;
            return token.value;
        } else {
            throw new IllegalArgumentException("Unexpected token: " + token);
        }
    }
}

enum TokenType {
    NUMBER,
    OPERATOR,
    PARENTHESIS
}

class Token {
    final TokenType type;
    final int value;

    public Token(TokenType type, int value) {
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