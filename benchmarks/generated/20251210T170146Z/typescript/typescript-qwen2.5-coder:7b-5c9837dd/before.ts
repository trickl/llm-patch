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
                num += input[i++];
            }
            tokens.push({ type: 'number', value: num });
        } else if (/\+|\-|\*|\/|\(|\)/.test(input[i])) {
            tokens.push({ type: 'operator', value: input[i++] });
        } else {
            throw new Error(`Unexpected character at position ${i}`);
        }
    }

    return tokens;
}

function parse(tokens: Token[]): number[] {
    const values: number[] = [];
    const ops: string[] = [];

    function applyOp(a: number, b: number, op: string): number {
        switch (op) {
            case '+': return a + b;
            case '-': return a - b;
            case '*': return a * b;
            case '/': return Math.floor(a / b);
            default: throw new Error(`Unknown operator ${op}`);
        }
    }

    function precedence(op: string): number {
        if (op === '+' || op === '-') return 1;
        if (op === '*' || op === '/') return 2;
        return 0;
    }

    for (const token of tokens) {
        if (token.type === 'number') {
            values.push(Number(token.value));
        } else if (token.value === '(') {
            ops.push(token.value);
        } else if (token.value === ')') {
            while (ops.length && ops[ops.length - 1] !== '(') {
                const b = values.pop()!;
                const a = values.pop()!;
                const op = ops.pop()!;
                values.push(applyOp(a, b, op));
            }
            ops.pop(); // Remove '('
        } else if (token.type === 'operator') {
            while (ops.length && precedence(ops[ops.length - 1]) >= precedence(token.value)) {
                const b = values.pop()!;
                const a = values.pop()!;
                const op = ops.pop()!;
                values.push(applyOp(a, b, op));
            }
            ops.push(token.value);
        }
    }

    while (ops.length) {
        const b = values.pop()!;
        const a = values.pop()!;
        const op = ops.pop()!;
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
        console.error(`Error evaluating expression: ${input}`);
        throw error;
    }
}

// CLI example
if (require.main === module) {
    const input = process.argv[2] || '3 + 4 * (2 - 1)';
    try {
        const result = evaluateExpression(input);
        console.log(`Result: ${result}`);
    } catch (error) {
        console.error('Invalid expression');
    }
}