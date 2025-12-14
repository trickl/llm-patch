// expression_evaluator.ts

function tokenize(input: string): string[] {
    return input.match(/[-+]?\d*\.?\d+|\(|\)|\*|\/|\+/g) || [];
}

function parse(tokens: string[]): number[] {
    const values: number[] = [];
    const ops: string[] = [];

    tokens.forEach(token => {
        if (!isNaN(Number(token))) {
            values.push(Number(token));
        } else if (token === '(') {
            ops.push(token);
        } else if (token === ')') {
            while (ops.length > 0 && ops[ops.length - 1] !== '(' && hasPrecedence(ops[ops.length - 1], token)) {            applyOp(values, ops);
            }
            ops.pop(); // Remove the '('
        } else {
            while (
                ops.length > 0 &&
                hasPrecedence(ops[ops.length - 1], token)
            ) {
                applyOp(values, ops);
            }
            ops.push(token);
        }
    });

    while (ops.length > 0) {
        applyOp(values, ops);
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

function hasPrecedence(op1: string, op2: string): boolean {
    if ((op1 === '*' || op1 === '/') && (op2 === '+' || op2 === '-')) {
        return false;
    }
    return true;
}

function applyOp(values: number[], ops: string[]): void {
    const b = values.pop()!;
    const a = values.pop()!;
    switch (ops.pop()!) {
        case '+':
            values.push(a + b);
            break;
        case '-':
            values.push(a - b);
            break;
        case '*':
            values.push(a * b);
            break;
        case '/':
            if (b === 0) throw new Error('Division by zero');
            values.push(Math.floor(a / b));
            break;
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
            console.log(result);
        } catch (error) {
            console.error(`Error evaluating expression: ${error.message}`);
        }
    }
}

node expression_evaluator.ts "3 + 4 * (2 - 1)"