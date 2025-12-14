// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let i = 0;

    while (i < input.length) {
        if (/\s/.test(input[i])) {
            i++;
            continue;
        }

        if (/[\d]/.test(input[i])) {
            let num = '';
            while (i < input.length && /\d/.test(input[i])) {
                num += input[i];
                i++;
            }
            tokens.push({ type: 'number', value: num });
        } else if (/[-+*/()]/.test(input[i])) {
            tokens.push({ type: 'operator', value: input[i] });
            i++;
        } else {
            throw new Error(`Unexpected character at position ${i}`);
        }
    }

    return tokens;
}

function parse(tokens: Token[]): number[] {
    const values: number[] = [];
    const operators: string[] = [];

    function applyOp(a: number, b: number, op: string): number {
        switch (op) {
            case '+': return a + b;
            case '-': return a - b;
            case '*': return a * b;
            case '/': return Math.floor(a / b);
            default: throw new Error(`Unknown operator ${op}`);
        }
    }

    function greaterPrecedence(op1: string, op2: string): boolean {
        if (op1 === '*' || op1 === '/') return true;
        if (op2 === '+' || op2 === '-') return true;
        return false;
    }

    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];

        if (token.type === 'number') {
            values.push(parseInt(token.value, 10));
        } else if (token.value === '(') {
            operators.push(token.value);
        } else if (token.value === ')') {
            while (operators.length && operators[operators.length - 1] !== '(') {
                const op = operators.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOp(a, b, op));
            }
            operators.pop(); // Remove '('
        } else {
            while (operators.length && greaterPrecedence(operators[operators.length - 1], token.value)) {
                const op = operators.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOp(a, b, op));
            }
            operators.push(token.value);
        }
    }

    while (operators.length) {
        const op = operators.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOp(a, b, op));
    }

    return values;
}

export function evaluateExpression(input: string): number {
    try {
        const tokens = tokenize(input);
        const result = parse(tokens);
        if (result.length !== 1) throw new Error('Invalid expression');
        return result[0];
    } catch (error) {
        console.error(`Error evaluating expression: ${error.message}`);
        return NaN;
    }
}

// Example CLI usage
if (require.main === module) {
    const input = process.argv.slice(2).join(' ');
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