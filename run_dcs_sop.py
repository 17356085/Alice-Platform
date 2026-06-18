#!/usr/bin/env python3
"""
快速测试 DCS SOP 通过 Chat API。
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/chat"

# 1. 创建会话
print("[1] Creating session...")
r = requests.post(f"{BASE_URL}/sessions")
if r.status_code != 200:
    print(f"Failed: {r.status_code} {r.text}")
    sys.exit(1)

session_id = r.json()["session_id"]
print(f"    Session: {session_id}")

# 2. 发送 SOP 触发消息
message = "dcs 完整流程"  # 触发 full-sop
print(f"[2] Sending message: '{message}'")
r = requests.post(
    f"{BASE_URL}/sessions/{session_id}/messages",
    json={"content": message}
)
if r.status_code != 200:
    print(f"Failed: {r.status_code} {r.text}")
    sys.exit(1)

msg_id = r.json()["message_id"]
stream_url = r.json()["stream_url"]
print(f"    Message ID: {msg_id}")
print(f"    Stream URL: {stream_url}")

# 3. 连接 SSE
print(f"[3] Connecting to SSE stream...")
stream_url_full = f"http://localhost:8000{stream_url}"
r = requests.get(stream_url_full, stream=True)
if r.status_code != 200:
    print(f"Failed: {r.status_code} {r.text}")
    sys.exit(1)

# 4. 打印事件流（前 50 个事件或 60 秒超时）
import time
start = time.time()
event_count = 0

print("[4] Streaming events...")
try:
    for line in r.iter_lines(decode_unicode=True):
        if time.time() - start > 60:
            print("[TIMEOUT] 60 seconds, stopping...")
            break
        if not line:
            continue
        if line.startswith("event:"):
            event = line.split(":", 1)[1].strip()
            print(f"    [event] {event}")
        elif line.startswith("data:"):
            data = line.split(":", 1)[1].strip()
            try:
                payload = json.loads(data)
                if "content" in payload:
                    content = payload["content"][:100]
                    print(f"        → {content}...")
                else:
                    print(f"        → {str(payload)[:100]}...")
            except:
                print(f"        → {data[:100]}...")
        event_count += 1
        if event_count >= 50:
            print(f"[50 events] Stopping stream trace...")
            break
except KeyboardInterrupt:
    print("[INTERRUPTED]")
except Exception as e:
    print(f"[ERROR] {e}")

print(f"\n[Done] Processed {event_count} event lines in {time.time()-start:.1f}s")
