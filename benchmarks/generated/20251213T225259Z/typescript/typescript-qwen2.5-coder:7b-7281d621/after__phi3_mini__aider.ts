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
        } else if (char === ' ') {
            continue;
        } else if (isOperator(char) || isParenthesis(char)) {
            if (currentToken !== '') {
                tokens.push({ type: 'number', value: currentToken });
                currentToken = '';
            }
            tokens.push({ type: 'operator', value: char });
        } else {
            throw new Error(`Unexpected character: ${char}`);
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
        switch (token.type) {
            case 'number':
                values.push(Number(token.value));
                break;
            case 'operator':
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
                break;
            case 'parenthesis':
                if (token.value === '(') {
                    operators.push(token.value);
                } else {
                    while (operators.length > 0 && operators[operators.length - 1] !== '(') {
                        const operator = operators.pop()!;
                        const b = values.pop()!;
                        const a = values.pop()!;
                        values.push(applyOperator(a, b, operator));
                    }
                    if (operators.length === 0) {
                        throw new Error('Unbalanced parentheses');
                    }
                    operators.pop(); // Remove '('
                }
                break;
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

function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    const result = parse(tokens);
    if (result.length !== 1) {
        throw new Error('Invalid expression');
    }
    return result[0];
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

function applyOperator(a: number, b: number, operator: string): number {
    switch (operator) {
        case '+':
            return a + b;
        case '-':
            return a - b;
        case '*':
            return a * b;
        case '/':
            if (b === 0) {
                throw new Error('Division by zero');
            }
            return Math.floor(a / b);
        default:
            throw new Error(`Unknown operator: ${operator}`);
    }
}

// Example CLI usage
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
        process.exit(1);
    }
}