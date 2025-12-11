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

        if (isNumber(char)) {
            currentToken += char;
        } else if (isOperator(char) || isParenthesis(char)) {
            if (currentToken !== '') {
                tokens.push({ type: 'number', value: currentToken });
                currentToken = '';
            }
            tokens.push({ type: 'operator' | 'parenthesis', value: char });
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

function parse(tokens: Token[]): number[] {
    const values: number[] = [];
    const operators: string[] = [];

    for (const token of tokens) {
        if (token.type === 'number') {
            values.push(Number(token.value));
        } else if (token.type === 'operator' || token.type === 'parenthesis') {
            while (
                operators.length > 0 &&
                precedence(operators[operators.length - 1]) >= precedence(token.value)
            ) {
                const operator = operators.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOperation(a, b, operator));
            }
            if (token.value !== ')') {
                operators.push(token.value);
            } else {
                while (operators.length > 0 && operators[operators.length - 1] !== '(') {
                    const operator = operators.pop()!;
                    const b = values.pop()!;
                    const a = values.pop()!;
                    values.push(applyOperation(a, b, operator));
                }
                operators.pop(); // Remove '('
            }
        }
    }

    while (operators.length > 0) {
        const operator = operators.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOperation(a, b, operator));
    }

    return values;
}

function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    return parse(tokens)[0];
}

function precedence(operator: string): number {
    if (operator === '+' || operator === '-') return 1;
    if (operator === '*' || operator === '/') return 2;
    throw new Error(`Unknown operator: ${operator}`);
}

function applyOperation(a: number, b: number, operator: string): number {
    switch (operator) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return Math.floor(a / b);
        default: throw new Error(`Unknown operator: ${operator}`);
    }
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