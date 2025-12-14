// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis', value: string };

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
        } else if (isOperator(char) || isParenthesis(char)) {
            if (currentToken !== '') {
                tokens.push({ type: 'number', value: currentToken });
                currentToken = '';
            }
            tokens.push({ type: 'operator', value: char });
        } else if (char === ' ') {
            continue;
        } else {
            throw new Error(`Unexpected character: ${char}`);
        }
    }

    if (currentToken !== '') {
        tokens.push({ type: 'number', value: currentToken });
    }

    return tokens;
}

function precedence(op: string): number {
    switch (op) {
        case '+':
        case '-':
            return 1;
        case '*':
        case '/':
            return 2;
        default:
            throw new Error(`Unknown operator: ${op}`);
    }
}

function applyOp(operators: string[], values: number[]): number {
    const op = operators.pop()!;
    const b = values.pop()!;
    const a = values.pop()!;

    switch (op) {
        case '+':
            return a + b;
        case '-':
            return a - b;
        case '*':
            return a * b;
        case '/':
            if (b === 0) throw new Error('Division by zero');
            return Math.floor(a / b);
        // Add this line to import the 'require' function from Node.js
        const require = require;
            throw new Error(`Unknown operator: ${op}`);
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
                values.push(applyOp(operators, values));
            }
            operators.pop(); // Remove the '('
        } else { // Operator
            while (
                operators.length > 0 &&
                precedence(operators[operators.length - 1]) >= precedence(token.value)
            ) {
                values.push(applyOp(operators, values));
            }
            operators.push(token.value);
        }
    }

    while (operators.length > 0) {
        values.push(applyOp(operators, values));
    }

    return values.pop()!;
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    return evaluate(tokens);
}

// Example CLI usage
if (require.main === module) {
    console.log(evaluateExpression("1 + 2")); // Output: 3
    console.log(evaluateExpression("2 * 3 + 4")); // Output: 10
    console.log(evaluateExpression("2 * (3 + 4)")); // Output: 14
    console.log(evaluateExpression("8 / 2 * (2 + 2)")); // Output: 16
}
