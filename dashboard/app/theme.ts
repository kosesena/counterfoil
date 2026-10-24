// AG Studio theme. Every value points at a token in ./globals.css, so Studio's widgets, grids and
// charts share the page's paper, ink and soft palette. The chart palette is ordered by meaning:
// amber (agent misled), terracotta (harm), green (stopped / safe); see ./report.ts.

import { studioTheme } from 'ag-studio';
import { ROW_HEIGHT } from './report';

const token = (name: string) => `var(--cf-${name})`;
const line = (color: string) => ({ width: 1, color: token(color) });

const palette = Object.fromEntries(
  Array.from({ length: 6 }, (_, i) => [
    [`chartPaletteFills${i + 1}Color`, token(`chart-${i + 1}`)],
    [`chartPaletteStrokes${i + 1}Color`, token(`chart-${i + 1}-edge`)],
  ]).flat(),
);

// Studio pads the canvas and every widget; widgets sit two paddings apart. Half the page gutter
// (globals.css --cf-gutter: 24px, 12px on phones) for both keeps widget edges in line with the hero.
export const canvasPadding = (compact: boolean) => (compact ? 6 : 12);

const params = {
  fontFamily: token('font'),
  fontSize: 14,
  textColor: token('ink'),
  foregroundColor: token('ink'),
  subtleTextColor: token('muted'),
  backgroundColor: token('surface'),
  borderColor: token('border'),
  accentColor: token('accent'),
  iconColor: token('ink'),
  rowHoverColor: token('highlight'),

  studioWrapperBorder: false,
  studioWrapperBorderRadius: 0,
  studioWrapperSpacing: 0,
  studioWrapperBackgroundColor: token('canvas'),
  studioCanvasBorder: false,
  studioCanvasBorderRadius: 0,
  studioCanvasShadow: false,
  studioCanvasBackgroundColor: token('canvas'),
  studioCanvasRowHeight: ROW_HEIGHT,
  studioCanvasFontFamily: token('font'),

  studioWidgetBackgroundColor: 'transparent',
  studioWidgetBorder: false,
  studioWidgetBorderRadius: 14,
  studioWidgetTitleFontFamily: token('font'),
  studioWidgetTitleFontSize: 14,
  studioWidgetTitleTextColor: token('ink'),
  studioWidgetTitleFontWeight: 600,
  studioWidgetSubtitleFontFamily: token('font'),
  studioWidgetSubtitleFontSize: 12,
  studioWidgetSubtitleTextColor: token('muted'),
  studioWidgetCaptionFontFamily: token('font'),
  studioWidgetCaptionFontSize: 12,
  studioWidgetCaptionTextColor: token('muted'),
  studioWidgetResizeBorderColor: token('accent'),

  studioPanelContainerBackgroundColor: token('surface'),
  studioPanelContainerBorder: line('border'),
  studioPanelContainerBorderRadius: 0,
  studioPanelDividerColor: token('border'),
  studioPanelDividerActiveColor: token('accent'),
  studioPanelSectionBorderColor: token('border'),
  studioPanelHeaderFontFamily: token('font'),
  studioPanelHeaderFontWeight: 600,
  studioPanelChevronButtonHoverBackgroundColor: token('highlight'),
  studioPanelChevronButtonHoverColor: token('accent'),
  studioToggleButtonActiveBackgroundColor: token('accent'),
  studioToggleButtonActiveBorderColor: token('accent'),
  studioToggleButtonActiveColor: token('on-accent'),

  gridFontFamily: token('font'),
  gridFontSize: 13,
  gridCellTextColor: token('ink'),
  gridHeaderBackgroundColor: token('surface'),
  gridHeaderTextColor: token('muted'),
  gridHeaderFontWeight: 500,
  gridHeaderFontSize: 12,
  gridRowHeight: 38,
  gridRowBorder: line('gridline'),
  gridHeaderRowBorder: line('border'),
  gridPinnedRowBorder: line('border'),
  gridRowHoverColor: token('highlight'),
  gridWrapperBorder: false,

  chartFontFamily: token('font'),
  chartTextColor: token('ink'),
  chartSubtleTextColor: token('muted'),
  chartAxisLineColor: token('border'),
  chartGridLineColor: 'transparent',
  ...palette,
};

export const counterfoilTheme = (compact: boolean) =>
  studioTheme.withParams({
    ...params,
    studioCanvasPadding: canvasPadding(compact),
    studioWidgetPadding: canvasPadding(compact),
    // Studio's defaults (600 / 720 px) would make a phone scroll sideways.
    ...(compact && { studioMinWidth: 320, studioCanvasMinWidth: 320 }),
  });
