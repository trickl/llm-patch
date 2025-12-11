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

    if (/[-+*/()]/.test(input[i])) {
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
};

const precedence = (operator: string): number => {
  if (operator === '+' || operator === '-') return 1;
  if (operator === '*' || operator === '/') return 2;
  return 0;
};

const applyOperation = (a: number, b: number, operator: string): number => {
  switch (operator) {
    case '+': return a + b;
    case '-': return a - b;
    case '*': return a * b;
    case '/': return Math.floor(a / b);
    default: throw new Error(`Unknown operator ${operator}`);
  }
};

const evaluate = (tokens: Token[]): number => {
  const values: number[] = [];
  const operators: string[] = [];

  for (const token of tokens) {
    if (token.type === 'number') {
      values.push(parseInt(token.value, 10));
    } else if (token.type === 'operator') {
      while (
        operators.length > 0 &&
        precedence(operators[operators.length - 1]) >= precedence(token.value)
      ) {
        const operator = operators.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOperation(a, b, operator));
      }
      operators.push(token.value);
    } else if (token.type === 'parenthesis' && token.value === '(') {
      operators.push(token.value);
    } else if (token.type === 'parenthesis' && token.value === ')') {
      while (operators.length > 0 && operators[operators.length - 1] !== '(') {
        const operator = operators.pop()!;
        const b = values.pop()!;
        const a = values.pop()!;
        values.push(applyOperation(a, b, operator));
      }
      if (operators.length === 0 || operators.pop() !== '(') {
        throw new Error('Mismatched parentheses');
      }
    }
  }

  while (operators.length > 0) {
    const operator = operators.pop()!;
    const b = values.pop()!;
    const a = values.pop()!;
    values.push(applyOperation(a, b, operator));
  }

  return values[0];
};

export const evaluateExpression = (input: string): number => {
  const tokens = tokenize(input);
  return evaluate(tokens);
};

// Example CLI usage
if (require.main === module) {
  const input = process.argv.slice(2).join(' ');
  try {
    console.log(evaluateExpression(input));
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}