// expression_evaluator.ts

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
            throw new Error(`Unexpected character: ${input[i]}`);
        }
    }

    return tokens;
}

function parse(tokens: Token[]): number[] {
    const values: number[] = [];
    const operators: string[] = [];

    function applyOperator() {
        while (operators.length > 0 && operators[operators.length - 1] !== '(') {
            const op = operators.pop();
            const b = values.pop();
            const a = values.pop();
            if (op === '+') values.push(a + b);
            else if (op === '-') values.push(a - b);
            else if (op === '*') values.push(a * b);
            else if (op === '/') values.push(Math.floor(a / b));
        }
    }

    function greaterPrecedence(op1: string, op2: string): boolean {
        const precedence = { '+': 1, '-': 1, '*': 2, '/': 2 };
        return precedence[op1] > precedence[op2];
    }

    for (const token of tokens) {
        if (token.type === 'number') {
            values.push(parseInt(token.value));
        } else if (token.value === '(') {
            operators.push(token.value);
  } else if (token.value === ')') {
    while (operators.length > 0 && operators[operators.length - 1] !== '(') {
      applyOperator();
    }
    if (token.type === 'parenthesis' && token.value === ')') {
      operators.pop();
    } else {
      throw new Error(`Unexpected character: ${token.value}`);
    }
  } else {
    while (
      operators.length > 0 &&
        operators[operators.length - 1] !== '(' &&
        greaterPrecedence(operators[operators.length - 1], token.value)
    ) {
      applyOperator();
    }
    operators.push(token.value);
  }
        }
    }

    while (operators.length > 0) {
        applyOperator();
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
        console.error('Error:', error.message);
    }
}
