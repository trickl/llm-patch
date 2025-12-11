import java.util.*;


public class ExpressionEvaluator {

    public static void main(String[] args) {

        // Smoke tests to demonstrate functionality

        System.out.println("1 + 2 = " + evaluateExpression("1 + 2"));         // Expected: 3

        System.out.println("2 * 3 + 4 = " + evaluateExpression("2 * 3 + 4")); // Expected: 10

        System.out.println("2 * (3 + 4) = " + evaluateExpression("2 * (3 + 4)")); // Expected: 14

        System.out.println("8 / 2 * (2 + 2) = " + evaluateExpression("8 / 2 * (2 + 2)")); // Expected: 16

    }


    public static int evaluateExpression(String expression) {

        TokenStream tokenizer = new InfixTokenizer(expression);

        ParseTree parseTree = Parser.parse(tokenizer);

        return Evaluator.evaluate(parseTree);

    }

}


class ExpressionEvaluatorTester {

    public static void main(String[] args) {

        // Test cases with expected results for demonstration purposes

        System.out.println("1 + 2 = " + evaluateExpression("1 + 2"));         // Expected: 3

        System.out.println("2 * 3 + 4 = " + evaluateExpression("2 * 3 + 4")); // Expected: 10

        System.out.println("2 * (3 + 4) = " + evaluateExpression("2 * (3 + 4)")); // Expected: 14

        System.out.println("8 / 2 * (2 + 2) = " + evaluateExpression("8 / 2 * (2 + 2)")); // Expected: 16

    }

}