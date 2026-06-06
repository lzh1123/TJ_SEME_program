# RAG Default, Image Support & Modern Layout — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make RAG hybrid search ON by default with a frontend toggle, add image generation + rendering (backgrounds and inline components), and overhaul the layout system from 8 basic templates to 17 modern layouts with smart selection.

**Architecture:** Three milestones, feature-parallel: (1) RAG toggle — backend defaults + frontend UI + always-on image search, (2) Layout overhaul — 9 new layout classes + smart selector + visual enhancements, (3) Image support — DSL image_query → compiler → frontend rendering.

**Tech Stack:** Python/FastAPI/Pydantic backend + Vue 3 frontend. Existing: Milvus vector DB, LangChain, python-pptx.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `backend/ppt_backend/api/routes.py` | Change `use_rag` defaults to `True` |
| Modify | `backend/ppt_backend/services/presentation_service.py` | Wire image search into RAG flow |
| Modify | `backend/ppt_backend/services/ai/pipeline.py` | Accept `rag_images`, add image hints to prompt |
| Modify | `backend/ppt_backend/domain/dsl.py` | Add `image_query` to `BaseSlideDSL` |
| Modify | `backend/ppt_backend/domain/render_tree.py` | Add `backgroundImage` to `RenderSlide` |
| Modify | `backend/ppt_backend/domain/theme.py` | Extend `ThemeSpacing` with layout tokens |
| Create | `backend/ppt_backend/services/rendering/layout_selector.py` | Smart deterministic layout selector |
| Modify | `backend/ppt_backend/services/rendering/layout.py` | Add 9 new layout classes |
| Modify | `backend/ppt_backend/services/rendering/planning.py` | Update composers with new layouts + image logic |
| Modify | `backend/ppt_backend/services/rendering/compiler.py` | Integrate layout selector + image map |
| Modify | `slideon-frontend/src/components/common/OutlineModal.vue` | Add RAG toggle UI |
| Modify | `slideon-frontend/src/services/api.js` | Pass `useRag` in API calls |
| Modify | `slideon-frontend/src/views/EditorView.vue` | Image component + visual enhancements |

---

## Milestone 1: RAG Toggle (Default ON, Always Hybrid)

### Task 1.1: Backend — Change `use_rag` defaults to `True`

**Files:**
- Modify: `backend/ppt_backend/api/routes.py:33, 69, 61`

- [ ] **Step 1: Change `CreatePresentationRequest.use_rag` default**

Edit `backend/ppt_backend/api/routes.py`, line 33:
```python
# Before:
    use_rag: bool = False

# After:
    use_rag: bool = True
```

- [ ] **Step 2: Change `GenerateOutlineRequest.use_rag` default**

Edit `backend/ppt_backend/api/routes.py`, line 69:
```python
# Before:
    use_rag: bool = False

# After:
    use_rag: bool = True
```

- [ ] **Step 3: Change `RegenerateRequest.use_rag` default**

Edit `backend/ppt_backend/api/routes.py`, line 61:
```python
# Before:
    use_rag: bool = False

# After:
    use_rag: bool = True
```

- [ ] **Step 4: Commit**

```bash
git add backend/ppt_backend/api/routes.py
git commit -m "feat: set use_rag default to True in all request models"
```

---

### Task 1.2: Backend — Wire image search into RAG flow in PresentationService

**Files:**
- Modify: `backend/ppt_backend/services/presentation_service.py:34-48, 49-61, 243-265`

- [ ] **Step 1: Update `create()` to fetch images when RAG is enabled**

Edit `backend/ppt_backend/services/presentation_service.py`. Replace the `create()` method's RAG block (lines 36-39):

```python
    def create(self, topic: str, theme: Optional[str] = None, use_rag: bool = False) -> PresentationBundle:
        presentation_id = new_id("pres")
        rag_context = ""
        rag_images: list = []
        if use_rag and self._rag:
            rag_context = self._rag.retrieve_context(topic, top_k=5)
            rag_images = self._rag.search_images(topic, max_results=10)
        dsl, ai_debug = self._ai.generate_dsl_with_debug(
            topic=topic, theme=theme, rag_context=rag_context, rag_images=rag_images
        )
        theme_tokens = get_theme_tokens(dsl.theme)
        tree = self._compiler.compile(presentation_id, dsl, theme_tokens, rag_images=rag_images)
        tree = apply_theme_to_tree(tree, theme_tokens)
        meta = PresentationMeta(id=presentation_id, topic=topic)
        meta.extra = {"ai": ai_debug}
        bundle = PresentationBundle(meta=meta, dsl=dsl, renderTree=tree)
        self._repo.save(bundle)
        return bundle
```

- [ ] **Step 2: Update `generate_outline()` to fetch images when RAG is enabled**

Replace the `generate_outline()` method's RAG block:

```python
    def generate_outline(self, topic: str, theme: Optional[str] = None, use_rag: bool = False) -> dict:
        rag_context = ""
        rag_images: list = []
        if use_rag and self._rag:
            rag_context = self._rag.retrieve_context(topic, top_k=5)
            rag_images = self._rag.search_images(topic, max_results=10)
        dsl = self._ai.generate_dsl(topic=topic, theme=theme, rag_context=rag_context, rag_images=rag_images)
        data = dsl.model_dump(by_alias=True)
        slides = data.get("slides") or []
        if isinstance(slides, list):
            for s in slides:
                if isinstance(s, dict):
                    s.pop("id", None)
        data["slides"] = slides
        return data
```

- [ ] **Step 3: Update `regenerate()` to fetch images when RAG is enabled**

Replace the `regenerate()` method's RAG block:

```python
    def regenerate(self, presentation_id: str, topic: Optional[str] = None, section: Optional[str] = None, use_rag: bool = False) -> PresentationBundle:
        bundle = self._repo.load(presentation_id)
        base_topic = topic or bundle.meta.topic
        rag_context = ""
        rag_images: list = []
        if use_rag and self._rag:
            rag_context = self._rag.retrieve_context(base_topic, top_k=5)
            rag_images = self._rag.search_images(base_topic, max_results=10)
        new_dsl, ai_debug = self._ai.generate_dsl_with_debug(
            topic=base_topic, theme=bundle.dsl.theme,
            rag_context=rag_context, rag_images=rag_images
        )
        bundle.meta.extra = {"ai": ai_debug}
        if section:
            old_ids = [s.id for s in bundle.dsl.slides if getattr(s, "section", "") == section]
            new_slides = [s for s in new_dsl.slides if getattr(s, "section", "") == section]
            kept = [s for s in bundle.dsl.slides if s.id not in set(old_ids)]
            bundle.dsl.slides = kept + new_slides
        else:
            bundle.dsl = new_dsl
        tokens = get_theme_tokens(bundle.dsl.theme)
        bundle.render_tree = self._compiler.compile(presentation_id, bundle.dsl, tokens, rag_images=rag_images)
        apply_theme_to_tree(bundle.render_tree, tokens)
        bundle.meta.topic = base_topic
        bundle.meta.updated_at = datetime.now(timezone.utc)
        bundle.meta.version += 1
        self._repo.save(bundle)
        return bundle
```

- [ ] **Step 4: Update `create_from_outline()` to search images for slides with `image_query`**

Replace the `create_from_outline` method:

```python
    def create_from_outline(self, topic: str, outline: dict, theme: Optional[str] = None) -> PresentationBundle:
        presentation_id = new_id("pres")
        hydrated = self._hydrate_outline(outline, topic=topic, theme=theme)
        theme_tokens = get_theme_tokens(hydrated.theme)

        # Search images for slides with image_query
        rag_images: list = []
        if self._rag:
            for slide in hydrated.slides:
                iq = getattr(slide, "image_query", None)
                if iq:
                    imgs = self._rag.search_images(iq, max_results=3)
                    rag_images.extend(imgs)

        tree = self._compiler.compile(presentation_id, hydrated, theme_tokens, rag_images=rag_images if rag_images else None)
        tree = apply_theme_to_tree(tree, theme_tokens)
        meta = PresentationMeta(id=presentation_id, topic=topic)
        bundle = PresentationBundle(meta=meta, dsl=hydrated, renderTree=tree)
        self._repo.save(bundle)
        return bundle
```

- [ ] **Step 5: Commit**

```bash
git add backend/ppt_backend/services/presentation_service.py
git commit -m "feat: wire image search into RAG flow in PresentationService"
```

---

### Task 1.3: Backend — Update AI Pipeline to accept and use `rag_images`

**Files:**
- Modify: `backend/ppt_backend/services/ai/pipeline.py:91-93, 95-96, 127-185`

- [ ] **Step 1: Update `generate_dsl()` signature**

Edit `backend/ppt_backend/services/ai/pipeline.py`. Replace `generate_dsl` method signature:

```python
    def generate_dsl(self, topic: str, theme: Optional[str] = None, rag_context: str = "", rag_images: list = None) -> PresentationDSL:
        dsl, _ = self.generate_dsl_with_debug(topic=topic, theme=theme, rag_context=rag_context, rag_images=rag_images)
        return dsl
```

- [ ] **Step 2: Update `generate_dsl_with_debug()` signature**

Replace `generate_dsl_with_debug` method signature:

```python
    def generate_dsl_with_debug(self, topic: str, theme: Optional[str] = None, rag_context: str = "", rag_images: list = None):
```

- [ ] **Step 3: Add image hints block to the system prompt**

Edit the system prompt in `generate_dsl_with_debug()` (around line 181). After the `rag_block` construction, add an image hint block. Replace lines 188-189:

```python
            rag_block = ""
            if rag_context:
                rag_block = f"\n## 参考资料（请优先使用以下资料中的信息和数据）\n{rag_context}"

            image_hint = ""
            if rag_images:
                image_descriptions = []
                for i, img in enumerate(rag_images[:10]):
                    desc = img.get("alt") or img.get("title") or img.get("query", "")
                    url = img.get("url", "")
                    if desc and url:
                        image_descriptions.append(f"  [{i+1}] {desc}")
                if image_descriptions:
                    image_hint = (
                        "\n## 可用图片资源（来自网络搜索）\n"
                        "以下图片可供使用。对于需要视觉辅助的幻灯片（如封面、分隔页、内容丰富的页），"
                        "请在 slide 对象中设置 image_query 字段，值为图片描述关键词（例如：image_query: \"城市夜景\"）。\n"
                        "适合使用图片的 slide intent：cover, divider, text（内容丰富时）, quote\n"
                        + "\n".join(image_descriptions) + "\n"
                    )
```

- [ ] **Step 4: Pass `image_hint` into the prompt template**

Edit the prompt invocation. Replace lines 192-201 to include `image_hint`:

```python
            raw = invoke_llm_text(
                self._llm,
                prompt,
                {
                    "topic": topic,
                    "analysis_json": analysis.model_dump_json(by_alias=True),
                    "plan_json": plan.model_dump_json(),
                    "theme_name": theme_name,
                    "rag_block": rag_block + image_hint,
                },
            )
```

- [ ] **Step 5: Commit**

```bash
git add backend/ppt_backend/services/ai/pipeline.py
git commit -m "feat: accept rag_images in AI pipeline and add image hints to prompt"
```

---

### Task 1.4: Frontend — Add RAG toggle to OutlineModal

**Files:**
- Modify: `slideon-frontend/src/components/common/OutlineModal.vue`

- [ ] **Step 1: Add `useRag` to form state**

In the `<script setup>` section, add `useRag` after the `form` ref (around line 290):

```javascript
const form = ref({
  topic: '',
  style: 'modern_blue'
})

const useRag = ref(true)
```

- [ ] **Step 2: Add RAG toggle UI in the template**

After the style selection `div.form-step` (after line 51, before the closing `</div>` of step-content), add:

```html
            <div class="form-step">
              <label class="form-label">
                <span class="step-number">3</span>
                AI增强选项
              </label>
              <div class="rag-toggle-row">
                <div class="rag-toggle-label">
                  <span class="rag-toggle-title">混合RAG增强 (知识库 + 网络搜索)</span>
                  <span class="rag-toggle-desc">AI将参考知识库和网络资料生成更专业的内容</span>
                </div>
                <button
                  :class="['rag-toggle-switch', { active: useRag }]"
                  @click="useRag = !useRag"
                  role="switch"
                  :aria-checked="useRag"
                >
                  <span class="rag-toggle-knob"></span>
                </button>
              </div>
            </div>
```

- [ ] **Step 3: Pass `useRag` to `generateOutline` call**

Update the `generateOutline` function to include `useRag`:

```javascript
const generateOutline = async () => {
  if (!form.value.topic.trim()) {
    alert('请输入主题')
    return
  }

  isGenerating.value = true

  try {
    const result = await apiService.generateOutline(form.value.topic, form.value.style, useRag.value)

    console.log('✅ 生成大纲成功:', result)

    outlineData.value = {
      title: result.title || form.value.topic,
      theme: result.theme || form.value.style,
      slides: (result.slides || []).map(prepareSlideForEdit)
    }

    step.value = 'editor'
  } catch (error) {
    console.error('❌ 生成大纲失败:', error)
    alert('生成大纲失败: ' + error.message)
  } finally {
    isGenerating.value = false
  }
}
```

- [ ] **Step 4: Pass `useRag` to `generatePresentation` call**

Update the `generatePresentation` function's API call:

```javascript
const generatePresentation = async () => {
  isGenerating.value = true

  try {
    const outline = {
      ...outlineData.value,
      slides: outlineData.value.slides.map(cleanSlideByIntent)
    }

    const renderTree = await apiService.compileOutline(form.value.topic, outline, form.value.style)

    // ... rest stays the same
```

- [ ] **Step 5: Add toggle CSS styles**

Add after the `.style-radio` styles (after line 773):

```css
.rag-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  gap: var(--space-4);
}

.rag-toggle-label {
  flex: 1;
}

.rag-toggle-title {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: var(--space-1);
}

.rag-toggle-desc {
  display: block;
  font-size: 12px;
  color: var(--gray-500);
  line-height: 1.4;
}

.rag-toggle-switch {
  position: relative;
  width: 48px;
  height: 28px;
  background: var(--gray-300);
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.rag-toggle-switch.active {
  background: var(--primary-500);
}

.rag-toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.rag-toggle-switch.active .rag-toggle-knob {
  transform: translateX(20px);
}
```

- [ ] **Step 6: Commit**

```bash
git add slideon-frontend/src/components/common/OutlineModal.vue
git commit -m "feat: add RAG toggle UI to OutlineModal with default ON"
```

---

### Task 1.5: Frontend — Update API service to pass `useRag`

**Files:**
- Modify: `slideon-frontend/src/services/api.js`

- [ ] **Step 1: Update `generateOutline()` to accept and pass `useRag`**

Edit `slideon-frontend/src/services/api.js`. Replace the `generateOutline` method:

```javascript
  // 生成大纲
  async generateOutline(topic, theme = null, useRag = true) {
    const response = await this.post(API_ENDPOINTS.dsl, {
      topic,
      theme,
      use_rag: useRag
    })
    return response.json()
  }
```

- [ ] **Step 2: Update `createPresentation()` to accept and pass `useRag`**

Replace the `createPresentation` method:

```javascript
  // 创建演示文稿
  async createPresentation(topic, useRag = true) {
    const response = await this.post(API_ENDPOINTS.presentations.create, {
      topic,
      use_rag: useRag
    })
    return response.json()
  }
```

- [ ] **Step 3: Update `compileOutline()` — no `useRag` needed (images determined during outline generation)**

The outline already contains `image_query` fields set by the AI during generation. The backend `create_from_outline` will handle image fetching based on those queries. No change needed to `compileOutline` signature:

```javascript
  // 根据大纲生成渲染树 (image_query fields from outline drive image search on backend)
  async compileOutline(topic, outline, theme = null) {
    const response = await this.post(API_ENDPOINTS.renderTree, {
      topic,
      outline,
      theme
    })
    return response.json()
  }
```

- [ ] **Step 4: Update `regenerate()` to accept and pass `useRag`**

Replace the `regenerate` method:

```javascript
  // 重新生成
  async regenerate(id, topic = null, section = null, useRag = true) {
    const response = await this.post(API_ENDPOINTS.presentations.regenerate(id), {
      topic,
      section,
      use_rag: useRag
    })
    return response.json()
  }
```

- [ ] **Step 5: Commit**

```bash
git add slideon-frontend/src/services/api.js
git commit -m "feat: pass useRag in all API generation calls with default true"
```

---

## Milestone 2: Modern Layout Overhaul

### Task 2.1: Backend — Extend ThemeTokens with new layout spacing fields

**Files:**
- Modify: `backend/ppt_backend/domain/theme.py:30-36, 46-127`

- [ ] **Step 1: Add new fields to `ThemeSpacing`**

Edit `backend/ppt_backend/domain/theme.py`. Replace the `ThemeSpacing` class:

```python
class ThemeSpacing(BaseModel):
    model_config = {"extra": "forbid"}

    slide_padding_px: int = Field(alias="slidePaddingPx")
    gap_px: int = Field(alias="gapPx")
    title_body_ratio: float = Field(default=1.618, alias="titleBodyRatio")
    accent_bar_width: int = Field(default=4, alias="accentBarWidth")
    card_radius: int = Field(default=12, alias="cardRadius")
    card_shadow: str = Field(default="0 2px 12px rgba(0,0,0,0.08)", alias="cardShadow")
```

- [ ] **Step 2: Update all four theme definitions to include new spacing fields**

Edit each theme's `spacing` dict. For `modern_blue`:

```python
        spacing={
            "slidePaddingPx": 56, "gapPx": 18,
            "titleBodyRatio": 1.618, "accentBarWidth": 4,
            "cardRadius": 12, "cardShadow": "0 2px 12px rgba(255,255,255,0.06)",
        },
```

For `paper_light`:

```python
        spacing={
            "slidePaddingPx": 56, "gapPx": 18,
            "titleBodyRatio": 1.618, "accentBarWidth": 4,
            "cardRadius": 12, "cardShadow": "0 2px 12px rgba(0,0,0,0.08)",
        },
```

For `academic_gray`:

```python
        spacing={
            "slidePaddingPx": 64, "gapPx": 16,
            "titleBodyRatio": 1.618, "accentBarWidth": 3,
            "cardRadius": 8, "cardShadow": "0 1px 6px rgba(0,0,0,0.06)",
        },
```

For `minimal_black`:

```python
        spacing={
            "slidePaddingPx": 60, "gapPx": 20,
            "titleBodyRatio": 1.618, "accentBarWidth": 4,
            "cardRadius": 16, "cardShadow": "0 2px 16px rgba(255,255,255,0.04)",
        },
```

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/domain/theme.py
git commit -m "feat: extend ThemeSpacing with layout tokens (titleBodyRatio, accentBarWidth, cardRadius, cardShadow)"
```

---

### Task 2.2: Backend — Create smart layout selector

**Files:**
- Create: `backend/ppt_backend/services/rendering/layout_selector.py`

- [ ] **Step 1: Create layout_selector.py**

Create the file `backend/ppt_backend/services/rendering/layout_selector.py`:

```python
from __future__ import annotations

from typing import Optional

from .planning import LayoutId


def select_layout(
    intent: str,
    content_count: int = 0,
    has_image: bool = False,
    item_count: int = 0,
    step_count: int = 0,
    column_count: int = 0,
) -> LayoutId:
    """Deterministic layout selection based on content characteristics.

    Args:
        intent: Slide intent (cover, text, kpi, comparison, etc.)
        content_count: Total number of content elements
        has_image: Whether slide has an associated image
        item_count: For KPI/agenda slides, number of items
        step_count: For process flows, number of steps
        column_count: For multi-column slides, number of columns
    """
    # Cover: use magazine_hero for rich covers
    if intent == "cover":
        if has_image or content_count >= 6:
            return "magazine_hero"
        return "cover"

    # Agenda
    if intent == "agenda":
        return "title_body"

    # Text: use asymmetric_split when image is available
    if intent == "text":
        if has_image:
            return "asymmetric_split"
        return "title_body"

    # Timeline
    if intent == "timeline":
        return "timeline"

    # KPI: big_number_grid for 4+ items
    if intent == "kpi":
        if item_count >= 4:
            return "big_number_grid"
        return "title_body"

    # Comparison: asymmetric_split when image available
    if intent == "comparison":
        if has_image:
            return "asymmetric_split"
        return "two_column"

    # SWOT: bento_grid for richer layout
    if intent == "swot":
        return "bento_grid"

    # Roadmap
    if intent == "roadmap":
        return "roadmap"

    # Process flow: step_numbered for ≤6 steps, else title_body
    if intent == "process_flow":
        if step_count <= 6:
            return "step_numbered"
        return "process_flow"

    # Chart
    if intent == "chart":
        return "chart"

    # Multi-column: card_masonry for 3 columns, else two_column
    if intent == "multi_column":
        if column_count == 3:
            return "card_masonry"
        return "two_column"

    # Architecture
    if intent == "architecture":
        return "title_body"

    # Quote: quote_centered for modern look
    if intent == "quote":
        return "quote_centered"

    # Divider: gradient_overlay
    if intent == "divider":
        return "gradient_overlay"

    # Team: card_masonry for 3 members
    if intent == "team":
        if item_count == 3:
            return "card_masonry"
        return "title_body"

    # Default fallback
    return "title_body"
```

- [ ] **Step 2: Commit**

```bash
git add backend/ppt_backend/services/rendering/layout_selector.py
git commit -m "feat: add smart deterministic layout selector"
```

---

### Task 2.3: Backend — Add 9 new layout classes

**Files:**
- Modify: `backend/ppt_backend/services/rendering/layout.py`

- [ ] **Step 1: Add golden-ratio helper and update imports**

Edit `backend/ppt_backend/services/rendering/layout.py`. At the top, after the imports, add:

```python
def _title_height(slide_h: int, padding_px: int, ratio: float = 1.618) -> float:
    """Title area height based on golden ratio."""
    available = slide_h - 2 * padding_px
    return available / (1 + ratio)
```

- [ ] **Step 2: Add `MagazineHeroLayout`**

Add after the existing `CoverLayout` class:

```python
class MagazineHeroLayout:
    layout_id: LayoutId = "magazine_hero"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        ch = h - 2 * padding_px
        left_w = cw * 0.38
        right_w = cw * 0.62 - gap_px
        title_h = 120
        subtitle_h = 70
        tagline_h = 60
        highlights_y = y0 + title_h + subtitle_h + tagline_h + 3 * gap_px
        highlights_h = max(120, h - highlights_y - padding_px)
        return {
            "title": Rect(x0, y0, left_w, title_h),
            "subtitle": Rect(x0, y0 + title_h + gap_px, left_w, subtitle_h),
            "tagline": Rect(x0, y0 + title_h + subtitle_h + 2 * gap_px, left_w, tagline_h),
            "highlights": Rect(x0, highlights_y, left_w, highlights_h),
            "visual": Rect(x0 + left_w + gap_px, y0, right_w, ch),
            "body": Rect(x0, y0, cw, ch),
        }
```

- [ ] **Step 3: Add `BigNumberGridLayout`**

```python
class BigNumberGridLayout:
    layout_id: LayoutId = "big_number_grid"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        ch = h - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        cell_w = (cw - gap_px) / 2
        cell_h = (body_h - gap_px) / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "cell_1": Rect(x0, body_y, cell_w, cell_h),
            "cell_2": Rect(x0 + cell_w + gap_px, body_y, cell_w, cell_h),
            "cell_3": Rect(x0, body_y + cell_h + gap_px, cell_w, cell_h),
            "cell_4": Rect(x0 + cell_w + gap_px, body_y + cell_h + gap_px, cell_w, cell_h),
            "body": Rect(x0, body_y, cw, body_h),
        }
```

- [ ] **Step 4: Add `AsymmetricSplitLayout`**

```python
class AsymmetricSplitLayout:
    layout_id: LayoutId = "asymmetric_split"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        ch = h - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        left_w = cw * 0.62 - gap_px / 2
        right_w = cw * 0.38 - gap_px / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "left": Rect(x0, body_y, left_w, body_h),
            "right": Rect(x0 + left_w + gap_px, body_y, right_w, body_h),
            "body": Rect(x0, body_y, cw, body_h),
        }
```

- [ ] **Step 5: Add `CardMasonryLayout`**

```python
class CardMasonryLayout:
    layout_id: LayoutId = "card_masonry"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        cell_w = (cw - gap_px) / 2
        cell_h = (body_h - gap_px) / 2
        bottom_w = cw * 0.5
        bottom_x = x0 + (cw - bottom_w) / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "cell_1": Rect(x0, body_y, cell_w, cell_h),
            "cell_2": Rect(x0 + cell_w + gap_px, body_y, cell_w, cell_h),
            "cell_3": Rect(bottom_x, body_y + cell_h + gap_px, bottom_w, cell_h),
            "body": Rect(x0, body_y, cw, body_h),
        }
```

- [ ] **Step 6: Add `StepNumberedLayout`**

```python
class StepNumberedLayout:
    layout_id: LayoutId = "step_numbered"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        return {
            "title": Rect(x0, y0, cw, title_h),
            "body": Rect(x0, body_y, cw, body_h),
        }
```

- [ ] **Step 7: Add `QuoteCenteredLayout`**

```python
class QuoteCenteredLayout:
    layout_id: LayoutId = "quote_centered"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        margin_x = w * 0.15
        margin_y = h * 0.2
        body_w = w - 2 * margin_x
        body_h = h - 2 * margin_y
        return {
            "body": Rect(margin_x, margin_y, body_w, body_h),
        }
```

- [ ] **Step 8: Add `BentoGridLayout`**

```python
class BentoGridLayout:
    layout_id: LayoutId = "bento_grid"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        col_w = (cw - gap_px) / 2
        # Tall cell on left, two stacked on right
        return {
            "title": Rect(x0, y0, cw, title_h),
            "cell_1": Rect(x0, body_y, col_w, body_h),                         # tall left
            "cell_2": Rect(x0 + col_w + gap_px, body_y, col_w, (body_h - gap_px) / 2),    # top right
            "cell_3": Rect(x0 + col_w + gap_px, body_y + (body_h - gap_px) / 2 + gap_px, col_w, (body_h - gap_px) / 2),  # bottom right
            "body": Rect(x0, body_y, cw, body_h),
        }
```

- [ ] **Step 9: Add `GradientOverlayLayout`**

```python
class GradientOverlayLayout:
    layout_id: LayoutId = "gradient_overlay"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = h * 0.3
        cw = w - 2 * padding_px
        body_h = h * 0.4
        return {
            "title": Rect(x0, y0 - 60, cw, 50),
            "subtitle": Rect(x0, y0 + body_h - 50, cw, 40),
            "body": Rect(x0, y0, cw, body_h),
        }
```

- [ ] **Step 10: Add `ImageHeroLayout`** (for image-background slides)

```python
class ImageHeroLayout:
    layout_id: LayoutId = "image_hero"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        cw = w - 2 * padding_px
        title_y = h * 0.55
        title_h = 80
        subtitle_y = title_y + title_h + gap_px
        subtitle_h = 50
        return {
            "title": Rect(x0, title_y, cw, title_h),
            "subtitle": Rect(x0, subtitle_y, cw, subtitle_h),
            "body": Rect(x0, padding_px, cw, h - 2 * padding_px),
        }
```

- [ ] **Step 11: Add `TextImageSplitLayout`**

```python
class TextImageSplitLayout:
    layout_id: LayoutId = "text_image_split"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        text_w = cw * 0.55 - gap_px / 2
        image_w = cw * 0.45 - gap_px / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "text": Rect(x0, body_y, text_w, body_h),
            "image": Rect(x0 + text_w + gap_px, body_y, image_w, body_h),
            "body": Rect(x0, body_y, cw, body_h),
        }
```

- [ ] **Step 12: Commit**

```bash
git add backend/ppt_backend/services/rendering/layout.py
git commit -m "feat: add 9 new layout classes (magazine_hero, big_number_grid, asymmetric_split, card_masonry, step_numbered, quote_centered, bento_grid, gradient_overlay, image_hero, text_image_split)"
```

---

### Task 2.4: Backend — Register new layouts and update LayoutId type

**Files:**
- Modify: `backend/ppt_backend/services/rendering/planning.py:26-36`
- Modify: `backend/ppt_backend/services/rendering/registry.py` (or wherever layouts are registered)
- Modify: `backend/ppt_backend/container.py`

- [ ] **Step 1: Update `LayoutId` type in planning.py**

Edit `backend/ppt_backend/services/rendering/planning.py`. Replace the `LayoutId` type definition:

```python
LayoutId = Literal[
    "cover",
    "title_body",
    "two_column",
    "grid_2x2",
    "timeline",
    "roadmap",
    "process_flow",
    "chart",
    "divider",
    "magazine_hero",
    "big_number_grid",
    "asymmetric_split",
    "card_masonry",
    "step_numbered",
    "quote_centered",
    "bento_grid",
    "gradient_overlay",
    "image_hero",
    "text_image_split",
]
```

- [ ] **Step 2: Register new layout classes in `registry.py`**

Edit `backend/ppt_backend/services/rendering/registry.py`. Update the imports and `build_layout_registry()` function:

```python
from .layout import (
    ChartLayout,
    CoverLayout,
    DividerLayout,
    Grid2x2Layout,
    ProcessFlowLayout,
    RoadmapLayout,
    TimelineLayout,
    TitleBodyLayout,
    TwoColumnLayout,
    MagazineHeroLayout,
    BigNumberGridLayout,
    AsymmetricSplitLayout,
    CardMasonryLayout,
    StepNumberedLayout,
    QuoteCenteredLayout,
    BentoGridLayout,
    GradientOverlayLayout,
    ImageHeroLayout,
    TextImageSplitLayout,
)


def build_layout_registry():
    reg = Registry()
    for layout in [
        CoverLayout(),
        TitleBodyLayout(),
        TwoColumnLayout(),
        Grid2x2Layout(),
        TimelineLayout(),
        RoadmapLayout(),
        ProcessFlowLayout(),
        ChartLayout(),
        DividerLayout(),
        MagazineHeroLayout(),
        BigNumberGridLayout(),
        AsymmetricSplitLayout(),
        CardMasonryLayout(),
        StepNumberedLayout(),
        QuoteCenteredLayout(),
        BentoGridLayout(),
        GradientOverlayLayout(),
        ImageHeroLayout(),
        TextImageSplitLayout(),
    ]:
        reg.register(layout.layout_id, layout)
    return reg
```

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/services/rendering/planning.py backend/ppt_backend/services/rendering/registry.py
git commit -m "feat: register all new layout classes and update LayoutId type"
```

---

### Task 2.5: Backend — Update Compiler to use layout selector and image map

**Files:**
- Modify: `backend/ppt_backend/services/rendering/compiler.py`

- [ ] **Step 1: Update `compile()` signature to accept `rag_images`**

Edit `backend/ppt_backend/services/rendering/compiler.py`. Replace the `compile` method:

```python
from .layout_selector import select_layout
from .planning import SlidePlan


class RenderCompiler:
    def __init__(
        self,
        slide_composers: Registry[SlideComposer],
        layouts: Registry,
        slide_size: Tuple[int, int] = (1280, 720),
    ):
        self._slide_composers = slide_composers
        self._layouts = layouts
        self._slide_size = slide_size

    def compile(
        self,
        presentation_id: str,
        dsl: PresentationDSL,
        theme_tokens: ThemeTokens,
        rag_images: list = None,
    ) -> RenderTree:
        slides_out = []
        padding = theme_tokens.spacing.slide_padding_px
        gap = theme_tokens.spacing.gap_px

        # Build image lookup: slide_id -> [image_urls]
        image_map: dict = {}
        if rag_images:
            # Assign images to slides that have image_query set
            for slide in dsl.slides:
                image_query = getattr(slide, "image_query", None)
                if image_query and rag_images:
                    # Pick first matching image
                    for img in rag_images:
                        alt = img.get("alt") or img.get("title") or ""
                        url = img.get("url", "")
                        if url:
                            if image_map.get(slide.id) is None:
                                image_map[slide.id] = []
                            image_map[slide.id].append(img)
                            break

        for slide in dsl.slides:
            composer = self._slide_composers.get(slide.intent)
            plan: SlidePlan = composer.compose(slide)

            # Apply layout selector to override layout_id
            has_image = slide.id in image_map
            item_count = 0
            step_count = 0
            column_count = 0

            if slide.intent in ("kpi", "agenda", "team"):
                items = getattr(slide, "items", None) or getattr(slide, "members", None)
                item_count = len(items) if items else 0
            if slide.intent == "process_flow":
                steps = getattr(slide, "steps", None)
                step_count = len(steps) if steps else 0
            if slide.intent == "multi_column":
                cols = getattr(slide, "columns", None)
                column_count = len(cols) if cols else 0

            content_count = len(plan.components)

            selected_layout_id = select_layout(
                intent=slide.intent,
                content_count=content_count,
                has_image=has_image,
                item_count=item_count,
                step_count=step_count,
                column_count=column_count,
            )

            # Fall back to plan's layout_id if selector returns one not registered
            layout = self._layouts.get(selected_layout_id)
            if layout is None:
                layout = self._layouts.get(plan.layout_id)

            comps = layout_components(layout, plan.components, self._slide_size, padding, gap)

            # Set slide background image if available
            background = None
            background_image = None
            if has_image:
                img = image_map[slide.id][0]
                if selected_layout_id in ("image_hero", "gradient_overlay", "cover", "magazine_hero"):
                    background_image = img.get("url")
                else:
                    background = None  # keep transparent

            render_slide = RenderSlide(
                id=plan.slide_id,
                width=self._slide_size[0],
                height=self._slide_size[1],
                background=background,
                backgroundImage=background_image,
                components=comps,
                notes=plan.notes,
            )
            render_slide = apply_theme_to_slide(render_slide, theme_tokens)
            slides_out.append(render_slide)

        return RenderTree(
            presentationId=presentation_id,
            title=dsl.title,
            themeName=dsl.theme,
            themeTokens=theme_tokens,
            slides=slides_out,
            meta={
                "audience": dsl.audience,
                "tone": dsl.tone,
                "images": {sid: [img["url"] for img in imgs] for sid, imgs in image_map.items()},
            },
        )
```

- [ ] **Step 2: Commit**

```bash
git add backend/ppt_backend/services/rendering/compiler.py
git commit -m "feat: integrate layout selector and image map into compiler"
```

---

### Task 2.6: Frontend — Update EditorView with modern visual styles

**Files:**
- Modify: `slideon-frontend/src/views/EditorView.vue`

- [ ] **Step 1: Add accent bar support to components**

In `getComponentStyle`, add accent bar detection. After the existing style application (around line 441), add:

```javascript
  // Accent bar for title components in modern layouts
  if (component.style) {
    if (component.style.accentBar) {
      style.borderLeft = `${component.style.accentBarWidth || 4}px solid ${component.style.accentBarColor || '#3B82F6'}`
      style.paddingLeft = `${(component.style.accentBarWidth || 4) + 16}px`
    }
  }
```

- [ ] **Step 2: Update component CSS — add card shadows and rounded corners**

Replace the `.component-bullet-list` style to add card support:

```css
.slide-component {
  box-sizing: border-box;
  overflow: hidden;
}

.slide-component.card-style {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  padding: 20px;
}
```

- [ ] **Step 3: Add step-numbered styling for process flow**

Replace the `.step-number` style:

```css
.step-number {
  width: 48px;
  height: 48px;
  background: transparent;
  color: #3b82f6;
  border: 3px solid #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
}
```

- [ ] **Step 4: Add gradient overlay styles**

Add new styles for divider in gradient mode:

```css
.component-divider.gradient-style {
  background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15));
}

.divider-container .divider-accent {
  width: 80px;
  height: 4px;
  background: #3b82f6;
  border-radius: 2px;
  margin: 16px auto;
}
```

- [ ] **Step 5: Add quote-centered large quote mark style**

Add new style:

```css
.component-quote.centered-style {
  text-align: center;
  justify-content: center;
  align-items: center;
}

.component-quote.centered-style blockquote {
  font-size: 1.6em;
  line-height: 1.6;
  font-weight: 500;
  padding: 0 40px;
}

.component-quote.centered-style blockquote::before {
  content: '"';
  font-size: 8em;
  opacity: 0.08;
  position: absolute;
  left: 50%;
  top: -60px;
  transform: translateX(-50%);
  font-family: serif;
  color: #3b82f6;
}
```

- [ ] **Step 6: Commit**

```bash
git add slideon-frontend/src/views/EditorView.vue
git commit -m "feat: add modern visual styles to EditorView (accent bars, cards, gradient overlays, step numbers, centered quotes)"
```

---

## Milestone 3: Image Support

### Task 3.1: Backend — Add `image_query` to DSL base slide model

**Files:**
- Modify: `backend/ppt_backend/domain/dsl.py:93-102`

- [ ] **Step 1: Add `image_query` to `BaseSlideDSL`**

Edit `backend/ppt_backend/domain/dsl.py`. Replace the `BaseSlideDSL` class:

```python
class BaseSlideDSL(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    intent: str
    section: str = ""
    title: str
    notes: List[str] = Field(default_factory=list)
    image_query: Optional[str] = None
```

- [ ] **Step 2: Update `_repair_slide_dict` in pipeline.py to preserve `image_query`**

Edit `backend/ppt_backend/services/ai/pipeline.py`. In the `_repair_slide_dict` method (around line 297), add `image_query` preservation. After `title = s.get("title") or wrapper.get("title") or topic`, add:

```python
        image_query = s.get("image_query") if s.get("image_query") is not None else wrapper.get("image_query")
```

And include it in `base` dict:

```python
        base = {
            "id": as_str(slide_id) or new_id("slide"),
            "intent": intent if intent in allowed_intents else "text",
            "section": as_str(section),
            "title": as_str(title) or topic,
            "notes": as_str_list(notes_raw),
            "image_query": image_query if isinstance(image_query, str) and image_query.strip() else None,
        }
```

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/domain/dsl.py backend/ppt_backend/services/ai/pipeline.py
git commit -m "feat: add image_query field to BaseSlideDSL for AI-driven image assignment"
```

---

### Task 3.2: Backend — Add `backgroundImage` to RenderSlide

**Files:**
- Modify: `backend/ppt_backend/domain/render_tree.py:72-80`

- [ ] **Step 1: Add `background_image` field to `RenderSlide`**

Edit `backend/ppt_backend/domain/render_tree.py`. Replace the `RenderSlide` class:

```python
class RenderSlide(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    width: int = 1280
    height: int = 720
    background: Optional[str] = None
    background_image: Optional[str] = Field(default=None, alias="backgroundImage")
    components: List[ComponentSpec] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
```

- [ ] **Step 2: Commit**

```bash
git add backend/ppt_backend/domain/render_tree.py
git commit -m "feat: add backgroundImage field to RenderSlide"
```

---

### Task 3.3: Backend — Update composers for image-aware layout

**Files:**
- Modify: `backend/ppt_backend/services/rendering/planning.py`

- [ ] **Step 1: Update `CoverComposer` to handle image_query**

Edit `backend/ppt_backend/services/rendering/planning.py`. In `CoverComposer.compose()`, after the highlights block, add an Image component if `image_query` is set:

```python
class CoverComposer:
    intent = "cover"

    def compose(self, slide: CoverSlideDSL) -> SlidePlan:
        comps: List[ComponentBlueprint] = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            )
        ]
        if slide.subtitle:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__subtitle",
                    type="Subtitle",
                    props={"text": slide.subtitle},
                    slot="subtitle",
                    z=10,
                )
            )
        if slide.tagline:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__tagline",
                    type="Text",
                    props={"text": slide.tagline},
                    slot="tagline",
                    z=10,
                )
            )
        if slide.highlights:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__highlights",
                    type="BulletList",
                    props={"items": slide.highlights},
                    slot="highlights",
                    z=10,
                )
            )
        if slide.image_query:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__image",
                    type="Image",
                    props={"query": slide.image_query, "alt": slide.title, "fit": "cover"},
                    slot="visual",
                    z=5,
                )
            )
        return SlidePlan(
            slide_id=slide.id,
            layout_id="cover",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )
```

- [ ] **Step 2: Update `TextComposer` to optionally split with image**

Edit `TextComposer.compose()`:

```python
class TextComposer:
    intent = "text"

    def compose(self, slide: TextSlideDSL) -> SlidePlan:
        body_parts: List[str] = []
        body_parts.extend(slide.paragraphs)
        if slide.bullets:
            body_parts.append("")
            body_parts.extend([f"• {b}" for b in slide.bullets])
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__text",
                type="Text",
                props={"text": "\n".join([p for p in body_parts if p is not None])},
                slot="text" if slide.image_query else "body",
                z=10,
            ),
        ]
        if slide.image_query:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__image",
                    type="Image",
                    props={"query": slide.image_query, "alt": slide.title, "fit": "contain"},
                    slot="image",
                    z=5,
                )
            )
        return SlidePlan(
            slide_id=slide.id,
            layout_id="text_image_split" if slide.image_query else "title_body",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )
```

- [ ] **Step 3: Update `DividerComposer` for gradient/image overlay**

```python
class DividerComposer:
    intent = "divider"

    def compose(self, slide: DividerSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__divider",
                type="Divider",
                props={"title": slide.title, "subtitle": slide.subtitle},
                slot="body",
                z=10,
            )
        ]
        if slide.image_query:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__bg_image",
                    type="Image",
                    props={"query": slide.image_query, "alt": slide.title, "fit": "cover"},
                    slot="body",
                    z=1,
                )
            )
        return SlidePlan(
            slide_id=slide.id,
            layout_id="gradient_overlay",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )
```

- [ ] **Step 4: Commit**

```bash
git add backend/ppt_backend/services/rendering/planning.py
git commit -m "feat: update composers for image-aware layout (cover, text, divider)"
```

---

### Task 3.4: Frontend — Add Image component rendering in EditorView

**Files:**
- Modify: `slideon-frontend/src/views/EditorView.vue`

- [ ] **Step 1: Add Image component template**

In the template, add after the `Divider` component block (after line 324, before the `<!-- 其他组件 -->` fallback):

```html
                  <!-- Image组件 -->
                  <div v-else-if="component.type === 'Image'" class="component-image" :style="getComponentStyle(component)">
                    <img
                      v-if="component.props?.url"
                      :src="component.props.url"
                      :alt="component.props?.alt || ''"
                      :style="{ objectFit: component.props?.fit || 'cover', width: '100%', height: '100%' }"
                      @error="onImageError($event, component)"
                      @load="onImageLoad($event, component)"
                    />
                    <div v-else class="image-placeholder">
                      <div class="image-placeholder-shimmer"></div>
                      <IconBase name="images" :size="32" />
                      <span>{{ component.props?.alt || '图片加载中...' }}</span>
                    </div>
                  </div>
```

- [ ] **Step 2: Add slide background image support in `getCanvasStyle`**

Edit `getCanvasStyle`:

```javascript
const getCanvasStyle = () => {
  const slide = currentSlide.value
  const style = {
    width: (slide.width || 1280) + 'px',
    height: (slide.height || 720) + 'px',
    background: slide.background || '#ffffff'
  }
  if (slide.backgroundImage) {
    style.backgroundImage = `url(${slide.backgroundImage})`
    style.backgroundSize = 'cover'
    style.backgroundPosition = 'center'
  }
  return style
}
```

- [ ] **Step 3: Add `onImageError` and `onImageLoad` handlers**

Add to the `<script setup>`:

```javascript
const onImageError = (event, component) => {
  event.target.style.display = 'none'
  // Show placeholder
  const parent = event.target.parentElement
  if (parent) {
    const placeholder = parent.querySelector('.image-placeholder')
    if (placeholder) placeholder.style.display = 'flex'
  }
}

const onImageLoad = (event, component) => {
  event.target.style.opacity = '1'
}
```

- [ ] **Step 4: Update `generateFromRenderTree` to pass backgroundImage**

In `generateFromRenderTree`, update the slide object to include `backgroundImage`:

```javascript
      newSlides.push({
        number: slideNum,
        title: slideTitle,
        components: slide.components || [],
        background: slide.background || '#ffffff',
        backgroundImage: slide.backgroundImage || null,
        width: slide.width || 1280,
        height: slide.height || 720
      })
```

- [ ] **Step 5: Add CSS styles for Image component**

Add below the existing component styles:

```css
/* Image组件 */
.component-image {
  overflow: hidden;
  background: #f3f4f6;
}

.component-image img {
  transition: opacity 0.3s ease;
  opacity: 0;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #9ca3af;
  font-size: 13px;
  position: relative;
}

.image-placeholder-shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255,255,255,0.4) 50%,
    transparent 100%
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

- [ ] **Step 6: Commit**

```bash
git add slideon-frontend/src/views/EditorView.vue
git commit -m "feat: add Image component rendering and slide background image support to EditorView"
```

---

### Task 3.5: Frontend — Add gradient overlay for slides with background images

**Files:**
- Modify: `slideon-frontend/src/views/EditorView.vue`

- [ ] **Step 1: Add gradient overlay div in template for slides with background images**

In the template, inside `.slide-canvas`, before `.slide-content`, add:

```html
          <div class="slide-canvas" :style="getCanvasStyle()">
            <div v-if="currentSlide.backgroundImage" class="slide-gradient-overlay"></div>
            <div class="slide-content" :style="{ transform: `scale(${zoom / 100})`, transformOrigin: 'center center' }">
```

- [ ] **Step 2: Add CSS for gradient overlay**

```css
.slide-gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(0,0,0,0.35) 0%,
    rgba(0,0,0,0.1) 50%,
    rgba(0,0,0,0.35) 100%
  );
  z-index: 1;
  pointer-events: none;
}
```

- [ ] **Step 3: Commit**

```bash
git add slideon-frontend/src/views/EditorView.vue
git commit -m "feat: add gradient overlay for slides with background images"
```

---

## Final Verification

### Task V.1: End-to-end verification

- [ ] **Step 1: Verify backend starts correctly**

```bash
cd backend && python -c "from ppt_backend.services.rendering.layout_selector import select_layout; print(select_layout('kpi', item_count=4))"
```
Expected output: `big_number_grid`

- [ ] **Step 2: Verify all layouts produce valid rects**

```bash
cd backend && python -c "
from ppt_backend.services.rendering.layout import (
    MagazineHeroLayout, BigNumberGridLayout, AsymmetricSplitLayout,
    CardMasonryLayout, StepNumberedLayout, QuoteCenteredLayout,
    BentoGridLayout, GradientOverlayLayout, ImageHeroLayout, TextImageSplitLayout
)
for L in [MagazineHeroLayout, BigNumberGridLayout, AsymmetricSplitLayout,
           CardMasonryLayout, StepNumberedLayout, QuoteCenteredLayout,
           BentoGridLayout, GradientOverlayLayout, ImageHeroLayout, TextImageSplitLayout]:
    slots = L().slot_rects((1280, 720), 64, 24)
    for name, rect in slots.items():
        assert 0 <= rect.x < 1280, f'{L.__name__} {name} x out of bounds: {rect.x}'
        assert 0 <= rect.y < 720, f'{L.__name__} {name} y out of bounds: {rect.y}'
        assert rect.w > 0, f'{L.__name__} {name} w <= 0'
        assert rect.h > 0, f'{L.__name__} {name} h <= 0'
    print(f'{L.__name__}: OK ({len(slots)} slots)')
print('All layouts valid!')
```

- [ ] **Step 3: Verify frontend builds**

```bash
cd slideon-frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 4: Commit any final fixes**

```bash
git add -A
git commit -m "chore: final verification and cleanup"
```
