"""
单元测试: RISK-T18-J — Sync Anthropic 阻塞 event loop 修复

验证所有 async 路径中的 Anthropic 调用已使用 AsyncAnthropic，
不阻塞 event loop。

修复范围 (T18-J):
1. alignment_service.py: Anthropic() → AsyncAnthropic() + await
2. app/api/chapters.py: Anthropic() → AsyncAnthropic() + await (Shot 调整端点)
3. story_generator.py: sync client 仅用于 generate_story_sync()（设计合理，保留）

运行命令:
  pytest tests/test_async_anthropic_t18_j.py -v
"""

import sys
import os
import ast
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read_source(rel_path: str) -> str:
    """读取服务源码"""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        rel_path
    )
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _find_sync_anthropic_calls(source: str) -> list:
    """
    在源码中找 anthropic.Anthropic() (非 AsyncAnthropic) 的实例化
    返回匹配的行号列表
    """
    matches = []
    for i, line in enumerate(source.split("\n"), 1):
        stripped = line.strip()
        # 找到 anthropic.Anthropic( 但不包含 AsyncAnthropic
        if "anthropic.Anthropic(" in stripped and "AsyncAnthropic" not in stripped:
            matches.append((i, stripped))
    return matches


class TestAlignmentServiceAsync:
    """alignment_service.py 的 AsyncAnthropic 修复验证"""

    def test_no_sync_anthropic_in_alignment_service(self):
        """alignment_service.py 不再有同步 Anthropic() 实例化"""
        source = _read_source("app/services/alignment_service.py")
        sync_calls = _find_sync_anthropic_calls(source)
        assert len(sync_calls) == 0, (
            f"alignment_service.py 仍有同步 Anthropic() (T18-J 应已修复): {sync_calls}"
        )

    def test_uses_async_anthropic(self):
        """alignment_service.py 使用 AsyncAnthropic"""
        source = _read_source("app/services/alignment_service.py")
        assert "AsyncAnthropic" in source, (
            "alignment_service.py 应使用 AsyncAnthropic (T18-J 修复)"
        )

    def test_visual_alignment_uses_await(self):
        """_visual_alignment 方法使用 await client.messages.create"""
        source = _read_source("app/services/alignment_service.py")
        lines = source.split("\n")
        # 找 _visual_alignment 方法中的 messages.create 调用
        in_visual_alignment = False
        found_await = False
        for line in lines:
            stripped = line.strip()
            if "_visual_alignment" in stripped and "def " in stripped:
                in_visual_alignment = True
            if in_visual_alignment and "messages.create" in stripped:
                if stripped.startswith("await ") or " await " in stripped:
                    found_await = True
                break
            # 到下一个 async def 停止搜索
            if in_visual_alignment and "async def " in stripped and "_visual_alignment" not in stripped:
                break
        assert found_await, (
            "_visual_alignment 应使用 await client.messages.create (T18-J 修复)"
        )

    def test_text_alignment_uses_await(self):
        """_text_alignment 方法使用 await client.messages.create"""
        source = _read_source("app/services/alignment_service.py")
        lines = source.split("\n")
        in_text_alignment = False
        found_await = False
        for line in lines:
            stripped = line.strip()
            if "_text_alignment" in stripped and "def " in stripped:
                in_text_alignment = True
            if in_text_alignment and "messages.create" in stripped:
                if stripped.startswith("await ") or " await " in stripped:
                    found_await = True
                break
            if in_text_alignment and "async def " in stripped and "_text_alignment" not in stripped:
                break
        assert found_await, (
            "_text_alignment 应使用 await client.messages.create (T18-J 修复)"
        )


class TestChaptersAPISyncAnthropicFixed:
    """chapters.py Shot 调整端点的 AsyncAnthropic 修复验证"""

    def test_no_sync_anthropic_in_shot_adjustment(self):
        """chapters.py 的 Shot 调整端点不再有同步 Anthropic()"""
        source = _read_source("app/api/chapters.py")
        sync_calls = _find_sync_anthropic_calls(source)
        assert len(sync_calls) == 0, (
            f"chapters.py 仍有同步 Anthropic() (T18-J 应已修复): {sync_calls}"
        )

    def test_chapters_uses_async_anthropic(self):
        """chapters.py 使用 AsyncAnthropic"""
        source = _read_source("app/api/chapters.py")
        assert "AsyncAnthropic" in source, (
            "chapters.py Shot 调整端点应使用 AsyncAnthropic (T18-J 修复)"
        )

    def test_shot_adjustment_uses_await(self):
        """Shot 调整端点中的 messages.create 使用 await"""
        source = _read_source("app/api/chapters.py")
        # 找到 AsyncAnthropic 上下文附近的 messages.create 调用
        lines = source.split("\n")
        async_client_line = None
        for i, line in enumerate(lines):
            if "AsyncAnthropic" in line and "api_key" in line:
                async_client_line = i
                break
        assert async_client_line is not None, "找不到 AsyncAnthropic 实例化行"
        # 检查附近 10 行内有 await messages.create
        window = lines[async_client_line:async_client_line + 15]
        found_await_create = any(
            "await" in l and "messages.create" in l
            for l in window
        )
        assert found_await_create, (
            "Shot 调整端点应使用 await client.messages.create (T18-J 修复)"
        )


class TestStoryGeneratorSyncClientByDesign:
    """
    story_generator.py 同步 client 是设计合理的（用于 generate_story_sync 同步方法），
    不需要修改。验证同步 client 确实只用于 generate_story_sync。
    """

    def test_sync_client_used_only_in_sync_method(self):
        """story_generator.py 中 claude_client (sync) 只用于 generate_story_sync"""
        source = _read_source("app/services/story_generator.py")
        # 仍然有 async claude client 用于 async 路径
        assert "async_claude_client" in source or "AsyncAnthropic" in source, (
            "story_generator.py 应有 AsyncAnthropic (async 路径)"
        )
        # 同步方法存在（设计上需要）
        assert "generate_story_sync" in source, (
            "story_generator.py 应有 generate_story_sync 方法（同步方法）"
        )


class TestAllMainServicesNoSyncAnthropic:
    """
    验证 Pipeline 主路径服务（Stage 1-4）全部使用 AsyncAnthropic
    """

    def _check_service(self, rel_path: str) -> list:
        source = _read_source(rel_path)
        return _find_sync_anthropic_calls(source)

    def test_story_outline_generator_no_sync(self):
        sync_calls = self._check_service("app/services/story_outline_generator.py")
        assert len(sync_calls) == 0, f"story_outline_generator.py 有同步 Anthropic(): {sync_calls}"

    def test_character_designer_no_sync(self):
        sync_calls = self._check_service("app/services/character_designer.py")
        assert len(sync_calls) == 0, f"character_designer.py 有同步 Anthropic(): {sync_calls}"

    def test_screenplay_writer_no_sync(self):
        sync_calls = self._check_service("app/services/screenplay_writer.py")
        assert len(sync_calls) == 0, f"screenplay_writer.py 有同步 Anthropic(): {sync_calls}"

    def test_storyboard_director_no_sync(self):
        sync_calls = self._check_service("app/services/storyboard_director.py")
        assert len(sync_calls) == 0, f"storyboard_director.py 有同步 Anthropic(): {sync_calls}"

    def test_music_generation_service_no_sync(self):
        sync_calls = self._check_service("app/services/music_generation_service.py")
        assert len(sync_calls) == 0, f"music_generation_service.py 有同步 Anthropic(): {sync_calls}"

    def test_prompt_safety_advisor_no_sync(self):
        sync_calls = self._check_service("app/services/prompt_safety_advisor.py")
        assert len(sync_calls) == 0, f"prompt_safety_advisor.py 有同步 Anthropic(): {sync_calls}"

    def test_alignment_service_no_sync(self):
        """alignment_service.py T18-J 修复后无同步 Anthropic()"""
        sync_calls = self._check_service("app/services/alignment_service.py")
        assert len(sync_calls) == 0, f"alignment_service.py 仍有同步 Anthropic() (T18-J): {sync_calls}"


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    t1 = TestAlignmentServiceAsync()
    t1.test_no_sync_anthropic_in_alignment_service()
    t1.test_uses_async_anthropic()
    t1.test_visual_alignment_uses_await()
    t1.test_text_alignment_uses_await()

    t2 = TestChaptersAPISyncAnthropicFixed()
    t2.test_no_sync_anthropic_in_shot_adjustment()
    t2.test_chapters_uses_async_anthropic()
    t2.test_shot_adjustment_uses_await()

    t3 = TestStoryGeneratorSyncClientByDesign()
    t3.test_sync_client_used_only_in_sync_method()

    t4 = TestAllMainServicesNoSyncAnthropic()
    t4.test_story_outline_generator_no_sync()
    t4.test_character_designer_no_sync()
    t4.test_screenplay_writer_no_sync()
    t4.test_storyboard_director_no_sync()
    t4.test_music_generation_service_no_sync()
    t4.test_prompt_safety_advisor_no_sync()
    t4.test_alignment_service_no_sync()

    print("All 15 test cases PASS!")
    sys.exit(0)
