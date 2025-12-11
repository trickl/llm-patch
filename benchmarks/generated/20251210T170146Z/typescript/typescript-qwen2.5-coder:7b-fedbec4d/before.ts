// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

const isNumber = (char: string) => !isNaN(Number(char));
const isOperator = (char: string) => '+-*/'.includes(char);
const isParenthesis = (char: string) => char === '(' || char === ')';

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let currentNumber = '';

    for (let i = 0; i < input.length; i++) {
        const char = input[i];

        if (isNumber(char)) {
            currentNumber += char;
            continue;
        }

        if (currentNumber !== '') {
            tokens.push({ type: 'number', value: currentNumber });
            currentNumber = '';
        }

        if (char === ' ') continue;

        if (isOperator(char) || isParenthesis(char)) {
            tokens.push({ type: 'operator', value: char });
        }
    }

    if (currentNumber !== '') {
        tokens.push({ type: 'number', value: currentNumber });
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
            return 0;
    }
}

function applyOperation(operators: string[], values: number[]): number {
    const operator = operators.pop()!;
    const b = values.pop()!;
    const a = values.pop()!;

    switch (operator) {
        case '+':
            return a + b;
        case '-':
            return a - b;
        case '*':
            return a * b;
        case '/':
            if (b === 0) throw new Error('Division by zero');
            return Math.trunc(a / b);
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
        } else if (token.type === 'operator') {
            while (
                operators.length > 0 &&
                precedence(operators[operators.length - 1]) >= precedence(token.value)
            ) {
                values.push(applyOperation(operators, values));
            }
            operators.push(token.value);
        } else if (token.value === '(') {
            operators.push(token.value);
        } else if (token.value === ')') {
            while (operators[operators.length - 1] !== '(') {
                values.push(applyOperation(operators, values));
            }
            operators.pop(); // Remove the '('
        }
    }

    while (operators.length > 0) {
        values.push(applyOperation(operators, values));
    }

    return values[0];
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    return evaluate(tokens);
}

// Example CLI usage:
if (require.main === module) {
    console.log(evaluateExpression('1 + 2')); // Output: 3
    console.log(evaluateExpression('2 * 3 + 4')); // Output: 10
    console.log(evaluateExpression('2 * (3 + 4)')); // Output: 14
    console.log(evaluateExpression('8 / 2 * (2 + 2)')); // Output: 16
}