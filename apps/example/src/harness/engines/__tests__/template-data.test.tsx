import { describe, it, expect } from '@jest/globals';
import { packItems, columnItem } from '../templateData';
import type { Item } from '../../types';

describe('UI 데이터 전달 값 보존', () => {
  it('인덱스와 다른 ID, 한글/이모지/따옴표/줄바꿈과 숫자 값을 보존한다', () => {
    const items: Item[] = [
      {
        id: 91,
        title: '한글 😀 "제목"',
        body: '첫째\n둘째\u0000끝',
        height: 234.5,
        hue: -47,
      },
      { id: 3, title: '', body: '𠮷/\\', height: 0, hue: 360.25 },
    ];
    const decoded = JSON.parse(JSON.stringify(packItems(items)));
    expect(items.map((_, i) => columnItem(decoded, i))).toEqual(items);
  });
  it('반복 여부에 관계없이 모든 행을 보존하고 원본을 변경하지 않는다', () => {
    const item = Object.freeze({
      id: 42,
      title: '같은 제목',
      body: '내용',
      height: 100,
      hue: 2,
    });
    const input = Object.freeze([item, item]);
    const decoded = JSON.parse(JSON.stringify(packItems(input)));
    expect([columnItem(decoded, 0), columnItem(decoded, 1)]).toEqual(input);
    expect(columnItem(decoded, 2)).toBeUndefined();
    expect(columnItem(decoded, -1)).toBeUndefined();
  });
  it('빈 데이터는 임의의 행을 만들어내지 않는다', () => {
    expect(columnItem(packItems([]), 0)).toBeUndefined();
  });
});
