// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

const isNumber = (char: string) => !isNaN(Number(char));
const isOperator = (char: string) => '+-*/'.includes(char);
const isParenthesis = (char: string) => char === '(' || char === ')';

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let currentToken = '';
    // Add this line to import the module
    const module = require('module');
    for (let i = 0; i < input.length; i++) {
        const char = input[i];

        if (isNumber(char)) {
            currentToken += char;
        } else if (isOperator(char) || isParenthesis(char)) {
            if (currentToken !== '') {
                tokens.push({ type: 'number', value: currentToken });
                currentToken = '';
            }
            tokens.push({ type: 'operator', value: char });
        } else if (char === ' ') {
            continue;
        } else {
            throw new Error(`Invalid character: ${char}`);
        }
    }

    if (currentToken !== '') {
        tokens.push({ type: 'number', value: currentToken });
    }

    return tokens;
}

function precedence(operator: string): number {
    switch (operator) {
        case '+':
        case '-':
            return 1;
        case '*':
        case '/':
            return 2;
        default:
            throw new Error(`Unknown operator: ${operator}`);
    }
}

function applyOperator(operators: string[], values: number[]): number {
    const operator = operators.pop()!;
    const right = values.pop()!;
    const left = values.pop()!;

    switch (operator) {
        case '+':
            return left + right;
        case '-':
            return left - right;
        case '*':
            return left * right;
        case '/':
            if (right === 0) throw new Error('Division by zero');
            return Math.trunc(left / right);
        default:
            throw new Error(`Unknown operator: ${operator}`);
    }
}

function evaluate(tokens: Token[]): number {
    const values: number[] = [];
    const operators: string[] = [];

    for (const token of tokens) {
        if (token.type === 'number') {
            values.push(Number(token.value));
        } else if (token.value === '(') {
            operators.push(token.value);
        } else if (token.value === ')') {
            while (operators.length > 0 && operators[operators.length - 1] !== '(') {
                values.push(applyOperator(operators, values));
            }
            operators.pop(); // Remove the '('
        } else {
            while (
                operators.length > 0 &&
                precedence(operators[operators.length - 1]) >= precedence(token.value)
            ) {
                values.push(applyOperator(operators, values));
            }
            operators.push(token.value);
        }
    }

    while (operators.length > 0) {
        values.push(applyOperator(operators, values));
    }

    return values.pop()!;
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    return evaluate(tokens);
}

// CLI example
if (require.main === module) {
    const input = process.argv[2];
    if (!input) {
        console.error('Usage: node expression_evaluator.ts "expression"');
        process.exit(1);
    }
    try {
        const result = evaluateExpression(input);
        console.log(result);
    } catch (error) {
        console.error(`Error evaluating expression: ${error.message}`);
    }
}
