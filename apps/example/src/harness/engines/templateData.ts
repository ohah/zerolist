import type { Item } from '../types';

export type Columns = {
  id: number[];
  title: string[];
  body: string[];
  height: number[];
  hue: number[];
};

// 동일한 실제 값을 보존한다. 반복 데이터 사전이나 인덱스 기반 재생성은 없다.
export function packItems(items: readonly Item[]): Columns {
  const columns: Columns = { id: [], title: [], body: [], height: [], hue: [] };
  for (const item of items) {
    columns.id.push(item.id);
    columns.title.push(item.title);
    columns.body.push(item.body);
    columns.height.push(item.height);
    columns.hue.push(item.hue);
  }
  return columns;
}

export function columnItem(source: Columns, index: number): Item | undefined {
  'worklet';
  if (index < 0 || index >= source.id.length) return undefined;
  return {
    id: source.id[index]!,
    title: source.title[index]!,
    body: source.body[index]!,
    height: source.height[index]!,
    hue: source.hue[index]!,
  };
}
