"""Test script for API endpoints"""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"


async def test_api():
    """Test the full API workflow"""
    print("=" * 60)
    print("序话Story - API Test")
    print("=" * 60)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # 1. Health check
        print("\n1. 健康检查...")
        resp = await client.get("/health")
        print(f"   状态: {resp.json()}")

        # 2. Login
        print("\n2. 登录测试...")
        resp = await client.post(
            "/api/auth/login",
            json={"user_id": "kai", "password": "xuhua2024"},
        )
        if resp.status_code != 200:
            print(f"   ❌ 登录失败: {resp.text}")
            return
        login_data = resp.json()
        print(f"   ✅ 登录成功: {login_data['name']}")
        token = login_data["token"]
        headers = {"X-User-ID": token}

        # 3. Create project
        print("\n3. 创建项目...")
        resp = await client.post(
            "/api/projects/",
            headers=headers,
            json={
                "original_idea": "一只流浪猫在城市中寻找家的故事，它遇到了各种各样的人和动物，最终找到了属于自己的温暖",
                "style_preset": "illustration",
                "total_chapters": 1,
                "chapter_duration_minutes": 2,
                "character_count": 3,
                "language": "zh-CN",
            },
        )
        if resp.status_code != 200:
            print(f"   ❌ 创建失败: {resp.text}")
            return
        project_data = resp.json()
        print(f"   ✅ 项目创建成功!")
        print(f"   项目ID: {project_data['project_id']}")
        print(f"   章节ID: {project_data['chapter_id']}")
        print(f"   任务ID: {project_data['job_id']}")

        project_id = project_data["project_id"]

        # 4. Poll for status
        print("\n4. 等待故事生成...")
        max_wait = 120  # 2 minutes max
        start_time = time.time()

        while time.time() - start_time < max_wait:
            resp = await client.get(
                f"/api/projects/{project_id}/chapters/1/status",
                headers=headers,
            )
            status = resp.json()
            print(
                f"   进度: {status['progress']}% - {status['message']} ({status['status']})"
            )

            if status["status"] == "completed":
                print("   ✅ 故事生成完成!")
                break
            elif status["status"] == "failed":
                print(f"   ❌ 生成失败: {status['message']}")
                return

            await asyncio.sleep(3)  # Poll every 3 seconds
        else:
            print("   ⏱️ 超时，但任务可能仍在运行")

        # 5. Get story content
        print("\n5. 获取故事内容...")
        resp = await client.get(
            f"/api/projects/{project_id}/chapters/1/story",
            headers=headers,
        )
        if resp.status_code != 200:
            print(f"   ❌ 获取失败: {resp.text}")
            return

        story = resp.json()
        print(f"   ✅ 故事获取成功!")
        print(f"   标题: {story['title']}")
        print(f"   摘要: {story['summary'][:100]}...")
        print(f"   角色数: {len(story['characters'])}")
        print(f"   场景数: {len(story['scenes'])}")

        # 6. List projects
        print("\n6. 列出用户项目...")
        resp = await client.get("/api/projects/", headers=headers)
        projects = resp.json()
        print(f"   共 {len(projects)} 个项目")
        for p in projects:
            print(f"   - {p['title']}: {p['original_idea'][:30]}...")

        print("\n" + "=" * 60)
        print("✅ API 测试完成!")
        print("=" * 60)


def main():
    """Run the test"""
    asyncio.run(test_api())


if __name__ == "__main__":
    main()
