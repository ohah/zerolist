import type { Item, HeightMode } from './types';

// 결정론적 데이터셋 — 시드 기반이라 실행마다 동일(공정 비교 전제).

const WORDS =
  'lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore'.split(
    ' '
  );

function text(seed: number, n: number): string {
  let s = '';
  for (let i = 0; i < n; i++) s += WORDS[(seed + i * 7) % WORDS.length] + ' ';
  return s.trim();
}

const FIXED_H = 88;

export function makeItems(count: number, height: HeightMode): Item[] {
  const items: Item[] = [];
  for (let i = 0; i < count; i++) {
    // body 길이를 시드로 흔들어 dynamic 모드에서 실제 높이 편차를 만든다.
    const bodyLen = 3 + ((i * 37) % 18);
    const h = height === 'fixed' ? FIXED_H : 64 + ((i * 53) % 140);
    items.push({
      id: i,
      title: `#${i} ${text(i, 3)}`,
      body: text(i + 1, bodyLen),
      height: h,
      hue: (i * 47) % 360,
    });
  }
  return items;
}
