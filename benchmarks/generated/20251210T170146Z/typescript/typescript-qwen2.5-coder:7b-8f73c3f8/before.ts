// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

const isNumber = (char: string): boolean => !isNaN(Number(char));
const isOperator = (char: string): boolean => '+-*/'.includes(char);
const isParenthesis = (char: string): boolean => char === '(' || char === ')';

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let currentToken = '';

    for (let i = 0; i < input.length; i++) {
        const char = input[i];

        if (isNumber(char) || (char === '-' && (i === 0 || isOperator(input[i - 1])))) {
            currentToken += char;
        } else if (isOperator(char) || isParenthesis(char)) {
            if (currentToken !== '') {
                tokens.push({ type: 'number', value: currentToken });
                currentToken = '';
            }
            tokens.push({ type: 'operator' | 'parenthesis', value: char });
        }
    }

    if (currentToken !== '') {
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
        } else if (token.value === '(') {
            operators.push(token.value);
        } else if (token.value === ')') {
            while (operators.length > 0 && operators[operators.length - 1] !== '(') {
                const operator = operators.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOperator(a, b, operator));
            }
            operators.pop(); // Remove the '('
        } else {
            while (
                operators.length > 0 &&
                precedence(token.value) <= precedence(operators[operators.length - 1])
            ) {
                const operator = operators.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOperator(a, b, operator));
            }
            operators.push(token.value);
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

function applyOperator(a: number, b: number, operator: string): number {
    switch (operator) {
        case '+':
            return a + b;
        case '-':
            return a - b;
        case '*':
            return a * b;
        case '/':
            if (b === 0) throw new Error('Division by zero');
            return Math.floor(a / b);
        default:
            throw new Error(`Unknown operator: ${operator}`);
    }
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

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    const result = parse(tokens);
    if (result.length !== 1) throw new Error('Invalid expression');
    return result[0];
}

// CLI example
if (require.main === module) {
    const input = process.argv.slice(2).join(' ');
    try {
        console.log(evaluateExpression(input));
    } catch (error) {
        console.error(`Error: ${error.message}`);
    }
}