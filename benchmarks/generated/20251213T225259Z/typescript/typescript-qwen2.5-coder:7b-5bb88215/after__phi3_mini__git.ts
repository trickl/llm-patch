// expression_evaluator.ts

type Token = { type: 'number' | 'operator' | 'lparen' | 'rparen'; value: string };

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
    if (input[i] === ' ') {
      i++;
      continue;
    }

    if (!isNaN(Number(input[i])) || input[i] === '-') {
      let numStr = input[i];
      while (i + 1 < input.length && !isNaN(Number(input[i + 1])) || input[i + 1] === '.') {
        numStr += input[++i];
      }
      tokens.push({ type: 'number', value: numStr });
    } else if ('+-*/()'.includes(input[i])) {
      tokens.push({ type: 'operator', value: input[i++] });
    } else {
      throw new Error(`Unexpected character: ${input[i]}`);
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
    } else if (token.value === '(') {
      operatorStack.push(token.value);
    } else if (token.value === ')') {
      while (operatorStack.length > 0 && operatorStack[operatorStack.length - 1] !== '(') {
        outputQueue.push(operatorStack.pop()!);
      }
      operatorStack.pop(); // Remove the '('
    } else {
      while (
        operatorStack.length > 0 &&
        precedence[token.value] <= precedence[operatorStack[operatorStack.length - 1]]
      ) {
        outputQueue.push(operatorStack.pop()!);
      }
      operatorStack.push(token.value);
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
if (require.main === module) {
  console.log(evaluateExpression('1 + 2')); // Output: 3
  console.log(evaluateExpression('2 * 3 + 4')); // Output: 10
  console.log(evaluateExpression('2 * (3 + 4)')); // Output: 14
  console.log(evaluateExpression('8 / 2 * (2 + 2)')); // Output: 16
}