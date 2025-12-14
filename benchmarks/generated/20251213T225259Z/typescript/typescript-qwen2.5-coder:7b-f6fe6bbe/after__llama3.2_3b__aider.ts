// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis', value: string };

const isNumber = (char: string): boolean => !isNaN(Number(char));
const isOperator = (char: string): boolean => '+-*/'.includes(char);
const isParenthesis = (char: string): boolean => char === '(' || char === ')';

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let currentToken = '';

    for (let i = 0; i < input.length; i++) {
        const char = input[i];

        if (isNumber(char)) {
            currentToken += char;
        } else if (isOperator(char) || isParenthesis(char)) {
            if (currentToken !== '') {
                tokens.push({ type: 'number', value: currentToken });
                currentToken = '';
            }
            tokens.push({ type: 'operator' | 'parenthesis', value: char });
        } else if (char === ' ') {
            continue;
        } else {
            throw new Error(`Unexpected character: ${char}`);
        }
    }

    if (currentToken !== '') {
        tokens.push({ type: 'number', value: currentToken });
    }

    return tokens;
}

function parse(tokens: Token[]): number[] {
    const values: number[] = [];
    const operators: string[] = [];
    for (const token of tokens as { type: 'number' | 'operator' | 'parenthesis', value: string }[]) {
      if (token.type === 'number') {
        values.push(Number(token.value));
      } else if (token.type === 'operator' || token.type === 'parenthesis') {
        while (
          operators.length > 0 &&
          precedence(operators[operators.length - 1]) >= precedence(token.value)
        ) {
          const operator = operators.pop()!;
          const b = values.pop()!;
          const a = values.pop()!;
          values.push(applyOperator(a, b, operator));
        }
        operators.push(token.type === 'operator' ? token.value : '(');
      }
    }
    while (operators.length > 0 && operators[operators.length - 1] !== ')') {
      const operator = operators.pop()!;
      const b = values.pop()!;
      const a = values.pop()!;
      values.push(applyOperator(a, b, operator));
    }
    return values;

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

function applyOperator(a: number, b: number, operator: string): number {
    switch (operator) {
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
            throw new Error(`Unknown operator: ${operator}`);
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
            console.log(`Result: ${result}`);
        } catch (error) {
            console.error(`Error: ${error.message}`);
        }
    }
}

node expression_evaluator.ts "3 + 4 * (2 - 1)"
