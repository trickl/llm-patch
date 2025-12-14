// expression_evaluator.ts

function tokenize(input: string): string[] {
    return input.match(/[\d\+\-\*\/\(\)]/g) || [];
}

function parse(tokens: string[]): number | null {
    const values: (number | null)[] = [];
    const ops: string[] = [];
    tokens.forEach((token, index): void => {
        if (!isNaN(Number(token))) {
            values.push(Number(token));
        } else if (token === '(') {
            ops.push(token);
        } else if (token === ')') {
            while (ops.length > 0 && ops[ops.length - 1] !== '(') {
                const op = ops.pop();
                if (op) {
                    values.push(applyOp(values.pop(), values.pop() as number, op));
                }
            }
            ops.pop(); // Remove the '('
        } else {
            while (
                ops.length > 0 &&
                hasPrecedence(token, ops[ops.length - 1])
            ) {
                const op = ops.pop();
                if (op) {
                    values.push(applyOp(values.pop(), values.pop() as number, op));
                }
            }
            ops.push(token);
        }
    });

    while (ops.length > 0) {
        const op = ops.pop();
        if (op) {
            values.push(applyOp(values.pop(), values.pop() as number, op));
        }
    }

    return values[0];
}

function applyOp(a: number | null, b: number, op: string): number {
    switch (op) {
        case '+':
            return a! + b;
        case '-':
            return a! - b;
        case '*':
            return a! * b;
        case '/':
            if (b === 0) throw new Error("Division by zero");
            return Math.floor(a! / b);
    }
    throw new Error("Invalid operator");
}

function hasPrecedence(op1: string, op2: string): boolean {
    if ((op1 === '*' || op1 === '/') && (op2 === '+' || op2 === '-')) return false;
    return true;
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    return parse(tokens) as number;
}

// Example CLI usage
if (require.main === module) {
    console.log(evaluateExpression("1 + 2")); // Output: 3
    console.log(evaluateExpression("2 * 3 + 4")); // Output: 10
    console.log(evaluateExpression("2 * (3 + 4)")); // Output: 14
    console.log(evaluateExpression("8 / 2 * (2 + 2)")); // Output: 16
}
