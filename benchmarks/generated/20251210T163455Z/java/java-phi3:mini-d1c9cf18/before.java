import java.util.ArrayDeque;

import java.util.Queue;


public class ExpressionEvaluator {

    public static void main(String[] args) {

        // Smoke tests for the evaluator functionality

        System.out.println("3 + 4 * (2 - 1) = " + evaluateExpression("3 + 4 * (2 - 1)"));

        System.out.println("2 * 3 + 4 = " + evaluateExpression("2 * 3 + 4"));

        System.out.println("2 * (3 + 4) = " + evaluateExpression("2 * (3 + 4)"));

        System.out.println("8 / 2 * (2 + 2) = " + evaluateExpression("8 / 2 * (2 + 2)"));

    }


    public static int evaluateExpression(String expression) {

        Tokenizer tokenizer = new Tokenizer(expression);

        Queue<Token> tokens = tokenizer.tokenize();

        Parser parser = new Parser(tokens);

        return evaluator.evaluate(parser.parse());

    }

}