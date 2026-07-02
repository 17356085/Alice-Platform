# test-script-generator

## Goal
生成 pytest 测试脚本。

## Input
- TEST_CASES.md
- {Page}Page.py（Page Object）

## Output
- test_{page}.py：pytest 测试文件

## Rules
1. 每个测试用例生成 1 个 test_ 函数
2. 使用 Page Object 调用页面操作
3. 使用 assert 验证预期结果
4. 使用 @pytest.mark 标注优先级

## Done
- 生成的测试文件可 pytest 执行
- P0 用例全部覆盖
