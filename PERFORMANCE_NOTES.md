# Performance Optimization Notes

## Current Implementation

### Preloading Strategy (v2.0)
- **When**: Words are preloaded when the home page renders
- **What**: Both new words and review words are fetched in the background
- **Cached in**: `st.session_state.preloaded_new_words` and `st.session_state.preloaded_review_words`

### User Flow:
1. User lands on home page → Words preload automatically in background
2. User clicks "Start Learning" → Uses cached words (INSTANT, <0.1s)
3. User completes session → Cache is cleared
4. User returns home → New words are preloaded again

### Expected Performance:
- **First click on "Start Learning"**: Instant (uses preloaded cache)
- **Subsequent sessions**: Instant (cache refreshed on home page)

### API Optimizations:
1. **get_stats()**: 1 API call (was 4)
2. **get_new_words()**: Fetches only 60 words with 2 fields (was 100 with all fields)
3. **get_review_words()**: Server-side filtering (was client-side after full fetch)

### Known Limitations:
- Network latency to Feishu API cannot be eliminated (1-2s baseline)
- Preloading only works after first home page visit
- Very first app load will still have initial API delay
