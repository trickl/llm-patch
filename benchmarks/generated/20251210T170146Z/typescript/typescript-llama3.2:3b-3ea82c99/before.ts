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
      if (char.match(/^[0-9]+$/)) {
        currentNumber += char;
      } else {
        if (currentNumber !== '') {
          output.push({ type: 'NUMBER', value: parseInt(currentNumber, 10) });
          currentNumber = '';
        }
        const tokenValue = this.getOperatorValue(char);
        output.push({ type: char, value: tokenValue });
      }
    }
    if (currentNumber !== '') {
      output.push({ type: 'NUMBER', value: parseInt(currentNumber, 10) });
    }

    return output;
  }

  private getOperatorValue(operator: string): number {
    switch (operator) {
      case '+':
        return 1;
      case '-':
        return -1;
      case '*':
        return 2;
      case '/':
        return 3;
      default:
        throw new Error(`Unsupported operator: ${operator}`);
    }
  }

  private parse(tokens: Token[]): number[] {
    const output: number[] = [];
    let currentNumber = '';
    for (const token of tokens) {
      if (token.type === 'NUMBER') {
        currentNumber += token.value.toString();
      } else {
        if (currentNumber !== '') {
          output.push(parseInt(currentNumber, 10));
          currentNumber = '';
        }

        const precedence = this.getPrecedence(token.type);
        let left: number[] | null = null;
        let right: number[] | null = null;

        switch (token.type) {
          case 'LPAREN':
            if (output.length > 0 && output[output.length - 1] !== '(') {
              throw new Error('Malformed expression');
            }
            left = this.parse(output);
            break;
          case 'RPAREN':
            if (!left || output[output.length - 1] !== ')') {
              throw new Error('Malformed expression');
            }
            right = this.parse(output.slice(0, output.length - 1));
            break;
          default:
            if (right) {
              throw new Error('Malformed expression');
            }

            const operatorIndex = output.indexOf(token);
            left = this.parse(output.slice(0, operatorIndex));
            right = this.parse(output.slice(operatorIndex + 1));
        }

        output.push(left!.reduce((a, b) => a * b, 1));
      }
    }

    if (currentNumber !== '') {
      output.push(parseInt(currentNumber, 10));
    }

    return output;
  }

  private getPrecedence(operator: string): number {
    switch (operator) {
      case '*':
      case '/':
        return 2;
      case '+':
      case '-':
        return 1;
      default:
        throw new Error(`Unsupported operator: ${operator}`);
    }
  }

  public evaluateExpression(): number {
    const parsed = this.parse(this.tokens);
    if (parsed.length !== 1) {
      throw new Error('Malformed expression');
    }
    return parsed[0];
  }
}

export function evaluateExpression(input: string): number {
  const evaluator = new ExpressionEvaluator(input);
  try {
    return evaluator.evaluateExpression();
  } catch (error) {
    console.error(error.message);
    return NaN;
  }
}