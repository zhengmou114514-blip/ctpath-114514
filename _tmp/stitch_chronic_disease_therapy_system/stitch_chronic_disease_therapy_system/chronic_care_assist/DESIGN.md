---
name: Chronic Care Assist
colors:
  surface: '#f7fafc'
  surface-dim: '#d7dadc'
  surface-bright: '#f7fafc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f4f6'
  surface-container: '#ebeef0'
  surface-container-high: '#e5e9eb'
  surface-container-highest: '#e0e3e5'
  on-surface: '#181c1e'
  on-surface-variant: '#3f4848'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eef1f3'
  outline: '#6f7978'
  outline-variant: '#bfc8c8'
  surface-tint: '#296767'
  primary: '#003434'
  on-primary: '#ffffff'
  primary-container: '#004d4d'
  on-primary-container: '#80bdbc'
  inverse-primary: '#94d1d1'
  secondary: '#0059bb'
  on-secondary: '#ffffff'
  secondary-container: '#0070ea'
  on-secondary-container: '#fefcff'
  tertiary: '#4c230b'
  on-tertiary: '#ffffff'
  tertiary-container: '#67381f'
  on-tertiary-container: '#e5a282'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b0eeed'
  primary-fixed-dim: '#94d1d1'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#044f4f'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc7ff'
  on-secondary-fixed: '#001a41'
  on-secondary-fixed-variant: '#004493'
  tertiary-fixed: '#ffdbcb'
  tertiary-fixed-dim: '#fcb795'
  on-tertiary-fixed: '#341100'
  on-tertiary-fixed-variant: '#6a3a21'
  background: '#f7fafc'
  on-background: '#181c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 40px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Public Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Public Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  data-mono:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  baseline: 4px
  gutter: 24px
  margin-page: 32px
  card-padding: 20px
  stack-sm: 8px
  stack-md: 16px
---

## 品牌与风格

本设计系统旨在为“慢性病辅疗系统”构建一个极其专业、严谨且具有医疗信任感的视觉环境。核心受众为医生、护理人员及医疗管理人员，因此系统强调极高的信息获取效率与心理安定感。

**视觉定位：现代医疗 (Corporate / Modern)**
设计风格融合了现代企业级软件的稳定感与医疗行业的洁净感。通过大面积的留白、深邃的蓝绿色调以及清晰的层级划分，消除医疗数据的冰冷感，转化为易于解读的临床洞察。我们采用卡片式布局作为核心容器，利用柔和的物理投影模拟纸质病历的层叠感，确保在复杂的数据环境下，用户依然能保持专注。

## 颜色

色彩方案以“治愈与信任”为核心。

- **主色 (#004D4D)**：深蓝绿色，代表深度、专业与医疗学术的严谨，用于导航、核心操作按钮及品牌标识。
- **背景色 (#F4F7F9)**：极淡的冷灰色，比纯白更具质感，能有效缓解长时间查看屏幕的视觉疲劳。
- **辅助色 (#007BFF)**：温和的蓝色，用于次要操作、链接或非紧急的状态提示。
- **状态语义色**：
  - **高风险 (Error)**：采用深红色，确保在大量数据中具有极强的视觉跳跃性。
  - **中风险 (Warning)**：温暖的琥珀色，用于提醒关注而非直接警示。
  - **稳定 (Success)**：宁静的森林绿，表示指标正常。

## 字体

为了确保医疗报表和患者数据的高可读性，本系统选用高度功能化的无衬线字体系统。

- **标题与标签 (Inter)**：利用其极高的字腔开阔度和数字化适配性，确保在各种尺寸下都具有优秀的辨识度。
- **正文与阅读 (Public Sans)**：这是一款专门为清晰度设计的政府/医疗级字体，字形规整，长文阅读不易疲劳。
- **数据呈现**：对于数值、指标等关键医疗数据，增加字重并微调字间距，确保医生在快速扫视时不会产生误读。
- **中文适配**：系统默认匹配用户环境下的高质量无衬线体（如 PingFang SC 或 Microsoft YaHei UI），并严格遵循 1.5 倍至 1.6 倍的行高规范。

## 布局与间距

本系统采用**固定网格与灵活内容区相结合**的布局策略。

- **网格系统**：标准的 12 列响应式网格，水槽 (Gutter) 固定为 24px，确保卡片之间有足够的呼吸感。
- **间距韵律**：基于 4px 的倍数原则。组件内部间距（如卡片内边距）统一为 20px 或 24px，确保严谨的对齐关系。
- **信息密度**：慢性病系统涉及大量表单与列表，我们通过适度的垂直间距 (Stack) 来区分逻辑块，而非使用繁琐的分隔线。

## 层级与深度

为了在浅灰背景上构建清晰的视觉结构，本系统放弃了强烈的投影，转而使用**环境柔和阴影 (Ambient Shadows)**。

- **基础卡片层**：使用极低透明度 (6%) 的深色投影，模糊半径较大 (12px-20px)，使卡片看起来像是微微悬浮在背景之上。
- **悬停态 (Hover)**：当用户交互时，阴影深度略微增加，并伴随 2px 的垂直位移，增强反馈感。
- **容器区分**：利用背景色的微差（如纯白卡片放置在 #F4F7F9 背景上）来建立第一层级，仅在需要强调点击或浮动面板时使用阴影。

## 形状

形状语言遵循“克制的圆润”原则，既避免了直角的尖锐感，也防止了过度圆润导致的非专业感。

- **通用圆角 (rounded-md)**：标准组件如按钮、输入框使用 8px (0.5rem) 圆角。
- **卡片容器 (rounded-lg)**：主数据卡片使用 16px (1rem) 圆角，营造温和的医疗辅助氛围。
- **状态标签 (Pill)**：风险等级标签（如“高风险”）采用全圆角（药丸形），便于在方形数据矩阵中被迅速识别。

## 组件

- **按钮 (Buttons)**：主操作采用深蓝绿色实色填充，文字反白；次要操作采用深蓝绿色描边或浅灰色背景。
- **卡片 (Cards)**：所有的患者信息、检测指标均承载于白色圆角卡片中。卡片头部包含清晰的标题和操作区。
- **输入字段 (Input Fields)**：采用浅灰色描边 (#D1D9E0)，聚焦时变为深蓝绿色高亮，并伴随柔和的内阴影。
- **风险标签 (Chips/Tags)**：通过背景色的饱和度区分风险等级。高风险使用淡红色背景配深红文字，保持警示性的同时也确保文字可读。
- **数据图表 (Charts)**：折线图与柱状图优先使用主色与辅助蓝，关键预警点使用警示色标注，背景辅助线保持极淡。
- **列表 (Lists)**：间距宽绰，每行均有微弱的底部分隔线或交互时的背景色变化，以支持长列表的数据核对。