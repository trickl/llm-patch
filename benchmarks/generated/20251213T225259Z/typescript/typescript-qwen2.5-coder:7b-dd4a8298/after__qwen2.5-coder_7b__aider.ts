// expression_evaluator.ts

import * as process from 'process';
type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

const isNumber = (char: string): boolean => !isNaN(Number(char));
const isOperator = (char: string): boolean => '+-*/'.includes(char);
const isParenthesis = (char: string): boolean => char === '(' || char === ')';

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let currentToken = '';

    for (let i = 0; i < input.length; i++) {
        const char = input[i];

        if (isNumber(char)) {
            currentToken += char;
            continue;
        }

        if (currentToken) {
            tokens.push({ type: 'number', value: currentToken });
            currentToken = '';
        }

        if (isOperator(char) || isParenthesis(char)) {
            tokens.push({ type: 'operator', value: char });
        }
    }

    if (currentToken) {
        tokens.push({ type: 'number', value: currentToken });
    }

    return tokens;
}

function parse(tokens: Token[]): number[] {
    const values: number[] = [];
    const operators: string[] = [];

    for (const token of tokens) {
        if (token.type === 'number') {
            values.push(Number(token.value));
        } else if (token.type === 'operator') {
            while (
                operators.length > 0 &&
                precedence(operators[operators.length - 1]) >= precedence(token.value)
            ) {
                const operator = operators.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOperator(a, b, operator));
            }
            operators.push(token.value);
        } else if (token.type === 'parenthesis' && token.value === '(') {
            operators.push(token.value);
        } else if (token.type === 'parenthesis' && token.value === ')') {
            while (operators.length > 0 && operators[operators.length - 1] !== '(') {
                const operator = operators.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOperator(a, b, operator));
            }
            operators.pop(); // Remove the '('
        }
    }

    while (operators.length > 0) {
        const operator = operators.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOperator(a, b, operator));
    }

    return values;
}

function precedence(operator: string): number {
    if (operator === '+' || operator === '-') return 1;
    if (operator === '*' || operator === '/') return 2;
    return 0;
}

function applyOperator(a: number, b: number, operator: string): number {
    switch (operator) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return Math.floor(a / b);
        default: throw new Error(`Unknown operator: ${operator}`);
    }
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    const parsedValues = parse(tokens);
    if (parsedValues.length !== 1) throw new Error('Invalid expression');
    return parsedValues[0];
}

// Example CLI usage
if (process.mainModule === module) {
    const input = process.argv.slice(2).join(' ');
    try {
        console.log(evaluateExpression(input));
    } catch (error) {
        console.error(`Error: ${error.message}`);
    }
}
