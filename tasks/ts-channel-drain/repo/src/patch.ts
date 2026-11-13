/** Disjoint text edits use original offsets, applied from right to left. */
export interface Edit { start: number; end: number; text: string }
export function apply(text: string,edits: readonly Edit[]): string {
  const sorted = [...edits].sort((a,b) => a.start-b.start || a.end-b.end);
  let previous = -1;
  for (const edit of sorted) {
    if (!Number.isInteger(edit.start) || !Number.isInteger(edit.end) || edit.start < 0 ||
        edit.end < edit.start || edit.end > text.length || edit.start < previous) throw new RangeError("invalid overlapping edits");
    previous = edit.end;
  }
  let result = text;
  for (const edit of sorted.reverse()) result = result.slice(0,edit.start)+edit.text+result.slice(edit.end);
  return result;
}
export function replaceAll(text: string,needle: string,replacement: string): Edit[] {
  if (!needle) throw new Error("empty search text");
  const result: Edit[] = [];
  let offset = 0;
  while (offset <= text.length) {
    const index = text.indexOf(needle,offset);
    if (index < 0) break;
    result.push({start:index,end:index+needle.length,text:replacement});
    offset = index+needle.length;
  }
  return result;
}
export function invert(text: string,edits: readonly Edit[]): Edit[] {
  apply(text,edits);
  let shift = 0;
  return [...edits].sort((a,b) => a.start-b.start).map(edit => {
    const inverse = {start:edit.start+shift,end:edit.start+shift+edit.text.length,text:text.slice(edit.start,edit.end)};
    shift += edit.text.length-(edit.end-edit.start);
    return inverse;
  });
}
