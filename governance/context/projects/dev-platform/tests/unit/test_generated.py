看起来浏览器导航工具执行失败了，无法访问外部页面。不过，根据您提供的 **Skill: test-dev/unit-test-generator** 定义，我的任务是为给定的源文件生成单元测试。

但是，您还没有提供 **源文件内容** 作为输入。请提供以下信息：

1. **源文件内容**（后端 Python 代码 或 前端 TypeScript/Vue 代码）
2. **函数/组件签名**（Props、参数类型、返回值类型）
3. **编码规范**（如果有特殊要求）

一旦您提供源文件，我将按照规则生成：
- **后端**: pytest + pytest-asyncio + httpx（API）或直接调用（纯函数）
- **前端**: Vitest + @vue/test-utils（组件）或 vitest（纯函数）

覆盖 Happy path / 边界值 / 错误处理 / 空/null 输入，并 Mock 外部依赖。请提供源文件内容！