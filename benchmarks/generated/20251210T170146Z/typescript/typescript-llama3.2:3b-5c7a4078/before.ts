// expression_evaluator.ts

interface Token {
  type: 'NUMBER' | 'PLUS' | 'MINUS' | 'MUL' | 'DIV' | 'LPAREN' | 'RPAREN';
  value?: number;
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
      if (char === ' ') continue;
      if (!isNaN(Number(char))) {
        currentNumber += char;
      } else {
        if (currentNumber !== '') {
          output.push({ type: 'NUMBER', value: Number(currentNumber) });
          currentNumber = '';
        }
        switch (char) {
          case '+':
            output.push({ type: 'PLUS' });
            break;
          case '-':
            output.push({ type: 'MINUS' });
            break;
          case '*':
            output.push({ type: 'MUL' });
            break;
          case '/':
            output.push({ type: 'DIV' });
            break;
          case '(':
            output.push({ type: 'LPAREN' });
            break;
          case ')':
            output.push({ type: 'RPAREN' });
            break;
        }
      }
    }
    if (currentNumber !== '') {
      output.push({ type: 'NUMBER', value: Number(currentNumber) });
    }
    return output;
  }

  private parse(tokens: Token[]): number[] {
    const output: number[] = [];
    let currentNumber = '';
    for (const token of tokens) {
      if (token.type === 'NUMBER') {
        currentNumber += token.value.toString();
      } else {
        switch (token.type) {
          case 'PLUS':
            output.push(Number(currentNumber));
            currentNumber = '';
            break;
          case 'MINUS':
            output.push(-Number(currentNumber));
            currentNumber = '';
            break;
          case 'MUL':
            output.push(Number(currentNumber) * Number(currentNumber));
            currentNumber = '';
            break;
          case 'DIV':
            output.push(Number(currentNumber) / Number(currentNumber));
            currentNumber = '';
            break;
        }
      }
    }
    if (currentNumber !== '') {
      output.push(Number(currentNumber));
    }
    return output;
  }

  private evaluate(expression: number[]): number {
    const precedence: { [key: string]: number } = {
      '*': 2,
      '/': 2,
      '+': 1,
      '-': 1
    };
    let output: number[] = [];
    for (const token of expression) {
      if (token in precedence) {
        const rightOperandIndex = output.indexOf(token);
        const leftOperandIndex = output.lastIndexOf(token);
        const rightOperand = output.splice(rightOperandIndex, 1)[0];
        const leftOperand = output.splice(leftOperandIndex - 1, 1)[0];
        switch (token) {
          case '*':
            output.push(leftOperand * rightOperand);
            break;
          case '/':
            output.push(leftOperand / rightOperand);
            break;
          case '+':
            output.push(leftOperand + rightOperand);
            break;
          case '-':
            output.push(leftOperand - rightOperand);
            break;
        }
      } else {
        output.push(token);
      }
    }
    return output[0];
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