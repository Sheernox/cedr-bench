/** Tab navigation is independent of document persistence. */
export class Tabs {
  private order: string[] = [];
  private selected: string | null = null;
  open(id: string): void {
    if (!this.order.includes(id)) this.order.push(id);
    this.selected = id;
  }
  close(id: string): string | null {
    const index = this.order.indexOf(id);
    if (index < 0) return this.selected;
    this.order.splice(index,1);
    if (this.selected === id) this.selected = this.order[Math.min(index,this.order.length-1)] ?? null;
    return this.selected;
  }
  select(id: string): void {
    if (!this.order.includes(id)) throw new Error("tab is not open");
    this.selected = id;
  }
  move(id: string,index: number): void {
    const old = this.order.indexOf(id);
    if (old < 0) throw new Error("tab is not open");
    if (!Number.isInteger(index) || index < 0 || index >= this.order.length) throw new RangeError("invalid tab index");
    this.order.splice(old,1);
    this.order.splice(index,0,id);
  }
  next(direction: 1 | -1 = 1): string | null {
    if (!this.order.length) return null;
    const index = this.selected === null ? 0 : this.order.indexOf(this.selected);
    this.selected = this.order[(index+direction+this.order.length)%this.order.length];
    return this.selected;
  }
  active(): string | null {
    return this.selected;
  }
  all(): string[] {
    return [...this.order];
  }
  restore(ids: readonly string[],selected: string | null): void {
    if (new Set(ids).size !== ids.length) throw new Error("duplicate tabs");
    if (selected !== null && !ids.includes(selected)) throw new Error("selected tab is missing");
    this.order = [...ids];
    this.selected = selected;
  }
}
