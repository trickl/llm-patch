import java.util.*;

public class ExpressionEvaluator {
    public static int evaluate(String expression) {
        // Tokenizer
        List<Token> tokens = tokenize(expression);

        // Parser
        ParseTree parseTree = parse(tokens);

        // Evaluator
        return evaluator(parseTree);
    }

    private static List<Token> tokenize(String expression) {
        List<Token> tokens = new ArrayList<>();
        StringBuilder currentToken = new StringBuilder();
        for (char c : expression.toCharArray()) {
            if (Character.isWhitespace(c)) {
                if (!currentToken.isEmpty()) {
                    tokens.add(new Token(TokenType.LITERAL, currentToken.toString()));
                    currentToken.setLength(0);
                }
            } else if ("+-*/()".indexOf(c) != -1) {
                if (!currentToken.isEmpty()) {
                    tokens.add(new Token(TokenType.OP, String.valueOf(c)));
                    currentToken.setLength(0);
                }
                tokens.add(new Token(TokenType.OP, String.valueOf(c)));
            } else {
                currentToken.append(c);
            }
        }
        if (!currentToken.isEmpty()) {
            tokens.add(new Token(TokenType.LITERAL, currentToken.toString()));
        }
        return tokens;
    }

    private static ParseTree parse(List<Token> tokens) {
        List<ParseNode> nodes = new ArrayList<>();
        Stack<ParseNode> stack = new Stack<>();
        for (Token token : tokens) {
            if (token.type == TokenType.LITERAL) {
                nodes.add(new LiteralNode(token.value));
            } else if (token.type == TokenType.OP) {
                while (!stack.isEmpty() && getPrecedence(stack.peek()) >= getPrecedence(token)) {
                    nodes.add(stack.pop());
                }
                stack.push(new Node(token, nodes.size()));
            } else if (token.type == TokenType.LPAREN) {
                stack.push(new LParenNode(nodes.size()));
            } else if (token.type == TokenType.RPAREN) {
                while (!stack.isEmpty() && !stack.peek().type.equals(TokenType.LPAREN)) {
                    nodes.add(stack.pop());
                }
                stack.pop();
            }
        }
        while (!stack.isEmpty()) {
            nodes.add(stack.pop());
        }
        return new ParseTree(nodes);
    }

    private static int getPrecedence(ParseNode node) {
        if (node.type == TokenType.LPAREN) {
            return 0;
        } else if (node.type == TokenType.OP) {
            switch (node.value.charAt(0)) {
                case '+':
                case '-':
                    return 1;
                case '*':
                case '/':
                    return 2;
                default:
                    throw new RuntimeException("Invalid operator");
            }
        } else {
            throw new RuntimeException("Invalid node type");
        }
    }

    private static int evaluator(ParseTree parseTree) {
        List<ParseNode> nodes = parseTree.nodes;
        Stack<Integer> stack = new Stack<>();
        for (ParseNode node : nodes) {
            if (node.type == TokenType.LITERAL) {
                stack.push(Integer.parseInt(node.value));
            } else if (node.type == TokenType.OP) {
                int operand2 = stack.pop();
                int operand1 = stack.pop();
                switch (node.value.charAt(0)) {
                    case '+':
                        stack.push(operand1 + operand2);
                        break;
                    case '-':
                        stack.push(operand1 - operand2);
                        break;
                    case '*':
                        stack.push(operand1 * operand2);
                        break;
                    case '/':
                        if (operand2 == 0) {
                            throw new RuntimeException("Division by zero");
                        }
                        stack.push(operand1 / operand2);
                        break;
                }
            } else if (node.type == TokenType.LPAREN) {
                int result = evaluator(parseTree.children.get(node.index));
                stack.push(result);
            }
        }
        return stack.pop();
    }

    private enum TokenType {
        LITERAL,
        OP,
        LPAREN,
        RPAREN
    }

    private static class Token {
        public TokenType type;
        public String value;

        public Token(TokenType type, String value) {
            this.type = type;
            this.value = value;
        }
    }

    private static class ParseNode {
        public TokenType type;
        public int index;
        public ParseTree children;

        public ParseNode(TokenType type, int index) {
            this.type = type;
            this.index = index;
        }

        public ParseNode(TokenType type, int index, List<ParseNode> children) {
            this(type, index);
            this.children = new ParseTree(children);
        }
    }

    private static class LiteralNode extends ParseNode {
        public String value;

        public LiteralNode(String value) {
            super(TokenType.LITERAL, 0);
            this.value = value;
        }
    }

    private static class Node extends ParseNode {
        public Token token;
        public int index;

        public Node(Token token, int index) {
            super(TokenType.OP, index);
            this.token = token;
            this.index = index;
        }
    }

    private static class LParenNode extends ParseNode {
        public List<ParseNode> children;

        public LParenNode(int index) {
            super(TokenType.LPAREN, index);
            this.children = new ArrayList<>();
        }
    }

    private static class ParseTree {
        public List<ParseNode> nodes;

        public ParseTree(List<ParseNode> nodes) {
            this.nodes = nodes;
        }
    }

    public static void main(String[] args) {
        System.out.println(evaluate("1 + 2")); // 3
        System.out.println(evaluate("2 * 3 + 4")); // 10
        System.out.println(evaluate("2 * (3 + 4)")); // 14
        System.out.println(evaluate("8 / 2 * (2 + 2)")); // 16
    }
}