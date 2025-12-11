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
        } else if (/[-+*/()]/.test(input[i])) {
            tokens.push({ type: 'operator', value: input[i++] });
        } else {
            throw new Error(`Unexpected character: ${input[i]}`);
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
            default: throw new Error(`Invalid operator: ${op}`);
        }
    }

    function precedence(op: string): number {
        if (op === '+' || op === '-') return 1;
        if (op === '*' || op === '/') return 2;
        return 0;
    }

    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];

        if (token.type === 'number') {
            values.push(parseInt(token.value, 10));
        } else if (token.type === 'operator') {
            while (ops.length && precedence(ops[ops.length - 1]) >= precedence(token.value)) {
                const op = ops.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOp(a, b, op));
            }
            ops.push(token.value);
        } else if (token.type === 'parenthesis') {
            if (token.value === '(') {
                ops.push(token.value);
            } else {
                while (ops.length && ops[ops.length - 1] !== '(') {
                    const op = ops.pop()!;
                    const b = values.pop()!;
                    const a = values.pop()!;
                    values.push(applyOp(a, b, op));
                }
                if (ops.length === 0 || ops.pop() !== '(') {
                    throw new Error('Mismatched parentheses');
                }
            }
        }
    }

    while (ops.length) {
        const op = ops.pop()!;
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
        console.error(`Error evaluating expression: ${input}`);
        throw error;
    }
}

// Example CLI usage:
if (require.main === module) {
    const input = process.argv.slice(2).join(' ');
    try {
        const result = evaluateExpression(input);
        console.log(result);
    } catch (error) {
        // Error handling already done in evaluateExpression
    }
}