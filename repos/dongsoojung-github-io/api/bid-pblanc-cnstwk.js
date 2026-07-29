/**
 * 나라장터 공사 입찰공고 → Supabase 프록시
 * GET/POST /api/bid-pblanc-cnstwk
 */
import {
  createBidHandler,
  parseBidPayload,
  normalizeItem,
  buildUrl,
  encodeServiceKey,
  PAGE_SIZE,
  formatYmdHm,
  daysAgoYmdHm,
  KIND_CONFIG,
} from './_lib/bid-pblanc-core.js';

export default createBidHandler('cnstwk');

export const __test = {
  parseBidPayload,
  normalizeItem,
  buildUrl: (params, apiKey) => buildUrl(KIND_CONFIG.cnstwk.apiUrl, params, apiKey),
  encodeServiceKey,
  PAGE_SIZE,
  formatYmdHm,
  daysAgoYmdHm,
};
