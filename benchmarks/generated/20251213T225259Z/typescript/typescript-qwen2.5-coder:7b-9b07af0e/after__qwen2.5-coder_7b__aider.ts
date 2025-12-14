// expression_evaluator.ts
// expression_evaluator.ts
import * as process from 'process';
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
                num += input[i];
                i++;
            }
            tokens.push({ type: 'number', value: num });
        } else if (/[-+*/()]/.test(input[i])) {
            tokens.push({ type: 'operator', value: input[i] });
            i++;
        } else {
            throw new Error(`Unexpected character at position ${i}`);
        }
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

    for (const token of tokens) {
        switch (token.type) {
            case 'number':
                values.push(parseInt(token.value, 10));
                break;
            case 'operator':
                while (
                    operators.length > 0 &&
                    precedence(operators[operators.length - 1]) >= precedence(token.value)
                ) {
                    applyOperator();
                }
                operators.push(token.value);
                break;
            case 'parenthesis':
                if (token.value === '(') {
                    operators.push(token.value);
                } else {
                    while (operators.length > 0 && operators[operators.length - 1] !== '(') {
                        applyOperator();
                    }
                    operators.pop(); // Remove '('
                }
                break;
        }
    }

    while (operators.length > 0) {
        applyOperator();
    }

    return values;
}

function precedence(operator: string): number {
    switch (operator) {
        case '+':
        case '-':
            return 1;
        case '*':
        case '/':
            return 2;
        default:
            return 0;
    }
}

export function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    const result = parse(tokens);
    if (result.length !== 1) throw new Error('Invalid expression');
    return result[0];
}

// CLI example
if (require.main === module) {
    const input = process.argv.slice(2).join(' ');
    try {
        console.log(evaluateExpression(input));
    } catch (error: unknown) {
        console.error(`Error: ${error.message}`);
    }
}
