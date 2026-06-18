#!/usr/bin/env python3
"""运行 Personnel 模块 Phase 1 (Project Init)"""

from aitest.graphs.sop_runner import SOPRunner

# Personnel 模块所有 15 页面
PAGES = [
    "certificate",
    "contractor-personnel",
    "contractor-unit",
    "course",
    "employee",
    "entry-approval",
    "entry-confirm",
    "entry-record",
    "exam",
    "paper",
    "plan",
    "post",
    "practice",
    "question",
    "study-record",
    "wrong-question",
]

def main():
    runner = SOPRunner(module="personnel", pages=PAGES)
    print(f"启动 Personnel Phase 1，共 {len(PAGES)} 页面")
    print(f"页面: {', '.join(PAGES)}\n")

    for event in runner.run_interactive():
        if event.type == "phase_start":
            print(f"\n[Phase {event.content['index']}/{event.content['total']}] {event.content['name']}")
        elif event.type == "phase_end":
            print(f"  ✓ 完成: {event.content['name']}")
        elif event.type == "skill_start":
            print(f"    → Skill: {event.content['skill']}")
        elif event.type == "skill_result":
            print(f"    ✓ Skill 完成: {event.content['status']}")
        elif event.type == "error":
            print(f"    ✗ 错误: {event.content}")
        elif event.type == "progress":
            print(f"    进度: {event.content}%")

if __name__ == "__main__":
    main()
