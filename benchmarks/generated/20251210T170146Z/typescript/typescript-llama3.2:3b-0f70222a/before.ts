// expression_evaluator.ts

class ExpressionEvaluator {
  private precedence: { [operator: string]: number };

  constructor() {
    this.precedence = {
      '+': 1,
      '-': 1,
      '*': 2,
      '/': 2,
    };
  }

  public evaluateExpression(input: string): number {
    const tokens = this.tokenize(input);
    return this.parse(tokens);
  }

  private tokenize(input: string): string[] {
    const output = [];
    let currentToken = '';

    for (const char of input) {
      if (char.match(/^[0-9+*/()-]/)) {
        currentToken += char;
      } else if (currentToken && !this.isOperator(char)) {
        output.push(currentToken);
        currentToken = '';
      }

      if (!char.match(/^[0-9+*/()-]$/)) {
        continue;
      }
    }

    if (currentToken) {
      output.push(currentToken);
    }

    return output;
  }

  private isOperator(char: string): boolean {
    return char in this.precedence;
  }

  private parse(tokens: string[]): number {
    const operatorStack = [];
    let outputQueue: string[] = [];

    for (const token of tokens) {
      if (!this.isOperator(token)) {
        outputQueue.push(Number(token));
      } else if (token === '(') {
        operatorStack.push(token);
      } else if (token === ')') {
        while (operatorStack[operatorStack.length - 1] !== '(') {
          const op = outputQueue.pop() as string;
          this.applyOperator(op, operatorStack);
        }
        operatorStack.pop();
      } else {
        while (
          operatorStack.length &&
          this.precedence[token] <= this.precedence[operatorStack[operatorStack.length - 1]]
        ) {
          const op = outputQueue.pop() as string;
          this.applyOperator(op, operatorStack);
        }
        operatorStack.push(token);
      }
    }

    while (operatorStack.length) {
      const op = outputQueue.pop() as string;
      this.applyOperator(op, operatorStack);
    }

    return outputQueue[0] as number;
  }

  private applyOperator(op: string, stack: string[]): void {
    if (op === '+') {
      outputQueue.push(stack.pop() as number + Number(outputQueue[outputQueue.length - 1]));
    } else if (op === '-') {
      const num = Number(outputQueue.pop() as string);
      outputQueue.push(num - Number(stack.pop() as string));
    } else if (op === '*') {
      outputQueue.push(Number(outputQueue.pop() as string) * Number(stack.pop() as string));
    } else if (op === '/') {
      const num = Number(outputQueue.pop() as string);
      outputQueue.push(Math.floor(num / Number(stack.pop() as string)));
    }
  }
}

export function evaluateExpression(input: string): number {
  return new ExpressionEvaluator().evaluateExpression(input);
}

// CLI example
const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

rl.question('Enter an expression: ', (input) => {
  const result = evaluateExpression(input);
  console.log(`Result: ${result}`);
  rl.close();
});