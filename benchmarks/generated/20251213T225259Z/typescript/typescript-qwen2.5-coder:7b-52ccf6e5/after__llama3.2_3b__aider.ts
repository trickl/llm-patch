// expression_evaluator.ts

type Token = number | '+' | '-' | '*' | '/' | '(' | ')' | 'u';

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let i = 0;

    while (i < input.length) {
        if (input[i] === ' ') {
            i++;
            continue;
        }

        if (!isNaN(Number(input[i]))) {
            const num = Number(input[i]);
            i++;
            while (i < input.length && !isNaN(num)) {
                num = num * 10 + Number(input[i]);
                i++;
            }
            tokens.push(num);
    } else if ('+-*/()'.includes(input[i])) {
        const token = input[i];
        tokens.push(token);
        i++;
    } else if (input[i] === '-') {
        if (i === 0 || input[i - 1] === '(') {
            tokens.push('u');
        } else {
            const token = '-';
            tokens.push(token);
        i++;
        } else {
            throw new Error(`Unexpected character: ${token}`);
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

    function greaterPrecedence(op1: string, op2: string): boolean {
        if (op1 === '*' || op1 === '/') return true;
        if (op2 === '+' || op2 === '-') return true;
        return false;
    }

    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];

        if (typeof token === 'number') {
            values.push(token);
        } else if (token === '(') {
            ops.push(token);
        } else if (token === ')') {
            while (ops[ops.length - 1] !== '(') {
                values.push(applyOp(values.pop()!, values.pop()!, ops.pop()!));
            }
            ops.pop();
        } else if (token === 'u') {
            values.push(-values.pop()!);
        } else {
            while (ops.length && greaterPrecedence(ops[ops.length - 1], token)) {
                values.push(applyOp(values.pop()!, values.pop()!, ops.pop()!));
            }
            ops.push(token);
        }
    }

    while (ops.length) {
        values.push(applyOp(values.pop()!, values.pop()!, ops.pop()!));
    }

    return values;
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    const result = parse(tokens);
    if (result.length !== 1) throw new Error('Invalid expression');
    return result[0];
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
