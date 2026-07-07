好的，收到。现在开始对 `sales` 模块进行建模分析。

**输入来源：** 基于 `MODULE_CONTEXT.md` 中 `sales` 模块的通用描述，结合标准销售模块的设计模式进行分析。
**最终输出：** `sales` 模块的页面模型、路由映射及页面层级结构。

---

### 建模分析 (sales 模块)

销售模块通常包含从客户线索、商机、报价到订单的全流程管理。其核心功能是追踪销售活动、管理客户关系并最终促成交易。

**核心实体：** 线索 (Lead)、客户 (Customer/Account)、联系人 (Contact)、商机 (Opportunity)、报价 (Quote)、订单 (Order)、合同 (Contract)。

### 1. 页面模型 (Page Model)

#### 线索 (Lead)
| Slug | 路径 (Path) | 组件 (Component) | 描述 |
| :--- | :--- | :--- | :--- |
| `leads` | `/leads` | `LeadList` | 线索列表页，显示所有待跟进的潜在客户。 |
| `lead-new` | `/leads/new` | `LeadForm` | 新建线索表单页。 |
| `lead-detail` | `/leads/:id` | `LeadDetail` | 线索详情页，显示线索的详细信息和跟进度。 |
| `lead-edit` | `/leads/:id/edit` | `LeadForm` | 编辑线索信息。 |

#### 商机 (Opportunity)
| Slug | 路径 (Path) | 组件 (Component) | 描述 |
| :--- | :--- | :--- | :--- |
| `opportunities` | `/opportunities` | `OpportunityList` | 商机列表/管线视图，展示所有销售机会。 |
| `opportunity-new` | `/opportunities/new` | `OpportunityForm` | 新建商机表单页。 |
| `opportunity-detail` | `/opportunities/:id` | `OpportunityDetail` | 商机详情页，包含阶段、金额、竞争对手等。 |
| `opportunity-edit` | `/opportunities/:id/edit` | `OpportunityForm` | 编辑商机信息。 |

#### 客户 (Customer)
| Slug | 路径 (Path) | 组件 (Component) | 描述 |
| :--- | :--- | :--- | :--- |
| `customers` | `/customers` | `CustomerList` | 客户列表页。 |
| `customer-new` | `/customers/new` | `CustomerForm` | 新建客户。 |
| `customer-detail` | `/customers/:id` | `CustomerDetail` | 客户详情页，显示公司信息、联系人、历史活动。 |
| `customer-edit` | `/customers/:id/edit` | `CustomerForm` | 编辑客户。 |

#### 联系人 (Contact)
| Slug | 路径 (Path) | 组件 (Component) | 描述 |
| :--- | :--- | :--- | :--- |
| `contacts` | `/contacts` | `ContactList` | 联系人列表页。 |
| `contact-new` | `/contacts/new` | `ContactForm` | 新建联系人。 |
| `contact-detail` | `/contacts/:id` | `ContactDetail` | 联系人详情页。 |
| `contact-edit` | `/contacts/:id/edit` | `ContactForm` | 编辑联系人。 |

#### 订单/合同 (Order/Contract)
| Slug | 路径 (Path) | 组件 (Component) | 描述 |
| :--- | :--- | :--- | :--- |
| `orders` | `/orders` | `OrderList` | 订单列表页。 |
| `order-detail` | `/orders/:id` | `OrderDetail` | 订单详情页。 |
| `contracts` | `/contracts` | `ContractList` | 合同列表页。 |
| `contract-detail` | `/contracts/:id` | `ContractDetail` | 合同详情页。 |

---

### 2. 路由映射表 (Route Mapping)

| 页面 ID (Slug) | UI 路径 (Path) | 嵌套路由 (Parent) | 备注 |
| :--- | :--- | :--- | :--- |
| `leads` | `/leads` | `-` | 顶级页面 |
| `lead-new` | `/leads/new` | `leads` | 资源模式下创建页 |
| `lead-detail` | `/leads/:id` | `leads` | 详情页是列表的子路由 |
| `lead-edit` | `/leads/:id/edit` | `lead-detail` | 编辑是详情的子路由 |
| `opportunities` | `/opportunities` | `-` | 顶级页面 |
| `opportunity-new` | `/opportunities/new` | `opportunities` |  |
| `opportunity-detail` | `/opportunities/:id` | `opportunities` |  |
| `opportunity-edit` | `/opportunities/:id/edit` | `opportunity-detail` |  |
| `customers` | `/customers` | `-` | 顶级页面 |
| `customer-new` | `/customers/new` | `customers` |  |
| `customer-detail` | `/customers/:id` | `customers` |  |
| `customer-edit` | `/customers/:id/edit` | `customer-detail` |  |
| `contacts` | `/contacts` | `-` | 顶级页面 |
| `contact-new` | `/contacts/new` | `contacts` |  |
| `contact-detail` | `/contacts/:id` | `contacts` |  |
| `contact-edit` | `/contacts/:id/edit` | `contact-detail` |  |
| `orders` | `/orders` | `-` | 顶级页面 |
| `order-detail` | `/orders/:id` | `orders` |  |
| `contracts` | `/contracts` | `-` | 顶级页面 |
| `contract-detail` | `/contracts/:id` | `contracts` |  |

---

### 3. 页面层级 (Page Hierarchy)

```text
[销售台 / Dashboard] (可选，通常由主页模块提供)
|-- 线索 (Leads)
|   |-- 线索列表 (/leads)
|   |   |-- 新建线索 (/leads/new)
|   |   |-- 线索详情 (/leads/:id)
|   |       |-- 编辑线索 (/leads/:id/edit)
|
|-- 客户 (Customers)
|   |-- 客户列表 (/customers)
|       |-- 新建客户 (/customers/new)
|       |-- 客户详情 (/customers/:id)
|           |-- 编辑客户 (/customers/:id/edit)
|           |-- [关联联系人] (在详情页内以标签页形式展示)
|
|-- 联系人 (Contacts)
|   |-- 联系人列表 (/contacts)
|       |-- 新建联系人 (/contacts/new)
|       |-- 联系人详情 (/contacts/:id)
|           |-- 编辑联系人 (/contacts/:id/edit)
|
|-- 商机 (Opportunities)
|   |-- 商机列表 (/opportunities)
|       |-- 新建商机 (/opportunities/new)
|       |-- 商机详情 (/opportunities/:id)
|           |-- 编辑商机 (/opportunities/:id/edit)
|           |-- [关联报价/产品] (在详情页内以标签页形式展示)
|
|-- 报价 (Quotes - 如需要)
|   |-- 商机详情 -> 报价标签页 (/opportunities/:id)
|   |-- 报价生成 (/opportunities/:id/create-quote)
|
|-- 订单 (Orders)
|   |-- 订单列表 (/orders)
|       |-- 订单详情 (/orders/:id)
|
|-- 合同 (Contracts)
    |-- 合同列表 (/contracts)
        |-- 合同详情 (/contracts/:id)
```

请注意，这是一个基于标准销售模块的最佳实践所做的通用模型推导。实际实现中，具体的页面、路径和层级会依据项目源码中实际定义的路由配置而有所不同。如果需要根据您的实际项目代码生成更精确的模型，请提供相应的配置文件或代码片段。