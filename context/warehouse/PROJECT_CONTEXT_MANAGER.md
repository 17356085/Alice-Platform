项目根目录/
├── src/
│   ├── modules/
│   │   ├── warehouse/
│   │   │   ├── pages/
│   │   │   │   ├── InventoryList/
│   │   │   │   │   ├── index.tsx
│   │   │   │   │   └── components/
│   │   │   │   │       └── InventoryTable.tsx
│   │   │   │   ├── StockIn/
│   │   │   │   │   ├── index.tsx
│   │   │   │   │   └── components/
│   │   │   │   │       └── StockInForm.tsx
│   │   │   │   └── StockOut/
│   │   │   │       ├── index.tsx
│   │   │   │       └── components/
│   │   │   │           └── StockOutForm.tsx
│   │   │   ├── components/
│   │   │   │   ├── Shared/
│   │   │   │   │   ├── LocationSelect.tsx
│   │   │   │   │   └── ProductSearch.tsx
│   │   │   ├── api/
│   │   │   │   ├── inventory.ts
│   │   │   │   ├── stockIn.ts
│   │   │   │   └── stockOut.ts
│   │   │   ├── routes.tsx          # 路由定义
│   │   │   └── index.tsx           # 模块入口
│   │   └── ... (其他模块)
│   ├── shared/
│   ├── router/
│   └── App.tsx
└── package.json