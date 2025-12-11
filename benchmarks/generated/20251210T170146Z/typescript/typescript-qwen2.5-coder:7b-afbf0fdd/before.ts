// expression_evaluator.ts

function tokenize(input: string): string[] {
    return input.match(/[\d\+\-\*\/\(\)\s]/g)?.filter(Boolean) ?? [];
}

function parse(tokens: string[]): number[] {
    const values: number[] = [];
    const ops: string[] = [];

    for (const token of tokens) {
        if (!isNaN(Number(token))) {
            values.push(Number(token));
        } else if (token === '(') {
            ops.push(token);
        } else if (token === ')') {
            while (ops.length > 0 && ops[ops.length - 1] !== '(') {
                const op = ops.pop();
                if (!op) break;
                values.push(applyOp(values.pop()!, values.pop()!, op));
            }
            ops.pop(); // pop '('
        } else {
            while (ops.length > 0 && hasPrecedence(token, ops[ops.length - 1])) {
                const op = ops.pop();
                if (!op) break;
                values.push(applyOp(values.pop()!, values.pop()!, op));
            }
            ops.push(token);
        }
    }

    while (ops.length > 0) {
        const op = ops.pop();
        if (!op) break;
        values.push(applyOp(values.pop()!, values.pop()!, op));
    }

    return values[0];
}

function applyOp(a: number, b: number, op: string): number {
    switch (op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return Math.floor(a / b);
        default: throw new Error(`Invalid operator: ${op}`);
    }
}

function hasPrecedence(op1: string, op2: string): boolean {
    if (op2 === '(' || op2 === ')') return false;
    if ((op1 === '*' || op1 === '/') && (op2 === '+' || op2 === '-')) return false;
    return true;
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    return parse(tokens);
}

// CLI example
if (require.main === module) {
    console.log(evaluateExpression("1 + 2")); // 3
    console.log(evaluateExpression("2 * 3 + 4")); // 10
    console.log(evaluateExpression("2 * (3 + 4)")); // 14
    console.log(evaluateExpression("8 / 2 * (2 + 2)")); // 16
}