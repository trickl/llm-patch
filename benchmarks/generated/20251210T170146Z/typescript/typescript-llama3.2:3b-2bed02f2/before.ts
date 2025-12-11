// Token types
enum TokenType {
  NUMBER,
  PLUS,
  MINUS,
  MUL,
  DIV,
  LPAREN,
  RPAREN,
}

// Token class
class Token {
  type: TokenType;
  value: string | number;

  constructor(type: TokenType, value: string | number) {
    this.type = type;
    this.value = value;
  }
}

// Lexer class
class Lexer {
  private input: string;
  private pos: number;
  private tokens: Token[] = [];

  constructor(input: string) {
    this.input = input;
    this.pos = 0;
  }

  public next(): Token | null {
    if (this.pos >= this.input.length) return null;

    let match: RegExpExecArray | null;
    while ((match = /\d+|\+|-|\*|\/|\(|\)/.exec(this.input.slice(this.pos)))) !== null) {
      const tokenValue = match[0];
      switch (tokenValue) {
        case '+':
        case '-':
          this.tokens.push(new Token(TokenType.PLUS, tokenValue));
          break;
        case '*':
        case '/':
          this.tokens.push(new Token(TokenType.MUL, tokenValue));
          break;
        default:
          if (!isNaN(Number(tokenValue))) {
            this.tokens.push(new Token(TokenType.NUMBER, Number(tokenValue)));
          } else {
            this.tokens.push(new Token(TokenType.LPAREN, tokenValue));
          }
      }
      this.pos += match[0].length;
    }

    return null;
  }
}

// Parser class
class Parser {
  private tokens: Token[];
  private pos: number;

  constructor(tokens: Token[]) {
    this.tokens = tokens;
    this.pos = 0;
  }

  public parse(): [number, number] | null {
    if (this.pos >= this.tokens.length) return null;

    const leftOperand = this.parseExpression();
    if (leftOperand === null) return null;

    while (true) {
      const token = this.tokens[this.pos];
      switch (token.type) {
        case TokenType.PLUS:
          this.pos++;
          const rightOperand = this.parseExpression();
          if (rightOperand === null) return null;
          break;
        default:
          return [leftOperand, rightOperand];
      }
    }
  }

  private parseExpression(): number | null {
    let result: number | null = null;

    while (true) {
      const token = this.tokens[this.pos];
      switch (token.type) {
        case TokenType.NUMBER:
          if (result === null) result = token.value;
          else return result + token.value;
          break;
        case TokenType.MINUS:
          this.pos++;
          result = -result;
          break;
        default:
          return result;
      }
    }
  }
}

// Evaluator class
class Evaluator {
  private pos: number;

  constructor(tokens: Token[]) {
    this.pos = 0;
  }

  public evaluate(): number | null {
    if (this.pos >= tokens.length) return null;

    const leftOperand = this.parseExpression();
    if (leftOperand === null) return null;

    while (true) {
      const token = tokens[this.pos];
      switch (token.type) {
        case TokenType.PLUS:
          this.pos++;
          const rightOperand = this.parseExpression();
          if (rightOperand === null) return null;
          break;
        default:
          return leftOperand + rightOperand;
      }
    }
  }

  private parseExpression(): number | null {
    let result: number | null = null;

    while (true) {
      const token = tokens[this.pos];
      switch (token.type) {
        case TokenType.NUMBER:
          if (result === null) result = token.value;
          else return result + token.value;
          break;
        case TokenType.MINUS:
          this.pos++;
          result = -result;
          break;
        default:
          return result;
      }
    }
  }
}

// Expression Evaluator
function evaluateExpression(input: string): number {
  const tokens = new Lexer(input).tokens;
  const parser = new Parser(tokens);
  const evaluator = new Evaluator(tokens);

  const result = parser.parse();
  if (result === null) return null;

  return evaluator.evaluate();
}

export default evaluateExpression;