// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

const tokenize = (input: string): Token[] => {
    const tokens: Token[] = [];
    let i = 0;

    while (i < input.length) {
        if (/\s/.test(input[i])) {
            i++;
            continue;
        }

        if (/[\d-]/.test(input[i])) {
            let numStr = input[i];
            while (i + 1 < input.length && /\d/.test(input[i + 1])) {
                numStr += input[++i];
            }
            tokens.push({ type: 'number', value: numStr });
        } else if (/[\+\-\*\/\(\)]/.test(input[i])) {
            tokens.push({ type: 'operator', value: input[i] });
        } else if (/\)/.test(input[i])) {
            tokens.push({ type: 'parenthesis', value: ')' });
        }

        i++;
    }

    return tokens;
};

const precedence = (op: string): number => {
    switch (op) {
        case '+':
        case '-':
            return 1;
        case '*':
        case '/':
            return 2;
        default:
            return 0;
    }
};

const applyOp = (a: number, b: number, op: string): number => {
    switch (op) {
        case '+':
            return a + b;
        case '-':
            return a - b;
        case '*':
            return a * b;
        case '/':
            if (b === 0) throw new Error('Division by zero');
            return Math.floor(a / b);
        default:
            throw new Error(`Unknown operator: ${op}`);
    }
};

const evaluate = (tokens: Token[]): number => {
    const values: number[] = [];
    const ops: string[] = [];

    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];

        if (token.type === 'number') {
            values.push(parseInt(token.value, 10));
        } else if (token.type === 'operator') {
            while (
                ops.length > 0 &&
                precedence(ops[ops.length - 1]) >= precedence(token.value)
            ) {
                const op = ops.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOp(a, b, op));
            }
            ops.push(token.value);
        } else if (token.type === 'parenthesis' && token.value === '(') {
            ops.push(token.value);
        } else if (token.type === 'parenthesis' && token.value === ')') {
            while (ops.length > 0 && ops[ops.length - 1] !== '(') {
                const op = ops.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOp(a, b, op));
            }
            if (ops.length === 0 || ops.pop() !== '(') throw new Error('Mismatched parentheses');
        }
    }

    while (ops.length > 0) {
        const op = ops.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOp(a, b, op));
    }

    return values[0];
};

export function evaluateExpression(input: string): number {
    try {
        const tokens = tokenize(input);
        return evaluate(tokens);
    } catch (error) {
        throw new Error(`Malformed expression: ${input}`);
    }
}

// CLI example
if (require.main === module) {
    const input = process.argv[2];
    if (!input) {
        console.log('Usage: node expression_evaluator.ts "expression"');
        process.exit(1);
    }

    try {
        const result = evaluateExpression(input);
        console.log(`Result: ${result}`);
    } catch (error) {
        console.error(error.message);
    }
}