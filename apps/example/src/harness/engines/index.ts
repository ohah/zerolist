import type { ForwardRefExoticComponent, RefAttributes } from 'react';
import { FlatListEngine } from './flatlist';
import type { EngineId, ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';

type EngineComponent = ForwardRefExoticComponent<
  ListEngineProps & RefAttributes<Scrollable>
>;

// 미구현 엔진은 null — Harness 가 "미구현" 표기. Phase C-2/B 에서 합류.
export const ENGINES: Record<EngineId, EngineComponent | null> = {
  flatlist: FlatListEngine,
  legend: null,
  flashlist: null,
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
