// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis', value: string };

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let i = 0;

    while (i < input.length) {
        if (/\s/.test(input[i])) {
            i++;
            continue;
        }

        if (/[-+\/*()]/.test(input[i])) {
            tokens.push({ type: 'operator', value: input[i] });
            i++;
            continue;
        }

        if (/^\d+$/.test(input.slice(i))) {
            const numStart = i;
            while (i < input.length && /^\d+$/.test(input[i])) {
                i++;
            }
            tokens.push({ type: 'number', value: input.slice(numStart, i) });
            continue;
        }

        throw new Error(`Unexpected character at position ${i}`);
    }

    return tokens;
}

function parse(tokens: Token[]): number[] {
    const values: number[] = [];
    const operators: string[] = [];

    function applyOperator() {
        const operator = operators.pop();
        if (!operator) return;

        const b = values.pop();
        const a = values.pop();

        switch (operator) {
            case '+': values.push(a + b); break;
            case '-': values.push(a - b); break;
            case '*': values.push(a * b); break;
            case '/': values.push(Math.floor(a / b)); break;
        }
    }

    for (const token of tokens) {
        if (token.type === 'number') {
            values.push(parseInt(token.value, 10));
        } else if (token.type === 'operator') {
            while (
                operators.length > 0 &&
                precedence(operators[operators.length - 1]) >= precedence(token.value)
            ) {
                applyOperator();
            }
            operators.push(token.value);
        } else if (token.value === '(') {
            operators.push(token.value);
        } else if (token.value === ')') {
            while (operators.length > 0 && operators[operators.length - 1] !== '(') {
                applyOperator();
            }
            operators.pop(); // Remove the '('
        }
    }

    while (operators.length > 0) {
        applyOperator();
    }

    return values;
}

function precedence(operator: string): number {
    if (operator === '+' || operator === '-') return 1;
    if (operator === '*' || operator === '/') return 2;
    return 0;
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