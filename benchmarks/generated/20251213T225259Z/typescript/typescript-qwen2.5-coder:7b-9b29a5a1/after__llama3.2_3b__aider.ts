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
            throw new Error(`Invalid character: ${char}`);
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

    for (const token of tokens) {
  if (token.type === 'number') {
    values.push(Number(token.value));
  } else if (token.value === '(') {
    operators.push('"parenthesis"');
  } else if (token.value === ')') {
    while (operators.length > 0 && operators[operators.length - 1] !== '(') {
      applyOperator(values, operators);
    }
    operators.pop(); // Remove the '('
        } else {
            while (
                operators.length > 0 &&
                precedence(operators[operators.length - 1]) >= precedence(token.value)
            ) {
                applyOperator(values, operators);
            }
            operators.push(token.value);
        }
    }

    while (operators.length > 0) {
        applyOperator(values, operators);
    }

    return values;
}

function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    const result = parse(tokens);
    if (result.length !== 1) {
        throw new Error('Malformed expression');
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

function applyOperator(values: number[], operators: string[]): void {
    const operator = operators.pop();
    const b = values.pop()!;
    const a = values.pop()!;

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
            values.push(Math.trunc(a / b));
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
            console.error(`Error: ${error.message}`);
        }
    }
}
