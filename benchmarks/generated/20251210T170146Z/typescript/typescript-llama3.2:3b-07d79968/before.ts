// tokenizer.ts
interface Token {
  type: 'NUMBER' | 'PLUS' | 'MINUS' | 'MUL' | 'DIV' | 'LPAREN' | 'RPAREN';
  value?: number;
}

function tokenize(expression: string): Token[] {
  const tokens: Token[] = [];
  let currentToken: Token | null = null;

  for (let i = 0; i < expression.length; i++) {
    const char = expression[i];

    if (char === ' ') continue;

    if (!currentToken) {
      currentToken = { type: 'NUMBER', value: parseInt(char, 10) };
      tokens.push(currentToken);
    } else if (isOperator(char)) {
      if (currentToken.type !== 'NUMBER') {
        throw new Error('Invalid expression');
      }
      const tokenValue = currentToken.value as number;
      currentToken = { type, value: tokenValue };
      tokens.push(currentToken);
    }

    if (char === '(') {
      currentToken = { type: 'LPAREN' };
      tokens.push(currentToken);
    } else if (char === ')') {
      if (!currentToken || currentToken.type !== 'LPAREN') {
        throw new Error('Invalid expression');
      }
      currentToken = null;
    }

    if (isOperator(char) && char !== '(' && char !== ')') {
      if (currentToken && currentToken.type !== 'NUMBER') {
        throw new Error('Invalid expression');
      }
      const tokenValue = parseInt(char, 10);
      currentToken = { type: 'MUL', value: tokenValue };
      tokens.push(currentToken);
    }
  }

  return tokens;
}

function isOperator(char: string): char is 'PLUS' | 'MINUS' | 'MUL' | 'DIV' {
  return ['+', '-', '*', '/'].includes(char);
}

// parser.ts
interface ParseResult {
  value: number;
  error?: Error;
}

function parse(tokens: Token[]): ParseResult {
  const operatorPrecedence: { [key: string]: number } = {
    '+': 1,
    '-': 1,
    '*': 2,
    '/': 2,
  };

  function applyOperator(operator: string, left: number, right: number): number {
    switch (operator) {
      case '+':
        return left + right;
      case '-':
        return left - right;
      case '*':
        return left * right;
      case '/':
        if (right === 0) throw new Error('Division by zero');
        return Math.floor(left / right);
      default:
        throw new Error(`Unknown operator: ${operator}`);
    }
  }

  function applyUnaryMinus(value: number): number {
    return -value;
  }

  const outputQueue: number[] = [];
  const operatorStack: string[] = [];

  for (const token of tokens) {
    if (token.type === 'NUMBER') {
      outputQueue.push(token.value as number);
    } else if (token.type === 'LPAREN') {
      operatorStack.push(token.type);
    } else if (token.type === 'RPAREN') {
      while (operatorStack[operatorStack.length - 1] !== 'LPAREN') {
        const rightOperand = outputQueue.pop() as number;
        const leftOperand = outputQueue.pop() as number;
        const operator = operatorStack.pop() as string;

        if (!leftOperand || !rightOperand) throw new Error('Invalid expression');

        const result = applyOperator(operator, leftOperand, rightOperand);
        outputQueue.push(result);
      }
      operatorStack.pop(); // Remove LPAREN
    } else if (token.type === 'PLUS' || token.type === 'MINUS') {
      while (
        operatorStack.length > 0 &&
        getPrecedence(operatorStack[operatorStack.length - 1]) >=
          getPrecedence(token.type)
      ) {
        const rightOperand = outputQueue.pop() as number;
        const leftOperand = outputQueue.pop() as number;
        const operator = operatorStack.pop() as string;

        if (!leftOperand || !rightOperand) throw new Error('Invalid expression');

        const result = applyOperator(operator, leftOperand, rightOperand);
        outputQueue.push(result);
      }
      operatorStack.push(token.type);
    } else if (token.type === 'MUL' || token.type === 'DIV') {
      while (
        operatorStack.length > 0 &&
        getPrecedence(operatorStack[operatorStack.length - 1]) >=
          getPrecedence(token.type)
      ) {
        const rightOperand = outputQueue.pop() as number;
        const leftOperand = outputQueue.pop() as number;
        const operator = operatorStack.pop() as string;

        if (!leftOperand || !rightOperand) throw new Error('Invalid expression');

        const result = applyOperator(operator, leftOperand, rightOperand);
        outputQueue.push(result);
      }
      operatorStack.push(token.type);
    } else {
      throw new Error(`Unknown token: ${token}`);
    }
  }

  while (operatorStack.length > 0) {
    const rightOperand = outputQueue.pop() as number;
    const leftOperand = outputQueue.pop() as number;
    const operator = operatorStack.pop() as string;

    if (!leftOperand || !rightOperand) throw new Error('Invalid expression');

    const result = applyOperator(operator, leftOperand, rightOperand);
    outputQueue.push(result);
  }

  return { value: outputQueue[0], error: null };
}

function getPrecedence(operator: string): number {
  if (!operatorPrecedence[operator]) throw new Error(`Unknown operator: ${operator}`);
  return operatorPrecedence[operator];
}

// evaluator.ts
interface EvaluatorOptions {
  unaryMinus?: (value: number) => number;
}

function evaluateExpression(
  expression: string,
  options: EvaluatorOptions = {}
): number | null {
  const tokens = tokenize(expression);
  if (!tokens.length) return null;

  const parseResult = parse(tokens);
  if (parseResult.error) throw new Error(`Invalid expression: ${expression}`);
  const value = parseResult.value;
  const unaryMinus = options.unaryMinus || ((value) => value);

  return unaryMinus(value);
}

// usage.ts
import { evaluateExpression } from './expression_evaluator';

const expressions = [
  '1 + 2',
  '2 * 3 + 4',
  '2 * (3 + 4)',
  '8 / 2 * (2 + 2)',
];

expressions.forEach((expr) => {
  try {
    const result = evaluateExpression(expr);
    console.log(`Result for "${expr}": ${result}`);
  } catch (error) {
    console.error(error.message);
  }
});