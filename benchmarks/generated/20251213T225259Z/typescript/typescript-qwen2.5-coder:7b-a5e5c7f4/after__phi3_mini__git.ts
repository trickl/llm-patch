// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

const isNumber = (char: string) => !isNaN(Number(char));
const isOperator = (char: string) => '+-*/'.includes(char);
const isParenthesis = (char: string) => char === '(' || char === ')';

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let current = '';

    for (let i = 0; i < input.length; i++) {
        const char = input[i];

        if (isNumber(char)) {
            current += char;
        } else if (char === ' ') {
            continue;
        } else if (isOperator(char) || isParenthesis(char)) {
            if (current !== '') {
                tokens.push({ type: 'number', value: current });
                current = '';
            }
            tokens.push({ type: 'operator', value: char });
        } else {
            throw new Error(`Invalid character: ${char}`);
        }
    }

    if (current !== '') {
        tokens.push({ type: 'number', value: current });
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
            return Math.trunc(a / b);
        default:
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
        } else {
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

// CLI example
if (require.main === module) {
    const input = process.argv[2];
    if (!input) {
        console.log('Usage: node expression_evaluator.ts "expression"');
    } else {
        try {
            const result = evaluateExpression(input);
            console.log(`Result: ${result}`);
        } catch (error) {
            console.error(`Error: ${error.message}`);
        }
    }
}

node expression_evaluator.ts "3 + 4 * (2 - 1)"

Result: 9