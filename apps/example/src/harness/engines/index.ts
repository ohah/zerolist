import type { ForwardRefExoticComponent, RefAttributes } from 'react';
import { FlatListEngine } from './flatlist';
import { LegendEngine } from './legend';
import { FlashListEngine } from './flashlist';
import { NativeFabricEngine } from './native';
import type { EngineId, ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';

type EngineComponent = ForwardRefExoticComponent<
  ListEngineProps & RefAttributes<Scrollable>
>;

// zerolist③ 는 Phase B-2. native = RN 내 Fabric 임베드 네이티브 리스트.
export const ENGINES: Record<EngineId, EngineComponent | null> = {
  flatlist: FlatListEngine,
  legend: LegendEngine,
  flashlist: FlashListEngine,
  native: NativeFabricEngine,
  zerolist: null,
};

// 라벨은 Maestro tapOn ^...$ 정규식에 안전하게(공백/괄호 없음).
export const ENGINE_LABEL: Record<EngineId, string> = {
  flatlist: 'FlatList',
  legend: 'Legend List',
  flashlist: 'FlashList',
  native: 'FabricNative',
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
