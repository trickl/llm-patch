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

        ExpressionParser parser = new BinaryExpressionParser();

        return evaluator.evaluate(parser, tokenizer).getResult();

    }

}


class InfixTokenizer {

    private Deque<String> tokens;


    public InfixTokenizer(String expression) {

        this.tokens = new LinkedList<>();

        // Tokenize the input string into numbers, operators, and parentheses

        int currentCharIndex = 0;

        while (currentCharIndex < expression.length()) {

            char c = expression.charAt(currentCharIndex);

            if (Character.isDigit(c)) {

                String number = "";

                do {

                    number += c;

                    currentCharIndex++;

                } while (Character.isDigit(expression.charAt(currentCharIndex)));

                tokens.push(number);

            } else if (c == '+' || c == '-' || c == '*' || c == '/') {

                String operator = "" + c;

                tokens.push(operator);

            } else if (c == '(') {

                tokens.push("(");

            } else if (c == ')') {

                while (!tokens.peek().equals("(")) {

                    String token = tokens.pop();

                    System.out.print(token + " "); // For demonstration purposes, print the tokens as they are parsed

               04-15 12:34:56] [ERROR   ] Failed to evaluate expression 'a * (b - c) / d' due to unexpected token sequence or syntax error. Please check your input and try again.

[04-15 12:34:57] [INFO    ] Expression evaluation complete with result: 6 for the test case "2 + 4 * (8 - 3) / 2".