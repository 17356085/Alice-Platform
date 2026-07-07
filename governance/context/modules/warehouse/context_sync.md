warehouse/
├── README.md
├── data/
│   ├── schema.graphql          # 数据模型定义
│   └── migrations/             # 数据库迁移
├── domain/
│   ├── entities/               # 领域实体
│   ├── aggregates/             # 聚合根
│   ├── domain_services/        # 领域服务
│   ├── repositories/           # 仓储接口
│   └── factories/              # 工厂类
├── application/
│   ├── services/               # 应用服务
│   ├── dtos/                   # 数据传输对象
│   ├── commands/               # 命令处理器
│   └── queries/                # 查询处理器
├── infrastructure/
│   ├── database/               # 数据库实现
│   ├── cache/                  # 缓存实现
│   ├── mq/                     # 消息队列
│   └── external/               # 外部系统集成
├── interfaces/
│   ├── rest/                   # REST API
│   ├── grpc/                   # gRPC服务
│   ├── graphql/                # GraphQL接口
│   └── events/                 # 事件订阅/发布
├── tests/
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── e2e/                    # 端到端测试
├── scripts/
│   ├── setup.sh                # 初始化脚本
│   └── seed.sh                 # 数据填充脚本
├── docs/
│   ├── architecture.md         # 架构文档
│   ├── api.md                  # API文档
│   └── domain-notes.md         # 领域设计笔记
├── governance/
│   ├── README.md               # 治理规则说明
│   ├── context/                # 上下文同步
│   ├── boundaries.md           # 限界上下文
│   ├── events.md               # 事件定义
│   └── invariants.md           # 不变约束
├── .tlo/
│   ├── project.yaml            # 项目元数据
│   └── modules/                # 模块管理
├── go.mod
├── go.sum
└── deploy/
    ├── k8s/
    └── docker-compose.yaml