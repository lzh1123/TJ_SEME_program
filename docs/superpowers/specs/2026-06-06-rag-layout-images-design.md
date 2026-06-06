# Design Spec: RAG Default, Image Support & Modern Layout

**Date:** 2026-06-06
**Status:** Approved
**Feature Branch:** `feature/rag`

---

## Overview

Three interconnected improvements to the Slideon PPT generation platform:

1. **RAG-by-default with hybrid toggle** — Backend RAG (KB + web search) is ON by default; frontend gets a simple ON/OFF toggle. Image search is always enabled.
2. **Image support** — Images as slide backgrounds AND inline content components, sourced from web image search via RAG.
3. **Modern layout overhaul** — Expand from 8 basic slot layouts to ~17 layouts with smart selection, visual enhancements, and modern AI-PPT aesthetics.

---

## Section 1: RAG Toggle (Default ON, Always Hybrid)

### 1.1 Behavior

| Aspect | Current | Target |
|--------|---------|--------|
| `use_rag` default | `False` | `True` |
| RAG mode on toggle ON | Hybrid (KB + web) | Hybrid (KB + web) — unchanged |
| Image search | Only via explicit `/rag/images/search` call | Always included alongside text context |
| Frontend toggle | None | ON/OFF switch, default ON |

### 1.2 Backend Changes

#### `api/routes.py`
- `CreatePresentationRequest.use_rag`: default `False` → `True`
- `GenerateOutlineRequest.use_rag`: default `False` → `True`
- `RegenerateRequest.use_rag`: default `False` → `True`

#### `services/presentation_service.py`
- `create()` / `generate_outline()` / `regenerate()`:
  When `use_rag=True`, call both `rag.retrieve_context(topic)` AND `rag.search_images(topic)`
  Pass both context string AND image list into the AI pipeline

#### `services/ai/pipeline.py`
- `generate_dsl_with_debug()`: Accept optional `rag_images: list[dict]` parameter
- Include image hints in the system prompt so AI sets `image_query` on relevant slides
- Image URLs/descriptions embedded in prompt as reference for the AI

### 1.3 Frontend Changes

#### `components/common/OutlineModal.vue`
- Add RAG toggle switch in the style-selection area (step 2)
- Default: ON (blue/active)
- Label: "混合RAG增强 (知识库 + 网络搜索)"
- Small description text below: "AI将参考知识库和网络资料生成更专业的内容"

#### `services/api.js`
- `generateOutline()`: Add `useRag: true` to payload
- `createPresentation()`: Add `useRag: true` to payload
- `regenerate()`: Add `useRag: true` to payload

#### `config/api.js`
- `UPLOAD_CONFIG.allowedTypes`: Extension list already supports document uploads for KB

---

## Section 2: Image Support (Backgrounds + Content Components)

### 2.1 DSL Layer

Add optional image-related fields to base slide model:

```python
# In domain/dsl.py — add to base class or individual slide models:
image_query: Optional[str] = None   # AI sets this when slide benefits from imagery
```

The AI pipeline, when given image hints from RAG, can set `image_query` on slides where visuals would enhance the content.

### 2.2 RenderTree Model

Already has `"Image"` in `ComponentType` and `background` on `RenderSlide`. Extend:

```python
# ComponentSpec.props for Image type:
{
    "url": str,          # Image URL
    "alt": str,          # Alt text / description
    "query": str,        # Original search query used
    "fit": "cover" | "contain"  # Object-fit mode
}
```

### 2.3 Compiler / Planning Layer

**New: `ImageComposer` logic** — Not a separate composer, but integrated into existing composers:
- **Cover**: If `image_query` is set, set slide background from matching image
- **Text/Bullet slides**: If content is rich, add an Image component in a secondary column (asymmetric split: text-left + image-right)
- **Divider**: Optionally use image as full-slide background with gradient overlay

**Image assignment**: Images are matched to slides by `image_query` → RAG image search result. The compiler receives a `dict[slide_id, list[image_urls]]` map.

### 2.4 Layout

Two new layouts for image-containing slides:
- `image_hero`: Full-width image with title overlay (for covers, dividers)
- `text_image_split`: 55/45 or 45/55 split with text on one side, image on the other

### 2.5 Frontend Changes

#### `EditorView.vue` — New Image component:

```vue
<div v-else-if="component.type === 'Image'" class="component-image"
     :style="getComponentStyle(component)">
  <img :src="component.props?.url"
       :alt="component.props?.alt || ''"
       :style="{ objectFit: component.props?.fit || 'cover' }"
       @error="onImageError" />
</div>
```

#### Slide background:
- `getCanvasStyle()`: When slide has `backgroundImage`, render `background-image: url(...)` with `background-size: cover`
- Gradient overlay div on top for readability when text is over background

#### Placeholder:
- Before load: shimmer/gradient placeholder
- On error: themed placeholder with icon

### 2.6 Image Source

- Images come from `rag.search_images(query)` → `web_search.py` (`WebSearchService.search_images()`)
- Stored per-slide in `RenderTree.meta["images"]` as `{slide_id: [url, ...]}`
- The compiler assigns best-matching image to each slide with `image_query`

---

## Section 3: Modern Layout Overhaul

### 3.1 New Layout Templates

| # | Layout ID | Description | Primary Intent |
|---|-----------|-------------|----------------|
| 1 | `cover` | (existing) Title center + subtitle + highlights | cover |
| 2 | `title_body` | (existing) Top title + body area | text, agenda, kpi (≤3) |
| 3 | `two_column` | (existing) 50/50 split | comparison, multi_column |
| 4 | `grid_2x2` | (existing) 2×2 equal grid | swot |
| 5 | `timeline` | (existing) Title + body for timeline | timeline |
| 6 | `roadmap` | (existing) Title + body for roadmap | roadmap |
| 7 | `process_flow` | (existing) Title + body for process | process_flow |
| 8 | `chart` | (existing) Title + body for chart | chart |
| 9 | `divider` | (existing) Centered body | divider |
| 10 | **`magazine_hero`** | Large title left 38% + stat/visual right 62%, accent bar | cover, key slides |
| 11 | **`big_number_grid`** | 3-4 giant KPI numbers, label underneath, equal grid | kpi (≥4 items) |
| 12 | **`asymmetric_split`** | 62/38 or 38/62 split with accent bar on larger side | text+image, comparisons |
| 13 | **`card_masonry`** | 3 cards: 2 top (50/50) + 1 bottom (centered, 50%) | multi_column, team |
| 14 | **`step_numbered`** | Horizontal steps, oversized outlined numbers (01, 02...) + arrows | process_flow |
| 15 | **`quote_centered`** | Centered quote, oversized " mark (decorative), author below | quote |
| 16 | **`bento_grid`** | 2×2 unequal: one cell 2×1 tall, others 1×1 | swot, multi_column |
| 17 | **`gradient_overlay`** | Full-slide gradient + centered title/subtitle + accent line | divider, section header |

### 3.2 Smart Layout Selector

New file: `services/rendering/layout_selector.py`

```python
def select_layout(
    intent: str,
    content_count: int,
    has_image: bool,
    item_count: int = 0,
) -> LayoutId:
    """Deterministic layout selection based on content characteristics."""
```

Rules (examples):
- KPI with ≥4 items → `big_number_grid` (not `title_body`)
- Comparison with image → `asymmetric_split` (not `two_column`)
- Process flow → `step_numbered` (not old `process_flow`)
- Quote → `quote_centered` (not `title_body`)
- Cover with highlights ≥ 4 → `magazine_hero` (not `cover`)
- SWOT → `bento_grid` (not `grid_2x2`)
- Divider → `gradient_overlay` (not `divider`)

The selector is **purely deterministic** — no LLM calls, fast and predictable.

### 3.3 Visual Enhancements

1. **Accent bars**: Colored left-edge or top-edge bar on title/body regions using `theme.colors.primary`
2. **Gradient overlays**: Subtle gradient from theme colors on cover/divider slides
3. **Numbered callouts**: Step numbers as large outlined digits (`01`, `02`) in `step_numbered` layout
4. **Golden-ratio spacing**: Title-to-body ratio ~1.618:1 instead of fixed 96px title height
5. **Card styling**: Cards get `box-shadow`, `border-radius: 12px`, colored top-border from theme

### 3.4 Theme Token Extensions

```python
# domain/theme.py — SpacingTokens additions:
class SpacingTokens(BaseModel):
    slide_padding_px: int = 64
    gap_px: int = 24
    title_body_ratio: float = 1.618   # NEW: golden ratio for title/body split
    accent_bar_width: int = 4         # NEW
    card_radius: int = 12             # NEW
    card_shadow: str = "0 2px 12px rgba(0,0,0,0.08)"  # NEW
```

### 3.5 Files to Modify

| File | Change |
|------|--------|
| `layout.py` | Add 9 new layout classes; update slot calculations |
| `planning.py` | Update composer layout_id assignments; add image-aware composition |
| `layout_selector.py` | **New file** — smart layout selection logic |
| `compiler.py` | Integrate layout selector; pass image map to composers |
| `theme.py` | Extend SpacingTokens with new layout tokens |
| `EditorView.vue` | Update CSS for accent bars, gradients, card shadows, numbered callouts; add Image component |

### 3.6 Backward Compatibility

- Existing 8 layout classes remain, mapped through the selector
- Theme token extensions have defaults — old themes work unchanged
- Old render trees (without `backgroundImage` or image components) render identically
- The `layout_selector` falls back to old layout IDs when content doesn't trigger new rules

---

## Implementation Order

Feature-parallel, three milestones:

### Milestone 1: RAG Toggle (backend + frontend)
1. Backend: Change defaults, wire image search into pipeline
2. Frontend: Add toggle UI, update API calls

### Milestone 2: Layout Overhaul
1. Backend: Add 9 new layouts, layout selector, theme token extensions
2. Frontend: Update component CSS for new visual styles

### Milestone 3: Image Support
1. Backend: Update DSL, composers, compiler for image components & backgrounds
2. Frontend: Add Image component rendering, background-image support, placeholders

---

## Testing Plan

### RAG Toggle
- Verify `use_rag=True` by default in all API calls
- Toggle OFF → no RAG context in prompt, no image search
- Toggle ON → context + images returned in response
- Image search always included when RAG is ON

### Image Rendering
- Image component renders correctly at specified position/size
- Slide background image with gradient overlay renders
- Broken image URL → fallback placeholder shown
- Image search returns valid URLs

### Layout
- All 17 layouts produce valid component positions (no overlaps, within slide bounds)
- Layout selector picks appropriate layout for each intent+content combination
- Visual enhancements (accent bars, gradients, cards) render correctly in frontend
- Old render trees still render correctly
