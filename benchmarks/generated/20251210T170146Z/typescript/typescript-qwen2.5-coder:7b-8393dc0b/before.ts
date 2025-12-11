// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'parenthesis'; value: string };

const precedence: { [key: string]: number } = {
  '+': 1,
  '-': 1,
  '*': 2,
  '/': 2,
};

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
      const match = input.slice(i).match(/^\d+/);
      if (match) {
        tokens.push({ type: 'number', value: match[0] });
        i += match[0].length;
      }
      continue;
    }

    throw new Error(`Unexpected character at position ${i}`);
  }

  return tokens;
}

function parse(tokens: Token[]): number[] {
  const outputQueue: string[] = [];
  const operatorStack: string[] = [];

  for (const token of tokens) {
    if (token.type === 'number') {
      outputQueue.push(token.value);
    } else if (token.type === 'operator') {
      while (
        operatorStack.length > 0 &&
        precedence[operatorStack[operatorStack.length - 1]] >= precedence[token.value]
      ) {
        outputQueue.push(operatorStack.pop()!);
      }
      operatorStack.push(token.value);
    } else if (token.value === '(') {
      operatorStack.push(token.value);
    } else if (token.value === ')') {
      while (operatorStack.length > 0 && operatorStack[operatorStack.length - 1] !== '(') {
        outputQueue.push(operatorStack.pop()!);
      }
      if (operatorStack.length === 0 || operatorStack.pop() !== '(') {
        throw new Error('Mismatched parentheses');
      }
    }
  }

  while (operatorStack.length > 0) {
    outputQueue.push(operatorStack.pop()!);
  }

  return outputQueue;
}

function evaluate(outputQueue: string[]): number {
  const stack: number[] = [];

  for (const token of outputQueue) {
    if (/^\d+$/.test(token)) {
      stack.push(parseInt(token, 10));
    } else {
      const b = stack.pop()!;
      const a = stack.pop()!;
      switch (token) {
        case '+':
          stack.push(a + b);
          break;
        case '-':
          stack.push(a - b);
          break;
        case '*':
          stack.push(a * b);
          break;
        case '/':
          stack.push(Math.floor(a / b));
          break;
        default:
          throw new Error(`Unknown operator: ${token}`);
      }
    }
  }

  return stack[0];
}

export function evaluateExpression(input: string): number {
  const tokens = tokenize(input);
  const outputQueue = parse(tokens);
  return evaluate(outputQueue);
}

// CLI example
if (require.main === module) {
  const input = process.argv[2] || '3 + 4 * (2 - 1)';
  try {
    console.log(`Result of '${input}': ${evaluateExpression(input)}`);
  } catch (error) {
    console.error(`Error evaluating expression: ${error.message}`);
  }
}