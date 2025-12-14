import { strict as assert } from 'assert';
import * as process from 'process';
enum TokenType {
  NUMBER,
  PLUS,
  MINUS,
  MUL,
  DIV,
  LPAREN,
  RPAREN,
  EOF,
}

interface Token {
  type: TokenType;
  value?: number;
}

class Lexer {
  private input: string;
  private pos: number = 0;
  private currentChar: string | null = this.input[this.pos];

  constructor(input: string) {
    this.input = input;
  }

  private advance(): void {
    this.pos++;
    if (this.pos < this.input.length) {
      this.currentChar = this.input[this.pos];
    } else {
      this.currentChar = null;
    }
  }

  private skipWhitespace(): void {
    while (this.currentChar !== null && /\s/.test(this.currentChar)) {
      this.advance();
    }
  }

  private number(): number {
    let result = '';
    while (this.currentChar !== null && /\d/.test(this.currentChar)) {
      result += this.currentChar;
      this.advance();
    }
    return parseInt(result, 10);
  }

  public getNextToken(): Token {
    while (this.currentChar !== null) {
      if (/\s/.test(this.currentChar)) {
        this.skipWhitespace();
        continue;
      }

      if (/\d/.test(this.currentChar)) {
        return { type: TokenType.NUMBER, value: this.number() };
      }

      if (this.currentChar === '+') {
        this.advance();
        return { type: TokenType.PLUS };
      }

      if (this.currentChar === '-') {
        this.advance();
        return { type: TokenType.MINUS };
      }

      if (this.currentChar === '*') {
        this.advance();
        return { type: TokenType.MUL };
      }

      if (this.currentChar === '/') {
        this.advance();
        return { type: TokenType.DIV };
      }

      if (this.currentChar === '(') {
        this.advance();
        return { type: TokenType.LPAREN };
      }

      if (this.currentChar === ')') {
        this.advance();
        return { type: TokenType.RPAREN };
      }

      throw new Error(`Invalid character: ${this.currentChar}`);
    }

    return { type: TokenType.EOF };
  }
}

class Parser {
  private lexer: Lexer;
  private currentToken: Token;

  constructor(lexer: Lexer) {
    this.lexer = lexer;
    this.currentToken = this.lexer.getNextToken();
  }

  private eat(tokenType: TokenType): void {
    if (this.currentToken.type === tokenType) {
      this.currentToken = this.lexer.getNextToken();
    } else {
      throw new Error(`Invalid token type: ${tokenType}`);
    }
  }

  private factor(): number {
    const token = this.currentToken;
    if (token.type === TokenType.NUMBER) {
      this.eat(TokenType.NUMBER);
      return token.value!;
    } else if (token.type === TokenType.MINUS) {
      this.eat(TokenType.MINUS);
      return -this.factor();
    } else if (token.type === TokenType.LPAREN) {
      this.eat(TokenType.LPAREN);
      const result = this.expr();
      this.eat(TokenType.RPAREN);
      return result;
    }
    throw new Error(`Unexpected token: ${token.type}`);
  }

  private term(): number {
    let result = this.factor();

    while (this.currentToken.type === TokenType.MUL || this.currentToken.type === TokenType.DIV) {
      const token = this.currentToken;
      if (token.type === TokenType.MUL) {
        this.eat(TokenType.MUL);
        result *= this.factor();
      } else if (token.type === TokenType.DIV) {
        this.eat(TokenType.DIV);
        result /= this.factor();
      }
    }

    return result;
  }

  public expr(): number {
    let result = this.term();

    while (this.currentToken.type === TokenType.PLUS || this.currentToken.type === TokenType.MINUS) {
      const token = this.currentToken;
      if (token.type === TokenType.PLUS) {
        this.eat(TokenType.PLUS);
        result += this.term();
      } else if (token.type === TokenType.MINUS) {
        this.eat(TokenType.MINUS);
        result -= this.term();
      }
    }

    return result;
  }
}

export function evaluateExpression(input: string): number {
  const lexer = new Lexer(input);
  const parser = new Parser(lexer);
  return parser.expr();
}
// CLI example
if (process.mainModule === module) {
  const input = process.argv[2];
  if (!input) {
    console.log('Usage: node expression_evaluator.ts "expression"');
    process.exit(1);
  }
  try {
    const result = evaluateExpression(input);
    console.log(`Result: ${result}`);
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

// Automated tests
assert.equal(evaluateExpression('1 + 2'), 3);
assert.equal(evaluateExpression('2 * 3 + 4'), 10);
assert.equal(evaluateExpression('2 * (3 + 4)'), 14);
assert.equal(evaluateExpression('8 / 2 * (2 + 2)'), 16);
