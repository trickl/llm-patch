// expression_evaluator.ts

type Token = { type: 'NUMBER' | 'PLUS' | 'MINUS' | 'MUL' | 'DIV' | 'LPAREN' | 'RPAREN' | 'UMINUS'; value?: number };

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let i = 0;

    while (i < input.length) {
        if (input[i] === ' ') {
            i++;
            continue;
        }

        if (/\d/.test(input[i])) {
            let num = parseInt(input[i], 10);
            i++;
            while (i < input.length && /\d/.test(input[i])) {
                num = num * 10 + parseInt(input[i], 10);
                i++;
            }
            tokens.push({ type: 'NUMBER', value: num });
        } else if (input[i] === '+') {
            tokens.push({ type: 'PLUS' });
            i++;
        } else if (input[i] === '-') {
            if (i === 0 || input[i - 1] === '(') {
                tokens.push({ type: 'UMINUS' });
            } else {
                tokens.push({ type: 'MINUS' });
            }
            i++;
        } else if (input[i] === '*') {
            tokens.push({ type: 'MUL' });
            i++;
        } else if (input[i] === '/') {
            tokens.push({ type: 'DIV' });
            i++;
        } else if (input[i] === '(') {
            tokens.push({ type: 'LPAREN' });
            i++;
        } else if (input[i] === ')') {
            tokens.push({ type: 'RPAREN' });
            i++;
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
        }
        throw new Error('Invalid operator');
    }

    function precedence(op: string): number {
        if (op === '+' || op === '-') return 1;
        if (op === '*' || op === '/') return 2;
        return 0;
    }

    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];

        if (token.type === 'NUMBER') {
            values.push(token.value!);
        } else if (token.type === 'UMINUS') {
            values.push(-values.pop()!);
        } else if (token.type === 'LPAREN') {
            ops.push(token.type);
        } else if (token.type === 'RPAREN') {
            while (ops[ops.length - 1] !== '(') {
                const op = ops.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOp(a, b, op));
            }
            ops.pop();
        } else {
            while (ops.length > 0 && precedence(ops[ops.length - 1]) >= precedence(token.type)) {
                const op = ops.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOp(a, b, op));
            }
            ops.push(token.type);
        }
    }

    while (ops.length > 0) {
        const op = ops.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOp(a, b, op));
    }

    return values;
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    const result = parse(tokens);
    if (result.length !== 1) throw new Error('Invalid expression');
    return result[0];
}

// Example CLI usage
if (require.main === module) {
    console.log(evaluateExpression("3 + 4 * (2 - 1)")); // Output: 9
    console.log(evaluateExpression("2 * 3 + 4")); // Output: 10
    console.log(evaluateExpression("2 * (3 + 4)")); // Output: 14
    console.log(evaluateExpression("8 / 2 * (2 + 2)")); // Output: 16
}