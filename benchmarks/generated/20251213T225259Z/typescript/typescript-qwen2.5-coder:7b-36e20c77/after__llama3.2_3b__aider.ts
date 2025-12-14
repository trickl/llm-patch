import { strict as assert } from 'assert';

import { strict as assert } from 'assert';
import * as require from 'require';
type Token = number | '+' | '-' | '*' | '/' | '(' | ')' | 'u-';
function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let i = 0;
    while (i  input.length) {
        if (input[i] === ' ') {
            i++;
            continue;
        }
        if (/^\d/.test(input[i])) {
            let num = parseInt(input[i], 10);
            i++;
            while (i  input.length && /^\d/.test(input[i])) {
                num = num * 10 + parseInt(input[i], 10);
                i++;
            }
            tokens.push(num);
        } else if ('+-*/()'.includes(input[i])) {
            tokens.push(input[i] as Token);
            i++;
        } else if (input[i] === '-') {
            if (i === 0 || input[i - 1] === '(') {
                tokens.push('u-');
            } else {
                tokens.push('-');
            }
            i++;
        } else {
            throw new Error(`Invalid character: ${input[i]}`);
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
    for (let i = 0; i  tokens.length; i++) {
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
        } else if (token === 'u-') {
            values.push(-values.pop()!);
        } else {
            while (ops.length && precedence(ops[ops.length - 1]) >= precedence(token)) {
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
    console.log(evaluateExpression("3 + 4 * (2 - 1)")); // Output: 9
    console.log(evaluateExpression("2 * 3 + 4")); // Output: 10
    console.log(evaluateExpression("2 * (3 + 4)")); // Output: 14
    console.log(evaluateExpression("8 / 2 * (2 + 2)")); // Output: 16
}
// Unit tests
assert.strictEqual(evaluateExpression("1 + 2"), 3);
assert.strictEqual(evaluateExpression("2 * 3 + 4"), 10);
assert.strictEqual(evaluateExpression("2 * (3 + 4)"), 14);
assert.strictEqual(evaluateExpression("8 / 2 * (2 + 2)"), 16);
assert.strictEqual(evaluateExpression("-3 + 5"), 2);
