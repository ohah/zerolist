import type { ForwardRefExoticComponent, RefAttributes } from 'react';
import { FlatListEngine } from './flatlist';
import { LegendEngine } from './legend';
import { FlashListEngine } from './flashlist';
import type { EngineId, ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';

type EngineComponent = ForwardRefExoticComponent<
  ListEngineProps & RefAttributes<Scrollable>
>;

// native/zerolist 는 네이티브 빌드 필요 — Phase B 에서 합류.
export const ENGINES: Record<EngineId, EngineComponent | null> = {
  flatlist: FlatListEngine,
  legend: LegendEngine,
  flashlist: FlashListEngine,
  native: null,
  zerolist: null,
};

export const ENGINE_LABEL: Record<EngineId, string> = {
  flatlist: 'FlatList',
  legend: 'Legend List',
  flashlist: 'FlashList',
  native: 'Native (RN내 Fabric)',
  zerolist: 'ZeroList ③',
};

// fixed/variable 에서 각 엔진이 받는 레이아웃 힌트(비대칭을 수치에 동행).
export const ENGINE_HINT: Record<EngineId, string> = {
  flatlist: 'getItemLayout',
  legend: 'estimatedSize',
  flashlist: 'none(auto)',
  native: 'offsets',
  zerolist: 'offsets',
};
