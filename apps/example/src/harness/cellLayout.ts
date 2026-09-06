import type { CellType } from './types';

// Fixed rows reserve the same space in data, virtualizer hints and native slots.
// Body text uses at most 3 lines outside dynamic mode; 64 dots still render.
export function fixedCellHeight(
  cell: CellType,
  width: number,
  fontScale: number
) {
  const scale = Math.max(1, fontScale);
  const text = (20 + 3 * 20 + (cell === 'heavy' ? 20 : 0)) * scale;
  const imageRow = Math.max(56, text);
  if (cell === 'simple') return Math.ceil(40 + 24 * scale);
  if (cell === 'image') return Math.ceil(40 + imageRow);
  if (cell === 'complex') return Math.ceil(40 + imageRow + 8 + 32 * scale);
  const columns = Math.max(1, Math.floor((width - 28 + 2) / 20));
  const grid = Math.ceil(64 / columns) * 20;
  return Math.ceil(40 + imageRow + 8 + 6 + grid);
}
