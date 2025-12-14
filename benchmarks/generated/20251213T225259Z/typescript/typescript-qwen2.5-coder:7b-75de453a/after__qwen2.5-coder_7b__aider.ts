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

    if (/[-+]?\d+(\.\d+)?/.test(input.slice(i))) {
      const match = input.slice(i).match(/[-+]?\d+(\.\d+)?/);
      tokens.push({ type: 'number', value: match![0] });
      i += match![0].length;
    } else if (/\(|\)/.test(input[i])) {
      tokens.push({ type: 'parenthesis', value: input[i] });
      i++;
    } else if (/[\+\-\*\/]/.test(input[i])) {
      tokens.push({ type: 'operator', value: input[i] });
      i++;
    } else {
      throw new Error(`Unexpected character at position ${i}`);
    }
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

function evaluateRPN(tokens: string[]): number {
  const stack: number[] = [];

  for (const token of tokens) {
    if (!isNaN(Number(token))) {
      stack.push(Number(token));
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
          stack.push(Math.trunc(a / b));
          break;
      }
    }
  }

  return stack.pop()!;
}

export function evaluateExpression(input: string): number {
  const tokens = tokenize(input);
  const rpn = parse(tokens);
  return evaluateRPN(rpn);
}
// CLI example
if (typeof require !== 'undefined' && require.main === module) {
  const input = process.argv[2];
  if (!input) {
    console.log('Usage: node expression_evaluator.ts "expression"');
  } else {
    try {
      const result = evaluateExpression(input);
      console.log(result);
    } catch (error) {
      console.error(`Error evaluating expression: ${error.message}`);
    }
  }
}
