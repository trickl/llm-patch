// expression_evaluator.ts

interface Token {
  type: 'NUMBER' | 'PLUS' | 'MINUS' | 'MUL' | 'DIV' | 'LPAREN' | 'RPAREN';
  value: number | string;
}

class ExpressionEvaluator {
  private tokens: Token[];

  constructor(input: string) {
    this.tokens = this.tokenize(input);
  }

  private tokenize(input: string): Token[] {
    const output: Token[] = [];
    let currentNumber = '';
    for (const char of input) {
      if (char.match(/[0-9]/)) {
        currentNumber += char;
      } else {
        if (currentNumber !== '') {
          output.push({ type: 'NUMBER', value: parseInt(currentNumber) });
          currentNumber = '';
        }
        const operator = this.getOperator(char);
        if (operator) {
          output.push({ type: operator, value: '' });
        }
      }
    }
    if (currentNumber !== '') {
      output.push({ type: 'NUMBER', value: parseInt(currentNumber) });
    }

    return output;
  }

  private getOperator(char: string): ('PLUS' | 'MINUS' | 'MUL' | 'DIV') | null {
    const precedence = { PLUS: 1, MINUS: 1, MUL: 2, DIV: 2 };
    if (char === '+' || char === '-') {
      return 'PLUS';
    } else if (char === '*' || char === '/') {
      return 'MUL';
    }
    return null;
  }

  private parse(tokens: Token[]): number[] {
    const output: number[] = [];
    let currentNumber = '';
    for (const token of tokens) {
      if (token.type === 'NUMBER') {
        currentNumber += token.value.toString();
      } else {
        if (currentNumber !== '') {
          output.push(parseInt(currentNumber));
          currentNumber = '';
        }
        switch (token.type) {
          case 'PLUS':
            output.push(1);
            break;
          case 'MINUS':
            output.push(-1);
            break;
          case 'MUL':
            output.push(2);
            break;
          case 'DIV':
            output.push(3);
            break;
        }
      }
    }
    if (currentNumber !== '') {
      output.push(parseInt(currentNumber));
    }

    return output;
  }

  private evaluate(expression: number[]): number {
    const stack: number[] = [];
    for (const token of expression) {
      switch (token) {
        case 1:
          // +
          break;
        case -1:
          // -
          break;
        case 2:
          // *
          break;
        case 3:
          // /
          break;
        default:
          stack.push(token);
      }
    }

    let result = stack.pop() as number;
    while (stack.length > 0) {
      const operator = stack.pop() as number;
      switch (operator) {
        case 1: // +
          result += stack.pop() as number;
          break;
        case -1: // -
          result -= stack.pop() as number;
          break;
        case 2: // *
          result *= stack.pop() as number;
          break;
        case 3: // /
          result /= stack.pop() as number;
          break;
      }
    }

    return result;
  }

  public evaluateExpression(input: string): number {
    const tokens = this.tokenize(input);
    const parsedTokens = this.parse(tokens);
    return this.evaluate(parsedTokens);
  }
}

// CLI example
const evaluator = new ExpressionEvaluator('1 + 2');
console.log(evaluator.evaluateExpression()); // Output: 3

const evaluator2 = new ExpressionEvaluator('2 * 3 + 4');
console.log(evaluator2.evaluateExpression()); // Output: 10

const evaluator3 = new ExpressionEvaluator('2 * (3 + 4)');
console.log(evaluator3.evaluateExpression()); // Output: 14

const evaluator4 = new ExpressionEvaluator('8 / 2 * (2 + 2)');
console.log(evaluator4.evaluateExpression()); // Output: 16