import java.util.*;


public class ExpressionEvaluator {

    public static void main(String[] args) {

        // Smoke tests

        System.out.println("3 + 4 * (2 - 1) = " + evaluateExpression("3 + 4 * (2 - 1)"));

        System.out.println("2 * 3 + 4 = " + evaluateExpression("2 * 3 + 4"));

        System.out.println("2 * (3 + 4) = " + evaluateExpression("2 * (3 + 4)"));

        System.out.println("8 / 2 * (2 + 2) = " + evaluateExpression("8 / 2 * (2 + 2)"));

    }


    public static int evaluateExpression(String expression) {

        TokenStream tokenizer = new InfixTokenizer(expression);

        ParseTree parseTree = Parser.parse(tokenizer);

        return Evaluator.evaluate(parseTree);

    }

}


class InfixTokenizer {

    private Deque<String> tokens;


    public InfixTokenizer(String expression) {

        Scanner scanner = new Scanner(expression).useDelimiter("\\s*(\\+|-|\\*|/|\\(|\\)|\\d+)");

        while (scanner.hasNext()) {

            String token = scanner.next();

            if (!token.isEmpty() && !isOperator(token)) {

                tokens.push(token); // Unary minus handling is not implemented in this snippet for brevity

            } else if (tokens.size() == 0 || tokens.peek().equals("(") || tokens.peek().equals(")")) {

                tokens.push(token);

            } else {

                throw new IllegalArgumentException("Malformed expression: " + token);

           s = scanner.next(); // Unary minus handling is not implemented in this snippet for brevity

        while (scanner.hasNext()) {

            StringTokenizer st = new StringTokenizer(input, "+-*/()", true);

            TokenStream tokenizer = new InfixTokenizer(st.nextToken()); // Recursive descent parser setup

            ParseTree parseTree = Parser.parse(tokenizer);

            int result = Evaluator.evaluate(parseTree);

            System.out.println("Result: " + result);

        }

    } else {

        throw new IllegalArgumentException("Malformed expression");

    }

}