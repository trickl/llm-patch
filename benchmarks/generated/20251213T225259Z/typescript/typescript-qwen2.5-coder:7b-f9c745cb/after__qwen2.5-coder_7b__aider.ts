// expression_evaluator.ts
import * as fs from 'fs';
import * as process from 'process';

type Token = { type: 'NUMBER' | 'PLUS' | 'MINUS' | 'MUL' | 'DIV' | 'LPAREN' | 'RPAREN' | 'UMINUS'; value?: number };

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let i = 0;

    while (i < input.length) {
        if (/\s/.test(input[i])) {
            i++;
            continue;
        }

        if (/^\d+$/.test(input.slice(i))) {
            const numMatch = input.slice(i).match(/^\d+/);
            tokens.push({ type: 'NUMBER', value: parseInt(numMatch![0], 10) });
            i += numMatch![0].length;
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
        } else {
            throw new Error(`Unexpected character at position ${i}: ${input[i]}`);
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
            default: throw new Error(`Unknown operator: ${op}`);
        }
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
            if (values.length > 0) {
                values[values.length - 1] *= -1;
            } else {
                throw new Error('Invalid unary minus');
            }
        } else if (token.type === 'LPAREN') {
            ops.push(token.type);
        } else if (token.type === 'RPAREN') {
            while (ops.length > 0 && ops[ops.length - 1] !== '(') {
                const op = ops.pop()!;
                const b = values.pop()!;
                const a = values.pop()!;
                values.push(applyOp(a, b, op));
            }
            if (ops.length === 0) throw new Error('Unbalanced parentheses');
            ops.pop(); // Remove '('
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

// Example CLI usage
if (require.main === module) {
    const input = process.argv.slice(2).join(' ');
    if (!input) {
        console.log('Usage: node expression_evaluator.ts <expression>');
    } else {
        try {
            const result = evaluateExpression(input);
            console.log(`Result: ${result}`);
        } catch (error) {
            // Error handling already done in evaluateExpression
        }
    }
}
