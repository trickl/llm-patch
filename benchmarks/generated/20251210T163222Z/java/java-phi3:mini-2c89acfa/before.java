import java.util.Stack;


public class ExpressionEvaluator {

    public static void main(String[] args) {

        // Smoke tests to demonstrate functionality

        System.out.println("1 + 2 = " + evaluateExpression("1 + 2"));

        System.out.println("2 * 3 + 4 = " + evaluateExpression("2 * 3 + 4"));

        System.out.println("2 * (3 + 4) = " + evaluateExpression("2 * (3 + 4)"));

        System.out.println("8 / 2 * (2 + 2) = " + evaluateExpression("8 / 2 * (2 + 2)"));

    }


    public static int evaluateExpression(String expression) {

        TokenStream tokenizer = new TokenStream(expression);

        ExpressionParser parser = new ExpressionParser();

        return parser.parseAndEvaluate(tokenizer).evaluate();

    }

}


class TokenStream {

    private final String expression;

    private int position = 0;


    public TokenStream(String expression) {

        this.expression = expression;

    }


    // Methods for tokenizing the input string, handling parentheses and unary operators...

}


class ExpressionParser {

    private Stack<Expression> stack = new Stack<>();


    public Expression parse(TokenStream tokenizer) throws MalformedExpressionException {

        Token current;

        while (tokenizer.hasNext()) {

            // Logic to handle different types of tokens...

        }

        if (!stack.empty()) throw new MalformedExpressionException();

        return stack.pop().evaluate();

    }

}


class Expression implements Comparable<Expression> {

    private final int value;

    private final boolean isUnary;

    private final String operator;

    private final Stack<Integer> operands = new Stack<>();


    public Expression(int[] values, char op) throws MalformedExpressionException {

        // Constructor logic to handle unary minus and nested expressions...

    }


    @Override

    public int compareTo(Expression other) {

        return Integer.compare(this.value, other.getValue());

   0x5B: '}'

   };

}