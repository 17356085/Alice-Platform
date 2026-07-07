# lab 项目上下文同步文件
name: "lab"
url: "https://github.com/your-org/lab"  # 替换为实际仓库地址
modules:
  - path: "lab/core"               # 核心模块路径
    description: "核心库与公共工具"
  - path: "lab/frontend"           # 前端模块
    description: "用户界面与前端资源"
  - path: "lab/backend"            # 后端模块
    description: "API 服务与业务逻辑"
  - path: "lab/infrastructure"     # 基础设施模块
    description: "CI/CD、Docker、Kubernetes 配置"
  - path: "lab/documentation"     # 文档模块
    description: "项目文档与开发指南"