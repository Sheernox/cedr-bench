/** UTF-16 offsets match JavaScript editor selections, including surrogate pairs. */
export interface Position { line: number; column: number }
export class LineMap {
  private starts: number[] = [0];
  private text: string;
  constructor(text: string) {
    this.text = text;
    for (let i=0;i<text.length;i++) if (text[i] === "\n") this.starts.push(i+1);
  }
  lines(): number {
    return this.starts.length;
  }
  position(offset: number): Position {
    if (!Number.isInteger(offset) || offset < 0 || offset > this.text.length) throw new RangeError("offset outside document");
    let low = 0;
    let high = this.starts.length;
    while (low+1 < high) {
      const middle = (low+high)>>>1;
      if (this.starts[middle] <= offset) low = middle;
      else high = middle;
    }
    return {line:low,column:offset-this.starts[low]};
  }
  offset(position: Position): number {
    const {line,column} = position;
    if (!Number.isInteger(line) || line < 0 || line >= this.starts.length ||
        !Number.isInteger(column) || column < 0) throw new RangeError("invalid position");
    const end = line+1 < this.starts.length ? this.starts[line+1]-1 : this.text.length;
    if (this.starts[line]+column > end) throw new RangeError("column outside line");
    return this.starts[line]+column;
  }
  line(number: number): string {
    const start = this.offset({line:number,column:0});
    const end = number+1 < this.starts.length ? this.starts[number+1]-1 : this.text.length;
    return this.text.slice(start,end).replace(/\r$/u,"");
  }
}
