#!/usr/bin/env python3
"""
Example client for Claude Code Server

Demonstrates how to submit tasks and stream progress via WebSocket.
"""

import asyncio
import json
from datetime import datetime

import aiohttp


class ClaudeServerClient:
    """Simple client for Claude Code Server"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    async def submit_task(self, task_id: str, prompt: str, workspace: str, **options):
        """Submit a task to the server"""
        url = f"{self.base_url}/api/v1/tasks"
        
        payload = {
            "task_id": task_id,
            "prompt": prompt,
            "workspace": workspace,
            "options": options.get("options", {}),
            "session": options.get("session", {"reuse_existing": False})
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()
    
    async def stream_progress(self, task_id: str):
        """Stream task progress via WebSocket"""
        ws_url = self.base_url.replace("http", "ws") + f"/ws/tasks/{task_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                print(f"🔗 Connected to WebSocket for task: {task_id}")
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        event = json.loads(msg.data)
                        yield event
                        
                        if event.get("type") == "complete":
                            break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"❌ WebSocket error: {ws.exception()}")
                        break
    
    async def get_task_status(self, task_id: str):
        """Get task status"""
        url = f"{self.base_url}/api/v1/tasks/{task_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()
    
    async def interrupt_task(self, task_id: str):
        """Interrupt a running task"""
        url = f"{self.base_url}/api/v1/tasks/{task_id}/interrupt"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()


def print_event(event: dict):
    """Pretty print event"""
    event_type = event.get("type")
    timestamp = event.get("timestamp", "")
    data = event.get("data", {})
    
    if event_type == "message":
        msg_type = data.get("message_type", "")
        content = data.get("content", "")
        print(f"💬 [{msg_type}] {content[:100]}...")
    
    elif event_type == "tool_use":
        tool_name = data.get("tool_name", "")
        print(f"🔧 Tool: {tool_name}")
    
    elif event_type == "tool_result":
        content = data.get("content", "")
        is_error = data.get("is_error", False)
        status = "❌" if is_error else "✅"
        print(f"{status} Tool result: {str(content)[:100]}...")
    
    elif event_type == "progress":
        turns = data.get("turns", 0)
        tokens = data.get("tokens_used", 0)
        files = data.get("files_modified", 0)
        elapsed = data.get("elapsed_time_ms", 0)
        print(f"📊 Progress: turns={turns}, tokens={tokens}, files={files}, time={elapsed}ms")
    
    elif event_type == "complete":
        summary = data.get("summary", "")
        exit_code = data.get("exit_code", 0)
        status = "✅" if exit_code == 0 else "❌"
        print(f"{status} Complete: {summary}")
    
    elif event_type == "error":
        error = data.get("error", "")
        print(f"❌ Error: {error}")


async def example_task():
    """Example: Submit a task and stream progress"""
    client = ClaudeServerClient()
    
    # Submit task
    print("📤 Submitting task...")
    result = await client.submit_task(
        task_id=f"example-{int(datetime.now().timestamp())}",
        prompt="Create a Python script that prints 'Hello, Claude Code Server!'",
        workspace="/tmp/test-workspace",
        options={
            "allowed_tools": ["Write", "Read", "Bash"],
            "permission_mode": "acceptEdits",
            "max_turns": 10,
            "timeout": 300
        }
    )
    
    task_id = result["task_id"]
    print(f"✅ Task submitted: {task_id}")
    print(f"🔗 WebSocket URL: {result['websocket_url']}")
    print()
    
    # Stream progress
    print("📡 Streaming progress...\n")
    async for event in client.stream_progress(task_id):
        print_event(event)
    
    print("\n🎉 Task completed!")


async def example_interrupt():
    """Example: Submit a task and interrupt it"""
    client = ClaudeServerClient()
    
    # Submit long-running task
    result = await client.submit_task(
        task_id=f"interrupt-{int(datetime.now().timestamp())}",
        prompt="Count from 1 to 1000 slowly, printing each number",
        workspace="/tmp/test-workspace"
    )
    
    task_id = result["task_id"]
    print(f"✅ Task submitted: {task_id}")
    
    # Start streaming in background
    stream_task = asyncio.create_task(
        consume_stream(client, task_id)
    )
    
    # Wait a bit then interrupt
    await asyncio.sleep(3)
    print("\n⏸️  Interrupting task...")
    await client.interrupt_task(task_id)
    
    # Wait for stream to complete
    await stream_task


async def consume_stream(client, task_id):
    """Helper to consume stream"""
    async for event in client.stream_progress(task_id):
        print_event(event)


if __name__ == "__main__":
    print("🚀 Claude Code Server - Example Client\n")
    
    # Run example
    asyncio.run(example_task())
    
    # Uncomment to test interruption
    # asyncio.run(example_interrupt())
