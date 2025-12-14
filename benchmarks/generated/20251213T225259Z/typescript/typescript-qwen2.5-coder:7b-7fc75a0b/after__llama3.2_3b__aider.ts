// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

const isNumber = (char: string): boolean => !isNaN(Number(char));
const isOperator = (char: string): boolean => '+-*/'.includes(char);
const isParenthesis = (char: string): boolean => char === '(' || char === ')';

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let i = 0;

    while (i < input.length) {
        if (isNumber(input[i])) {
            let numStr = '';
            while (i < input.length && isNumber(input[i])) {
                numStr += input[i];
                i++;
            }
            tokens.push({ type: 'number', value: numStr });
        } else if (isOperator(input[i]) || isParenthesis(input[i])) {
            tokens.push({ type: 'operator', value: input[i] });
            i++;
        } else {
            i++;
        }
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

// CLI example
if (require.main === module) {
    const input = process.argv[2] || '3 + 4 * (2 - 1)';
    try {
        console.log(`Result: ${evaluateExpression(input)}`);
    } catch (error) {
        console.error(`Error: ${error.message}`);
    }
}
