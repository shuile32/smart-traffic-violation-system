# backend-midterm_ppt169_20260711 - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | backend-midterm_ppt169_20260711 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 10 |
| **Design Style** | dark-tech card + code-block — 深蓝底色，卡片式布局，每页左侧要点 + 右侧 JSON 代码段 |
| **Target Audience** | 课程答辩导师、同组同学 |
| **Use Case** | 中期答辩后端进度汇报 |
| **Delivery Purpose** | `presentation` — 每页一个独立主题，演讲者口述要点，屏幕展示代码段佐证 |
| **Content Strategy** | balanced — 保留所有真实 API 数据和代码，按逻辑重排为 10 页故事线 |
| **Created Date** | 2026-07-11 |

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top 50px, bottom 40px |
| **Content Area** | 1160×630 |

## III. Visual Theme

- **Mode**: briefing — 技术汇报，每页主题独立
- **Visual style**: dark-tech — 深色背景 + 霓虹青代码 + 卡片式布局
- **Theme**: Dark theme
- **Tone**: 专业、学术、技术感

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0a1628` | 页背景 |
| **Secondary bg** | `#0f1d32` | 卡片/面板背景 |
| **Primary** | `#409EFF` | 标题装饰、数字高亮 |
| **Accent** | `#00d4ff` | JSON key 高亮、代码边框 |
| **Secondary accent** | `#5b8def` | 次要强调 |
| **Body text** | `#e0e0e0` | 正文 |
| **Secondary text** | `#8899aa` | 说明文字 |
| **Tertiary text** | `#556677` | 页码/页脚 |
| **Border/divider** | `#1a3050` | 卡片边框 |
| **Success** | `#67c23a` | 完成标记 |
| **Warning** | `#f56c6c` | 问题标记 |

## IV. Typography

- **Heading**: 思源黑体 Bold, 36px, `#409EFF`
- **Subheading**: 思源黑体 Medium, 22px, `#e0e0e0`
- **Body**: 微软雅黑, 18px, `#c0c4cc`
- **Code**: Consolas / monospace, 14px, `#00d4ff` (keys), `#e0e0e0` (values)
- **Body size**: 24px (presentation)
- **Formula policy**: text-only

## V. Layout

每页统一模板：
```
┌──────────────────────────────────────┐
│  [标题条: primary accent bar + 标题]   │
├────────────────────┬─────────────────┤
│   要点列表          │   代码段卡片      │
│   · bullet 1       │   ┌───────────┐ │
│   · bullet 2       │   │ JSON/代码  │ │
│   · bullet 3       │   │ (monospace)│ │
│                     │   └───────────┘ │
├────────────────────┴─────────────────┤
│  [页脚: 页码 + 项目名]                │
└──────────────────────────────────────┘
```

## VI. Icon

- 状态标记用 emoji：✅ ⚠️ 🔴
- 箭头用 SVG 简单线条

## VII. Visualization

无数据图表。用代码段展示 API 响应。

## VIII. Image

无图片，纯代码+文字排版。

## IX. Content Outline

### Page 1: 封面
- 大标题「后端开发进度汇报」
- 副标题「FastAPI + SQLAlchemy + JWT/RBAC · 基于 AI 的交通违章智能管理平台」
- 底部：杨翼、张浩 · 2026.07

### Page 2: 后端 API 全览
- 左：18 个核心端点表格
- 右：业务闭环流程图（摄入→审核→归档→统计）
- 数据：205 测试 · 17 张表 · 4 角色 · 3 摄入来源

### Page 3: 登录鉴权 + RBAC
- 左：四角色说明、JWT 机制
- 右：POST /auth/login 和 GET /auth/me 的请求/响应 JSON

### Page 4: 图片摄入
- 左：三来源 + 安全机制（SHA-256 去重、magic byte 校验）
- 右：POST /intakes/citizen-reports 的 JSON 响应

### Page 5: 审核工作流
- 左：案件状态机 + approve/reject 流程
- 右：POST /cases/{id}/approve 请求/响应 JSON + 自动化链

### Page 6: 违章归档 + 通知
- 左：审核通过后的自动化链（Violation → 车主 → 模板 → SMTP → Reward）
- 右：GET /violations 和 GET /owners/{id}/violations JSON

### Page 7: 统计分析
- 左：4 维度聚合（overview/by-time/by-type/by-location）
- 右：GET /statistics/overview 和 /statistics/by-type 的 JSON

### Page 8: AI 接口层
- 左：适配器模式（ABC → Stub/Real → DI 工厂）
- 右：POST /internal/ai/yolo/detect 和 /review/text JSON

### Page 9: 数据库 + 权限矩阵
- 左：17 张表分层图
- 右：四角色权限矩阵 + `require_role` 代码段

### Page 10: 问题与后续计划
- 左：4 个当前问题
- 右：后续计划时间线

## X. Speaker Notes

每页对应简短口述要点，不展开。

## XI. Tech Constraints

- SVG viewBox 严格 1280×720
- 代码块用 `<text>` + monospace，不用 `<foreignObject>`
- 颜色引用 `var(--primary)` 等避免硬编码
- 圆角卡片 `rx="8"`
