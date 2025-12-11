import java.util.*;


public class ExpressionEvaluator {

    public static void main(String[] args) {

        // Smoke tests to demonstrate functionality

        System.out.println("1 + 2 = " + evaluateExpression("1 + 2"));

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