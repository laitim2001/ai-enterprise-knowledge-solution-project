/**
 * Unit tests — en / zh 字典守門 (W103 F7.3)。
 *
 * 呢層唔 render 任何組件,純粹守住字典本身的不變式。價值在於**將來**:加新
 * key 時漏咗 zh、rich tag 打錯、ICU 語法寫壞,都會喺呢度即刻紅,唔使等到
 * runtime 先爆(next-intl 對缺 key 係 throw,唔係靜靜 fallback)。
 *
 * 亦守住 W103 F7 的標點正規化成果 —— 中文緊貼半形逗號 / 冒號 / 分號會回歸
 * 紅燈。**括號例外**:27 條「中文標籤 + 空格 + 半形括號包純西文」
 * (`應用程式 (client) ID`)係 2026-07-20 明確拍板保持半形,故不檢查括號。
 */

import { describe, expect, it } from 'vitest';

import enMessages from '../../messages/en.json';
import zhMessages from '../../messages/zh.json';

type Dict = Record<string, unknown>;

function flatten(obj: Dict, prefix = '', out: Record<string, string> = {}) {
  for (const [key, value] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      flatten(value as Dict, path, out);
    } else {
      out[path] = String(value);
    }
  }
  return out;
}

const en = flatten(enMessages as Dict);
const zh = flatten(zhMessages as Dict);

/** ICU 參數名(`{name}` / `{count, plural, …}` 都只取參數名)。 */
function placeholders(value: string): string[] {
  return [...value.matchAll(/\{([a-zA-Z0-9_]+)[,}]/g)].map((m) => m[1]).sort();
}

/** rich-text tag(`<b>` / `<mono>` / `<terms>` …)。 */
function tags(value: string): string[] {
  return [...value.matchAll(/<\/?[a-zA-Z][a-zA-Z0-9]*>/g)].map((m) => m[0]).sort();
}

describe('i18n 字典 — en / zh 對稱性', () => {
  it('兩邊 key 集合完全一致(冇缺漏、冇多餘)', () => {
    expect(Object.keys(zh).filter((k) => !(k in en))).toEqual([]);
    expect(Object.keys(en).filter((k) => !(k in zh))).toEqual([]);
  });

  it('每條 key 的 ICU 參數集合兩邊一致', () => {
    const mismatched = Object.keys(en)
      .filter((k) => k in zh)
      .filter((k) => placeholders(en[k]).join() !== placeholders(zh[k]).join());
    expect(mismatched).toEqual([]);
  });

  it('每條 key 的 rich-text tag 集合兩邊一致', () => {
    const mismatched = Object.keys(en)
      .filter((k) => k in zh)
      .filter((k) => tags(en[k]).join() !== tags(zh[k]).join());
    expect(mismatched).toEqual([]);
  });

  it('冇空字串值(漏譯會變空白 UI)', () => {
    expect(Object.keys(zh).filter((k) => zh[k].trim() === '')).toEqual([]);
  });
});

describe('i18n 字典 — zh 中文排版', () => {
  const CJK = '\\u4e00-\\u9fff\\u3400-\\u4dbf';

  it('中文唔會緊貼半形逗號 / 冒號 / 分號(W103 F7 正規化守門)', () => {
    const before = new RegExp(`[${CJK}][,;:]`);
    const after = new RegExp(`[,;:][${CJK}]`);
    const offenders = Object.keys(zh).filter((k) => {
      // 先剝走 ICU placeholder 同 tag —— 佢哋內部的標點屬語法,唔算排版。
      const stripped = zh[k].replace(/\{[^{}]*\}|<[^<>]*>|https?:\/\/\S+/g, '');
      return before.test(stripped) || after.test(stripped);
    });
    expect(offenders).toEqual([]);
  });

  it('中文後面唔會用三點省略號(應用「…」)', () => {
    const dots = new RegExp(`[${CJK}]\\.\\.\\.`);
    expect(Object.keys(zh).filter((k) => dots.test(zh[k]))).toEqual([]);
  });
});

describe('i18n 字典 — 刻意保留英文的項目', () => {
  // 保留清單的抽樣:vendor / 產品名 / metric 名喺兩個 locale 必須一模一樣,
  // 否則就係有人「順手翻譯」咗唔應該譯的technical identifier。
  it.each([
    'Common.appName',
    'Dashboard.statRecall',
    'Eval.colRecall5',
    'Traces.colCrag',
    'KbDetail.modeHybridHint',
  ])('%s 在 en / zh 保持一致', (key) => {
    expect(zh[key]).toBe(en[key]);
  });
});
