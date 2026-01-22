export enum FormulationPartType {
    INPUT = "input",
    CONSTANT = "constant",
    BINARY_OP = "binary_op",
    NARY_OP = "nary_op",
    UNARY_OP = "unary_op",
}
export abstract class FormulationPart {
    abstract getName(): string;
    type: FormulationPartType = FormulationPartType.INPUT;
}

export class InputPart extends FormulationPart {
    getName(): string {
        return this.inputName;
    }
    constructor(public inputName: string) {
        super();
        this.type = FormulationPartType.INPUT;
    }
}
export class ConstantPart extends FormulationPart {
    getName(): string {
        return this.value.toString();
    }

    constructor(public value: number) {
        super();
        this.type = FormulationPartType.CONSTANT;
    }
}
export class BinaryOpPart extends FormulationPart {
    getName(): string {
        return `(${this.left.getName()} ${this.op} ${this.right.getName()})`;
    }
    constructor(
        public left: FormulationPart,
        public right: FormulationPart,
        public op: string
    ) {
        super();
        this.type = FormulationPartType.BINARY_OP;
    }
}
export class NaryOpPart extends FormulationPart {
    getName(): string {
        return `(${this.operands.map((o) => o.getName()).join(` ${this.op} `)})`;
    }
    constructor(public operands: FormulationPart[], public op: string) {
        super();
        this.type = FormulationPartType.NARY_OP;
    }
}
export class UnaryOpPart extends FormulationPart {
    getName(): string {
        return `${this.op}(${this.operand.getName()})`;
    }
    constructor(public operand: FormulationPart, public op: string) {
        super();
        this.type = FormulationPartType.UNARY_OP;
    }
}
export class PlaceholderPart extends FormulationPart {
    getName(): string {
        return `?`;
    }
    constructor() {
        super();
        this.type = FormulationPartType.INPUT;
    }
}