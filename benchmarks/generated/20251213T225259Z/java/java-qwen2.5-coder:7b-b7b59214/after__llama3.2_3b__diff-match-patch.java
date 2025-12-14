import java.util.*;import java.util.*;public class ExpressionEvaluator {
    public static void main(String[] args) {
        System.out.println(evaluate("3 + 4 * (2 - 1)")); // Output: 7
        System.out.println(evaluate("2 * 3 + 4")); // Output: 10
        System.out.println(evaluate("2 * (3 + 4)")); // Output: 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // Output: 16
    }

    public static int evaluate(St        return new Parser(new Tokenizer(expression).tokenize()).parse();kenize()).parse();
    }
}

class Tokenizer {
    private final String input;
    private int pos;

    public Tokenizer(String input) {
        this.input = input;
        this.pos = 0;
    }

    public List<To        List<Token> tokens = new ArrayList<>();ew ArrayList<>();
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
                tokens.add(new Token(TokenType.LPAREN, null));
                pos++;
            } else if (c == ')') {
                tokens.add(new Token(TokenType.RPAREN, null));
                pos++;
            } else if (Character.isWhitespace(c)) {
                pos++;
            } else {
                throw new IllegalArgumentException("Invalid character: " + c);
               return tokens;  return tokens;
    }

    private enum TokenType {
        NUMBER,
        OPERATOR,
        LPAREN,
        RPAREN
    }

    public static class Token {
        private final TokenType type;
        private final Object value;

        public Token(TokenType type, Object value) {
            this.type = type;
            this.value = value;
        }

        public TokenT            return type;   return type;
        }

        public Objec            return value; return value;
        }
    }
}

class Parser {
    private final List<Token> tokens;
    private int pos;

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
        this.pos = 0;
    }

    public         return expression();expression();
    }

    private int ex        int result = term();lt = term();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if (token.getType() == Token.TokenType.OPERATOR && (token.getValue().equals("+") || token.getValue().equals("-"))) {
                pos++;
                int nextTerm = term();
                if (token.getValue().equals("+")) {
                    result += nextTerm;
                } else {
                    result -= nextTerm;
                }
                         break;     break;
            }        return result;rn result;
    }

    private int        int result = factor();factor();
        while (pos < tokens.size()) {
            Token token = tokens.get(pos);
            if (token.getType() == Token.TokenType.OPERATOR && (token.getValue().equals("*") || token.getValue().equals("/"))) {
                pos++;
                int nextFactor = factor();
                if (token.getValue().equals("*")) {
                    result *= nextFactor;
                } else {
                    result /= nextFactor;
                }
                            break;  break;
            }
          return result;result;
    }

    private int fact        Token token = tokens.get(pos);(pos);
        if (token.getType() == Token.TokenType.LPAREN) {
            pos++;
            int result = expression();
            if (tokens.get(pos).getType() != Token.TokenType.RPAREN) {
                throw new IllegalArgumentException("Expected ')'");
            }
            pos++;
            return result;
        } else if (token.getType() == Token.TokenType.OPERATOR && token.getValue().equals("-")) {
            pos++;
            int result = factor();
            return -result;
        } else if (token.getType() == Token.TokenType.NUMBER) {
            pos++;
            return (int) token.getValue();
        } e            throw new IllegalArgumentException("Unexpected token: " + token);ken);
        }
    }
}