// expression_evaluator.ts

type Token = {
  type: 'number' | 'operator' | 'parenthesis';
  value: string;
};

const isNumber = (char: string): boolean => !isNaN(Number(char));
const isOperator = (char: string): boolean => '+-*/'.includes(char);
const isParenthesis = (char: string): boolean => char === '(' || char === ')';

function tokenize(input: string): Token[] {
  const tokens: Token[] = [];
  let current = '';

  for (let i = 0; i < input.length; i++) {
    const char = input[i];

    if (isNumber(char)) {
      current += char;
      continue;
    }

    if (current) {
      tokens.push({ type: 'number', value: current });
      current = '';
    }

    if (isOperator(char)) {
      tokens.push({ type: 'operator', value: char });
    } else if (isParenthesis(char)) {
      tokens.push({ type: 'parenthesis', value: char });
    }
  }

  if (current) {
    tokens.push({ type: 'number', value: current });
  }

  return tokens;
}

function parse(tokens: Token[]): number[] {
  const values: number[] = [];
  const operators: string[] = [];

  for (const token of tokens) {
    if (token.type === 'number') {
      values.push(Number(token.value));
    } else if (token.type === 'operator') {
      while (
        operators.length > 0 &&
        precedence(operators[operators.length - 1]) >= precedence(token.value)
      ) {
        const operator = operators.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOperator(a, b, operator));
      }
      operators.push(token.value);
    } else if (token.type === 'parenthesis' && token.value === '(') {
      operators.push(token.value);
    } else if (token.type === 'parenthesis' && token.value === ')') {
      while (operators.length > 0 && operators[operators.length - 1] !== '(') {
        const operator = operators.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOperator(a, b, operator));
      }
      operators.pop(); // Remove the '('
    }
  }

  while (operators.length > 0) {
    const operator = operators.pop()!;
    const b = values.pop()!;
    const a = values.pop()!;
    values.push(applyOperator(a, b, operator));
  }

  return values;
}

function precedence(operator: string): number {
  if (operator === '+' || operator === '-') return 1;
  if (operator === '*' || operator === '/') return 2;
  return 0;
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
      return Math.floor(a / b);
    default:
      throw new Error(`Unknown operator: ${operator}`);
  }
}
export function evaluateExpression(input: string): number {
  const tokens = tokenize(input);
  const result = parse(tokens);
  if (result.length !== 1) {
    throw new Error('Invalid expression');
  }
  return result[0];
}

// Example CLI usage
if (require.main === module) {
  const input = process.argv.slice(2).join(' ');
  try {
    const result = evaluateExpression(input);
    console.log(`Result: ${result}`);
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

node expression_evaluator.js "3 + 4 * (2 - 1)"

Result: 9
