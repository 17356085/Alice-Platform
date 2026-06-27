# Alice (有珠) — Visual Design Specification

> 月下魔女 · Midnight Iris & Classical Gold · Restrained Elegance
> 项目名 "Alice / 有珠" 取自《魔法使之夜》角色久远寺有珠
> 版本 v1.0 | 2026-06-26

---

## 0. 设计理念

> "月が綺麗ですね。"

久远寺有珠 — 静谧、优雅、神秘。她的魔法在月下展开，影子是她的使魔，古旧宅邸是她的居所。

Alice 平台的视觉语言由此提炼：

| 意象 | 设计映射 |
|------|----------|
| **月** | 暗黑模式 OLED 深夜底 + 柔光阴影，模拟月光 |
| **影** | 多层阴影系统 + 紫调 glow，使魔般的暗影层次 |
| **古宅** | 暖羊皮纸浅底、古典衬线标题、克制圆角 |
| **魔法阵** | 几何精确（8px grid）、金色点缀、紫→金渐变 |
| **静** | 低对比度 muted 色调、大留白、15px base font |

**设计原则：**
1. **沉静优先** — 低饱和度、低对比度，不抢夺用户注意力
2. **精确克制** — 少即是多，每处样式有理由
3. **暗底为尊** — 暗黑模式是 first-class，非浅色翻版
4. **触感细腻** — 玻璃态、微阴影、微交互反馈

---

## 1. 色彩系统

### 1.1 主色板 — Midnight Iris

shadcn/ui 标准 HSL 格式（`<hue> <sat>% <light>%`），无 `hsl()` 包裹。

```
--primary:     257 73% 61%    #7360E8  鸢尾紫
--primary-foreground: 0 0% 100%        白色文字
```

**暗黑模式:**
```
--primary:     257 78% 71%    #8F7EF0  月下紫（更亮）  
--primary-foreground: 250 40% 8%       #0E0B1A 深夜底文字
```

### 1.2 辅色板

| Token | Light (HSL) | Dark (HSL) | 用途 |
|-------|-------------|------------|------|
| `--secondary` | `250 20% 96%` | `250 20% 12%` | 次级容器 |
| `--secondary-foreground` | `250 30% 15%` | `250 15% 90%` | 次级文字 |

### 1.3 金色点缀

```
--gold:        43 53% 56%     #C9A94F  古典金
--gold-foreground: 0 0% 100%
--gold-light:   43 53% 92%    #F7EFD6  金底色
```

**用途:** 强调链接、选中态边框、徽章、魔法阵装饰、hover 高亮

### 1.4 表面色 — Parchment / Midnight

| Token | Light | Dark | 意象 |
|-------|-------|------|------|
| `--background` | `40 25% 97%` (#F7F3EE 羊皮纸) | `250 25% 5%` (#080812 深夜) | 页面底 |
| `--foreground` | `250 25% 15%` | `250 15% 88%` | 正文 |
| `--card` | `0 0% 100% / 0.85` | `250 25% 8% / 0.85` | 卡片玻璃态 |
| `--card-foreground` | `250 25% 15%` | `250 15% 88%` | 卡片文字 |
| `--border` | `250 15% 88%` | `250 15% 14%` | 边框 |
| `--input` | `250 15% 85%` | `250 15% 16%` | 输入框 |
| `--ring` | `257 73% 61%` | `257 78% 71%` | 聚焦环 |
| `--muted` | `250 15% 94%` | `250 15% 10%` | 弱化底 |
| `--muted-foreground` | `250 10% 45%` | `250 10% 55%` | 弱化文字 |
| `--accent` | `257 30% 94%` | `257 25% 14%` | 强调底 |
| `--accent-foreground` | `257 73% 61%` | `257 78% 71%` | 强调文字 |

### 1.5 语义色

| Token | Light | Dark |
|-------|-------|------|
| `--success` | `158 60% 42%` | `158 55% 52%` |
| `--success-light` | `158 60% 92%` | `158 40% 10%` |
| `--warning` | `38 90% 50%` | `45 85% 55%` |
| `--warning-light` | `38 90% 92%` | `38 40% 10%` |
| `--destructive` | `0 75% 55%` | `0 70% 60%` |
| `--destructive-light` | `0 75% 93%` | `0 40% 10%` |
| `--info` | `217 70% 55%` | `217 65% 60%` |
| `--info-light` | `217 70% 92%` | `217 40% 10%` |

所有 `*-foreground` 在 light 为 `#ffffff`，dark 继承或略调暗。

### 1.6 渐变

```
--primary-gradient:  linear-gradient(135deg, hsl(257 73% 61%) 0%, hsl(280 60% 55%) 100%)
  /* dark: linear-gradient(135deg, hsl(257 78% 71%) 0%, hsl(280 65% 65%) 100%) */
--gold-gradient:     linear-gradient(135deg, hsl(43 53% 56%) 0%, hsl(35 65% 50%) 100%)
```

---

## 2. 排版

### 2.1 字体栈

| 角色 | 字体 | 用途 |
|------|------|------|
| **标题** | `'Lora', 'Noto Serif SC', serif` | h1-h4、品牌标记、引用 |
| **正文** | `'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif` | body、按钮、表单 |
| **等宽** | `'JetBrains Mono', 'Fira Code', monospace` | 代码、日志、终端 |

Lora 由 Google Fonts 加载（`@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap')`）。

### 2.2 字号阶梯（15px base）

| 级别 | 字号 | 行高 | 字重 | 用途 |
|------|------|------|------|------|
| `h1` | `2rem` (30px) | 1.25 | 700 (Lora) | 页面标题 |
| `h2` | `1.5rem` (22.5px) | 1.3 | 600 (Lora) | 区块标题 |
| `h3` | `1.15rem` (17.25px) | 1.4 | 600 | 卡片标题 |
| `h4` | `1rem` (15px) | 1.45 | 600 | 小节标题 |
| `body` | `0.933rem` (14px) | 1.55 | 400 | 正文 |
| `body-sm` | `0.8rem` (12px) | 1.5 | 400 | 辅助文字 |
| `caption` | `0.733rem` (11px) | 1.5 | 500 | 标签、badge、caption |
| `mono` | `0.8rem` (12px) | 1.6 | 400 | 代码/日志 |

### 2.3 字距

- 正文: `-0.01em`（轻微收紧，Inter 优化）
- 标题: `-0.015em`（衬线标题收紧）
- Badge/标签: `0.02em`（大写风格宽松）
- 等宽: `0`（保持对齐）

---

## 3. 间距与圆角

### 3.1 间距（8px 网格）

| Token | 值 | Tailwind |
|-------|-----|----------|
| `space-1` | 4px | `p-1`, `gap-1` |
| `space-2` | 8px | `p-2`, `gap-2` |
| `space-3` | 12px | `p-3`, `gap-3` |
| `space-4` | 16px | `p-4`, `gap-4` |
| `space-6` | 24px | `p-6`, `gap-6` |
| `space-8` | 32px | `p-8`, `gap-8` |

遵循 Tailwind 默认间距系统（4px 基础单位），无需自定义。

### 3.2 圆角

shadcn 统一 `--radius` token：

```
--radius: 0.625rem   10px  默认圆角（按钮、输入框、卡片）
```

Tailwind 映射：
- `rounded-sm` → `calc(var(--radius) - 0.25rem)` 约 6px
- `rounded-md` → `calc(var(--radius) - 0.125rem)` 约 8px
- `rounded-lg` → `var(--radius)` 10px
- `rounded-xl` → `calc(var(--radius) + 0.25rem)` 约 14px

原有 `--radius-sm/md/lg/xl/2xl/full` 废弃，统一由 shadcn `--radius` 管理。

---

## 4. 阴影与发光

### 4.1 层级阴影

| Token | Light (细微软阴影) | Dark (深暗阴影) |
|-------|---------------------|-------------------|
| `--shadow-xs` | `0 1px 2px rgba(0,0,0,0.04)` | `0 1px 2px rgba(0,0,0,0.3)` |
| `--shadow-sm` | `0 2px 4px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)` | `0 2px 4px rgba(0,0,0,0.5)` |
| `--shadow-md` | `0 4px 8px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.02)` | `0 4px 12px rgba(0,0,0,0.6)` |
| `--shadow-lg` | `0 8px 16px rgba(0,0,0,0.05), 0 4px 8px rgba(0,0,0,0.02)` | `0 8px 24px rgba(0,0,0,0.7)` |
| `--shadow-xl` | `0 12px 24px rgba(0,0,0,0.06), 0 6px 12px rgba(0,0,0,0.03)` | `0 12px 32px rgba(0,0,0,0.8)` |

### 4.2 品牌发光

```
--shadow-focus: 0 0 0 3px hsla(257 73% 61% / 0.25)
  /* dark: 0 0 0 3px hsla(257 78% 71% / 0.3) */

--shadow-glow:  0 0 30px hsla(257 73% 61% / 0.12)
  /* dark: 0 0 40px hsla(257 78% 71% / 0.10) */

--shadow-gold:  0 0 20px hsla(43 53% 56% / 0.15)
```

**使用规则:**
- `--shadow-focus`: 所有 focus-visible 状态
- `--shadow-glow`: 主按钮、选中的卡片、激活的导航项
- `--shadow-gold`: 金色徽章、荣誉标记、完成状态

---

## 5. 组件样式

### 5.1 shadcn/ui 基础组件

Alice 使用 shadcn/ui（Radix + Tailwind）作为基础组件层。以下组件按需引入 `src/components/ui/`：

| 组件 | 用途 | 自定义 |
|------|------|--------|
| `Button` | 主按钮(gradient)、ghost、outline、destructive | `variant="gradient"` 使用 `--primary-gradient` |
| `Card` | 内容卡片 | 默认 glass-card 风格 |
| `Input` | 表单输入 | 圆角 10px，focus ring 紫色 |
| `Select` | 下拉选择 | Popover 弹层 |
| `Checkbox` | 多选框 | 选中态紫色 |
| `Badge` | 状态标记 | 6 变体：default/secondary/success/warning/destructive/gold |
| `Popover` | 弹出面板 | 12px blur 玻璃态 |
| `Command` | 搜索式选择器 (cmdk) | 项目选择器核心 |
| `Sheet` | 侧滑面板 | 详情抽屉 |
| `Collapsible` | 折叠面板 | 侧边栏 submenu |
| `Separator` | 分隔线 | 细线，灰色 |
| `Progress` | 进度条 | gradient 填充 |
| `Sonner` | Toast 通知 | 右上角，紫色边框 |
| `ToggleGroup` | 切换按钮组 | 主题选择器 |

### 5.2 平台自定义组件

| 组件 | 样式原则 |
|------|----------|
| **Sidebar** | 左 232px，玻璃态，active 项紫色左边框 + 淡紫底 |
| **Kanban Board** | 列宽度 300px，卡片拖拽阴影用 glow，Phase 节点用金色 |
| **Terminal** | 深黑底 #080812，等宽字体，绿色光标 |
| **Timeline** | 竖线 timeline（shadcn 无此组件），节点用 success/destructive 圆点 |
| **Agent Graph** | SVG 自定义，紫色节点 + 金色连线 |

---

## 6. 图标

**库:** `lucide-react` (v0.441+)

| 尺寸 | 用途 |
|------|------|
| `size={14}` | Badge 内、行内图标 |
| `size={16}` | 按钮内、导航项 |
| `size={20}` | 卡片标题 |
| `size={24}` | 空状态大图标 |
| `size={32}` | 页面 hero 图标 |

**颜色:** 默认继承 `currentColor`，特殊状态使用 `text-primary`、`text-gold`、`text-muted-foreground`。

**描边:** 全部 `strokeWidth={2}`（lucide 默认），不使用填充图标。

---

## 7. 动效

### 7.1 过渡

```
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)  悬停、聚焦
--transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1)  开关、展开
--transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1)  页面切换、模态
```

### 7.2 微交互

| 场景 | 动效 |
|------|------|
| 按钮 hover | `translateY(-1px)` + shadow 加深 (150ms) |
| 按钮 active | `translateY(0)` + shadow 回弹 (100ms) |
| 卡片 hover | shadow md → lg (200ms) |
| 弹出层 (popover/sheet) | scale(0.95)→1 + opacity 0→1 (200ms) |
| 侧边栏折叠 | width 过渡 (200ms) |
| Toast 进出 | translateX + opacity (300ms, Sonner 默认) |
| 骨架屏 | 左右 shimmer (1.5s ease-in-out infinite) |
| Live dot | pulse scale (2s ease-in-out infinite) |

### 7.3 tailwindcss-animate

使用 `tailwindcss-animate` 插件提供标准动画 class：
- `animate-in fade-in slide-in-from-top` 等用于 shadcn 组件
- 自定义 `animate-glow-pulse` 用于品牌发光呼吸

---

## 8. 三主角主题

Alice、Aoko、Soujuurou — 三主角各一主题，浅/暗双模式。通过 `[data-theme="<name>"]` 选择器定义于 `themes/all.css`。

| Theme | 角色 | Light | Dark | 气质 |
|-------|------|-------|------|------|
| **default** (Alice) | 久远寺有珠 | 羊皮纸 `#F7F3EE` + 鸢尾紫 `#7360E8` | 月夜 `#0E0D1A` + 月下紫 `#8F7EF0` | 静 · 克制 · 知性 |
| **aoko** | 苍崎青子 | 晴空 `#F0F6FC` + 青空蓝 `#1E90FF` | 深蓝 `#0A1220` + 魔力青 `#40A0FF` | 明快 · 直率 · 动能 |
| **soujuurou** | 静希草十郎 | 木肌 `#F4F0EA` + 山林绿 `#4A7850` | 深林 `#0E1410` + 夜绿 `#60A868` | 素直 · 温厚 · 自然 |

全部变量名与 shadcn 标准对齐。

---

## 9. 暗黑模式

**策略:** `class` 模式（Tailwind `darkMode: 'class'`），`<html class="dark">` 触发。

**设计方向: 月下魔法书 (Moonlit Grimoire)** — 月明之夜，非纯黑。紫调底 + 可见卡片 + 柔光阴影。

| 特性 | 值 |
|------|-----|
| 底色 | `hsl(250 30% 8%)` (#0E0D1A) — 月下深夜，可见紫调 |
| 卡片 | `hsl(250 25% 11% / 0.9)` — 微高于底，玻璃态 |
| 文字 | `hsl(250 20% 85%)` — 柔白，非刺眼纯白 |
| 阴影 | 深投影 + 紫调 glow (`0 0 50px hsla(257 78% 71% / 0.12)`) |
| 边框 | `hsl(250 15% 18%)` — 可见分隔 |
| 强调 | 月下紫 `#8F7EF0` + 古典金 `#C9A94F` 在暗底发光 |
| 选择 | 紫底 + 暗文字 |

**切换:** 无闪烁。`<script>` 在 `<head>` 中内联执行，读取 `localStorage` 并在 paint 前设置 class。

---

## 10. 实施指南

### 颜色转换参考

| 旧色 (hex) | 新色 (HSL) | 变更 |
|------------|------------|------|
| `#5b7fff` (蓝) | `257 73% 61%` (#7360E8 鸢尾紫) | 品牌色蓝→紫 |
| `#f5f6fa` (灰白) | `40 25% 97%` (#F7F3EE 羊皮纸) | 冷灰→暖纸 |
| `#0b0b12` (灰黑) | `250 25% 5%` (#080812 深夜) | 灰黑→蓝调黑 |
| `#1a1a2e` (深蓝灰) | `250 25% 15%` | 保持蓝调，变暖 |

### 文件变更清单

1. `tokens.css` — 替换全部 `:root` / `.dark` 变量值
2. `tailwind.config.js` — 添加 `--radius: DEFAULT` + `tailwindcss-animate` 插件
3. `themes/all.css` — 更新 8 主题色值（可选，后续）
4. 组件迁移 — 按 Phase 1/2/3 渐进替换

### Lora 字体加载

在 `index.html` `<head>` 中添加：
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
```

或通过 `tokens.css` `@import`。

---

## 11. 人物主题体系 (Character Theme System)

三主角各对应一组设计基调，共享同一 CSS 变量 infrastructure，通过 `[data-theme]` 切换。

### 11.1 久远寺有珠 · Alice (当前)

| 维度 | Light | Dark |
|------|-------|------|
| **意象** | 古宅午后 · 羊皮纸 · 银茶器 | 月下庭园 · 使魔之影 · 紫光 |
| **Primary** | `257 73% 61%` 鸢尾紫 | `257 78% 71%` 月下紫 |
| **Background** | `40 25% 97%` 羊皮纸 | `250 30% 8%` 月夜 |
| **Accent** | `43 53% 56%` 古典金 | `43 53% 62%` 月光金 |
| **字体** | Lora 衬线标题 + Inter 正文 | 同上 |
| **气质** | 静 · 克制 · 古典 · 知性 | 神秘 · 优雅 · 冷艳 |
| **识别** | 紫金渐变按钮、衬线标题、玻璃态卡片 | 月下紫 glow、可见卡片层 |

**主题名**: `default` (Alice) — 当前 8 主题中的默认位置。

### 11.2 苍崎青子 · Aoko (计划 v1.2)

> "壊すのが得意なんだ、私は。" — 第五魔法继承者 · 破坏与创造

| 维度 | Light | Dark |
|------|-------|------|
| **意象** | 晴空下 · 校园 · 能量 | 青炎 · 流星 · 魔力爆发 |
| **Primary** | `210 85% 50%` 青空蓝 | `210 90% 60%` 魔力青 |
| **Background** | `210 20% 97%` 晴空白 | `215 30% 7%` 深蓝夜 |
| **Accent** | `25 90% 55%` 橙炎 | `25 95% 60%` 灼橙 |
| **字体** | 无衬线全用 Inter（直接、现代） | 同上 |
| **气质** | 明快 · 直率 · 力量 · 动能 | 炽热 · 决绝 · 破坏力 |
| **识别** | 蓝橙撞色、直角卡片、无衬线 | 青炎 glow、锐角阴影 |

### 11.3 静希草十郎 · Soujuurou (计划 v1.3)

> "山から降りてきただけなんだ。" — 山之子 · 素朴坚韧

| 维度 | Light | Dark |
|------|-------|------|
| **意象** | 山间 · 木造校舍 · 土 | 星夜 · 篝火 · 大地 |
| **Primary** | `140 40% 38%` 山林绿 | `140 35% 48%` 夜绿 |
| **Background** | `35 20% 94%` 木肌色 | `140 15% 6%` 深山林 |
| **Accent** | `30 35% 55%` 土棕 | `30 40% 60%` 篝火橙 |
| **字体** | 标题 Georgia（衬线但朴素），body Inter | 同上 |
| **气质** | 素直 · 温厚 · 自然 · 坚韧 | 静寂 · 大地 · 安心 |
| **识别** | 暖木色调、大圆角、无 glass | 篝火光晕、最大圆角 |

### 11.4 技术实现

三主角共用：
- 同一 CSS 变量名空间（shadcn 标准）
- 同一 Tailwind 配置
- 同一 14 个 shadcn 组件

仅 `tokens.css` 的 `:root` / `.dark` 值变化 + `themes/all.css` 主题块。切换 `data-theme` 属性即时生效。

未来考虑: 每个角色一个独立 `themes/<character>.css`，`SettingsView` 先选角色再选 light/dark。

---

> 月が導く。青が燃える。土が支える。三つの魔法、一つのプラットフォーム。
> — Alice Design System v1.1
