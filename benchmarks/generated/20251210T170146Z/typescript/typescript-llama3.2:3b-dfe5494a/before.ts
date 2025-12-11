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

  evaluateExpression(input: string): number {
    const tokens = this.tokenize(input);
    return this.parse(tokens);
  }

  private tokenize(input: string): string[] {
    const output = [];
    let currentToken = '';

    for (const char of input) {
      if (char.match(/[0-9+*/()-]/)) {
        currentToken += char;
      } else if (currentToken !== '') {
        output.push(currentToken);
        currentToken = '';
      }

      if (char === '(' || char === ')') {
        output.push(char);
      }
    }

    if (currentToken !== '') {
      output.push(currentToken);
    }

    return output;
  }

  private parse(tokens: string[]): number {
    const operatorStack: string[] = [];
    let outputQueue: number[] = [];

    for (const token of tokens) {
      if (token === '(') {
        operatorStack.push(token);
      } else if (token === ')') {
        while (operatorStack[operatorStack.length - 1] !== '(') {
          const op = operatorStack.pop() as string;
          outputQueue.push({ type: 'number', value: this.parseNumber(op) });
          outputQueue.push({ type: 'operator', value: op });
        }

        operatorStack.pop();
      } else if (this.isOperator(token)) {
        while (
          operatorStack.length > 0 &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence[token]
        ) {
          const op = operatorStack.pop() as string;
          outputQueue.push({ type: 'number', value: this.parseNumber(op) });
          outputQueue.push({ type: 'operator', value: op });
        }

        operatorStack.push(token);
      } else if (this.isUnaryMinus(token)) {
        operatorStack.push(token);
      } else {
        outputQueue.push({ type: 'number', value: this.parseNumber(token) });
      }
    }

    while (operatorStack.length > 0) {
      const op = operatorStack.pop() as string;
      outputQueue.push({ type: 'number', value: this.parseNumber(op) });
      outputQueue.push({ type: 'operator', value: op });
    }

    return this.evaluate(outputQueue);
  }

  private isOperator(token: string): boolean {
    return token in this.precedence;
  }

  private isUnaryMinus(token: string): boolean {
    return token === '-' && (token.length === 1 || !this.isOperator(token.slice(1)));
  }

  private parseNumber(token: string): number {
    if (!isNaN(Number(token))) {
      return Number(token);
    } else {
      throw new Error(`Invalid input: ${token}`);
    }
  }

  private evaluate(queue: { type: 'number' | 'operator' }[]): number {
    while (queue.length > 0) {
      const item = queue.shift() as { type: 'number' | 'operator' };

      if (item.type === 'number') {
        continue;
      }

      const rightOperand = queue.pop() as { type: 'number' };
      const leftOperand = queue.pop() as { type: 'number' };

      switch (item.value) {
        case '+':
          return leftOperand + rightOperand;
        case '-':
          return leftOperand - rightOperand;
        case '*':
          return leftOperand * rightOperand;
        case '/':
          return Math.floor(leftOperand / rightOperand);
        default:
          throw new Error(`Invalid operator: ${item.value}`);
      }
    }

    throw new Error('Invalid expression');
  }
}

export function evaluateExpression(input: string): number {
  const evaluator = new ExpressionEvaluator();
  return evaluator.evaluateExpression(input);
}

// example.js

const express = require('./expression_evaluator');

console.log(express.evaluateExpression("1 + 2")); // Output: 3
console.log(express.evaluateExpression("2 * 3 + 4")); // Output: 10
console.log(express.evaluateExpression("2 * (3 + 4)")); // Output: 14
console.log(express.evaluateExpression("8 / 2 * (2 + 2)")); // Output: 16