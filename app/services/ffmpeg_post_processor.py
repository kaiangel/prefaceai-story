"""
FFmpeg 音频后处理服务

负责对 Mureka API 输出的 BGM 进行：
  1. 切末尾 4 秒水印（Mureka "当前内容由 AI 生成" 水印）
  2. 根据故事篇幅裁剪到目标时长（快闪 ~60s / 短篇 ~90s / 中篇 ~180s）
  3. 应用音量系数（用户调过的 bgm_volume，0.0-1.0，破坏性应用）
  4. 淡入（1s）+ 淡出（3s）
  5. QA 检测：静音检测 + 音量电平（LUFS）

使用 subprocess 直接调用 FFmpeg 命令行，不依赖 ffmpeg-python 第三方库。
"""

import json
import logging
import re
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# Mureka 输出末尾水印长度（秒）
MUREKA_WATERMARK_DURATION_SEC = 4.0

# 淡入淡出参数（秒）
FADE_IN_DURATION_SEC = 1.0
FADE_OUT_DURATION_SEC = 3.0

# QA 参数
QA_SILENCE_THRESHOLD_DB = -30      # 静音检测阈值 dB
QA_SILENCE_MIN_DURATION_SEC = 5.0  # 触发静音警告的最短持续时间（秒）
QA_LUFS_MIN = -23.0                # LUFS 响度下限
QA_LUFS_MAX = -14.0                # LUFS 响度上限


def _get_ffmpeg_path() -> Optional[str]:
    """
    查找 ffmpeg 可执行文件路径。

    Returns:
        ffmpeg 的绝对路径，如果找不到则返回 None。
    """
    return shutil.which("ffmpeg")


def _get_ffprobe_path() -> Optional[str]:
    """
    查找 ffprobe 可执行文件路径。

    Returns:
        ffprobe 的绝对路径，如果找不到则返回 None。
    """
    return shutil.which("ffprobe")


def get_audio_duration(file_path: str) -> float:
    """
    使用 ffprobe 获取音频文件总时长（秒）。

    Args:
        file_path: 音频文件的绝对路径。

    Returns:
        音频时长（秒），浮点数。

    Raises:
        RuntimeError: 如果 ffprobe 不可用或解析失败。
    """
    ffprobe_path = _get_ffprobe_path()
    if not ffprobe_path:
        raise RuntimeError(
            "[FFmpegPostProcessor] ffprobe 未找到。请确认 FFmpeg 已安装并在 PATH 中。"
        )

    cmd = [
        ffprobe_path,
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"[FFmpegPostProcessor] ffprobe 返回错误 (code={result.returncode}): {result.stderr.strip()}"
            )
        duration_str = result.stdout.strip()
        if not duration_str:
            raise RuntimeError(
                f"[FFmpegPostProcessor] ffprobe 无输出，文件可能损坏: {file_path}"
            )
        return float(duration_str)
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"[FFmpegPostProcessor] ffprobe 超时（30s）: {file_path}"
        )
    except ValueError as e:
        raise RuntimeError(
            f"[FFmpegPostProcessor] ffprobe 输出无法解析为浮点数 ('{duration_str}'): {e}"
        )


def process_bgm(
    input_path: str,
    output_path: str,
    target_duration_sec: float,
    volume: float = 1.0,
) -> dict:
    """
    FFmpeg 后处理：切水印 + 裁剪 + 淡入淡出 + 音量系数 + QA 检测。

    处理步骤（一次性 filter_complex）：
      1. 切末尾 4 秒（Mureka 水印）
      2. 裁剪到目标时长（不补长，只裁短）
      3. 应用音量系数（0.0-1.0，破坏性）
      4. 淡入 1 秒 + 淡出 3 秒
      5. 编码为 mp3 (libmp3lame, qscale:a 2)
      6. QA：静音检测 (-30dB / ≥5s 段)
      7. QA：LUFS 响度检测 (-23 ~ -14 范围)

    目标时长预设：
      - 快闪（~10 shots）: 60s
      - 短篇（~18 shots）: 90s
      - 中篇（~36 shots）: 180s

    Args:
        input_path:          原始 Mureka mp3 路径。
        output_path:         处理后 mp3 输出路径。
        target_duration_sec: 目标时长秒（60 / 90 / 180 等）。
        volume:              音量系数 0.0-1.0。超过 1.0 不放大，强制截断到 1.0。

    Returns:
        dict 包含以下字段：
            success (bool)               — 处理是否成功
            output_path (str)            — 输出文件路径（成功时）
            output_duration_sec (float)  — 实际输出时长（成功时）
            qa_silence_detected (bool)   — True 表示发现 ≥5s / -30dB 静音段
            qa_silence_details (str)     — 静音段描述（诊断用）
            qa_lufs (float)              — 整体响度 LUFS 值
            qa_lufs_in_range (bool)      — True 表示在 -23 ~ -14 区间
            warnings (list[str])         — 非阻塞警告列表
            error (str)                  — 错误信息（失败时）
    """
    warnings: list[str] = []

    # ------------------------------------------------------------------
    # 0. 前置检查
    # ------------------------------------------------------------------
    ffmpeg_path = _get_ffmpeg_path()
    if not ffmpeg_path:
        return {
            "success": False,
            "error": (
                "[FFmpegPostProcessor] ffmpeg 未找到。"
                "请确认 FFmpeg 已安装并在 PATH 中（brew install ffmpeg）。"
            ),
        }

    # 音量参数校验：最大 1.0（不放大）
    if volume > 1.0:
        warnings.append(
            f"volume={volume} 超过 1.0，已截断到 1.0（本服务不做放大处理）。"
        )
        volume = 1.0
    if volume < 0.0:
        return {
            "success": False,
            "error": f"[FFmpegPostProcessor] volume={volume} 无效，必须 0.0-1.0。",
        }

    # ------------------------------------------------------------------
    # 1. 获取输入文件时长
    # ------------------------------------------------------------------
    try:
        input_duration = get_audio_duration(input_path)
    except RuntimeError as e:
        return {"success": False, "error": str(e)}

    logger.info(
        "[FFmpegPostProcessor] 开始处理 BGM: input=%s, input_duration=%.2fs, "
        "target=%.2fs, volume=%.2f",
        input_path, input_duration, target_duration_sec, volume,
    )

    # ------------------------------------------------------------------
    # 2. 计算实际裁剪时长
    #    先切末尾水印：effective_input = input_duration - WATERMARK
    #    再裁剪到目标时长：actual_duration = min(target, effective_input)
    #    边界：如果原始文件太短，保留去水印后全部内容
    # ------------------------------------------------------------------
    effective_input = input_duration - MUREKA_WATERMARK_DURATION_SEC
    if effective_input <= 0:
        warnings.append(
            f"输入文件时长 {input_duration:.2f}s 不足以切除 {MUREKA_WATERMARK_DURATION_SEC}s 水印，"
            "将直接使用原始文件（不切水印）。"
        )
        effective_input = input_duration

    # 实际输出时长：不补长，只裁短
    actual_duration = min(target_duration_sec, effective_input)

    # 淡出起始位置：在输出音频的末尾 3 秒开始淡出
    fade_out_start = max(0.0, actual_duration - FADE_OUT_DURATION_SEC)

    # ------------------------------------------------------------------
    # 3. 构建 FFmpeg filter 链（一次性，不多次调用）
    #
    #    atrim=0:{effective_input}         → 切末尾水印
    #    atrim=0:{actual_duration}         → 裁剪到目标时长
    #    volume={volume}                   → 音量系数
    #    afade=t=in:st=0:d=1              → 淡入 1s
    #    afade=t=out:st={fade_out_start}:d=3 → 淡出 3s
    #
    #    注意：两个 atrim 串联，第一个切水印，第二个裁剪时长。
    #    asetpts=PTS-STARTPTS 在每个 atrim 后重置时间戳，防止跳帧/静音。
    # ------------------------------------------------------------------
    filter_chain = (
        f"atrim=0:{effective_input:.6f},"
        f"asetpts=PTS-STARTPTS,"
        f"atrim=0:{actual_duration:.6f},"
        f"asetpts=PTS-STARTPTS,"
        f"volume={volume:.4f},"
        f"afade=t=in:st=0:d={FADE_IN_DURATION_SEC},"
        f"afade=t=out:st={fade_out_start:.6f}:d={FADE_OUT_DURATION_SEC}"
    )

    cmd_process = [
        ffmpeg_path,
        "-y",                        # 覆盖输出文件（不弹交互提示）
        "-i", input_path,
        "-af", filter_chain,
        "-acodec", "libmp3lame",
        "-qscale:a", "2",            # VBR 质量 2（约 190 kbps，高质量）
        output_path,
    ]

    logger.debug("[FFmpegPostProcessor] Step 1 命令: %s", " ".join(cmd_process))

    try:
        result_process = subprocess.run(
            cmd_process,
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
        )
        if result_process.returncode != 0:
            return {
                "success": False,
                "error": (
                    f"[FFmpegPostProcessor] FFmpeg 处理失败 (code={result_process.returncode}):\n"
                    f"{result_process.stderr[-2000:]}"  # 只取最后 2000 字符
                ),
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "[FFmpegPostProcessor] FFmpeg 处理超时（300s）。",
        }

    # ------------------------------------------------------------------
    # 4. 获取输出文件实际时长
    # ------------------------------------------------------------------
    try:
        output_duration = get_audio_duration(output_path)
    except RuntimeError as e:
        warnings.append(f"无法获取输出文件时长: {e}")
        output_duration = actual_duration  # fallback 到计算值

    logger.info(
        "[FFmpegPostProcessor] ✅ 处理完成: output=%s, output_duration=%.2fs",
        output_path, output_duration,
    )

    # ------------------------------------------------------------------
    # 5. QA Step 1 — 静音检测
    #    ffmpeg -i {output} -af silencedetect=n=-30dB:d=5 -f null - 2>&1
    #    解析 stderr 中的 silence_start / silence_end 行。
    # ------------------------------------------------------------------
    qa_silence_detected = False
    qa_silence_details = ""

    cmd_silence = [
        ffmpeg_path,
        "-i", output_path,
        "-af", f"silencedetect=n={QA_SILENCE_THRESHOLD_DB}dB:d={QA_SILENCE_MIN_DURATION_SEC}",
        "-f", "null",
        "-",
    ]

    try:
        result_silence = subprocess.run(
            cmd_silence,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # silencedetect 输出在 stderr
        stderr_silence = result_silence.stderr

        # 解析 silence_start / silence_end 对
        silence_starts = re.findall(r"silence_start:\s*([\d.]+)", stderr_silence)
        silence_ends = re.findall(r"silence_end:\s*([\d.]+)", stderr_silence)
        silence_durations = re.findall(
            r"silence_end:.*?silence_duration:\s*([\d.]+)", stderr_silence
        )

        if silence_starts:
            qa_silence_detected = True
            details_parts = []
            for i, start in enumerate(silence_starts):
                end = silence_ends[i] if i < len(silence_ends) else "?"
                dur = silence_durations[i] if i < len(silence_durations) else "?"
                details_parts.append(
                    f"段{i+1}: {start}s ~ {end}s (时长 {dur}s)"
                )
            qa_silence_details = "; ".join(details_parts)
            warnings.append(
                f"QA: 检测到 {len(silence_starts)} 个静音段（≥{QA_SILENCE_MIN_DURATION_SEC}s / {QA_SILENCE_THRESHOLD_DB}dB）: {qa_silence_details}"
            )
            logger.warning(
                "[FFmpegPostProcessor] QA 静音告警: %s", qa_silence_details
            )
        else:
            logger.info("[FFmpegPostProcessor] QA 静音检测: 无异常静音段 ✅")

    except subprocess.TimeoutExpired:
        warnings.append("QA 静音检测超时（120s），已跳过。")
        logger.warning("[FFmpegPostProcessor] QA 静音检测超时，已跳过。")

    # ------------------------------------------------------------------
    # 6. QA Step 2 — LUFS 音量电平检测（EBU R128 真实积分响度）
    #    使用 ebur128 filter（正确实现 EBU R128），不用 loudnorm 单 pass
    #    （loudnorm 单 pass 只测 RMS，input_i 字段并非真实 integrated LUFS）
    #    ffmpeg -i {output} -af ebur128=peak=true -f null - 2>&1
    #    解析 stderr 末尾 "Integrated loudness:" 段，取 "I: -XX.X LUFS" 行。
    # ------------------------------------------------------------------
    qa_lufs = 0.0
    qa_lufs_in_range = True  # 默认 True，检测失败时不误报

    cmd_lufs = [
        ffmpeg_path,
        "-i", output_path,
        "-af", "ebur128=peak=true",
        "-f", "null",
        "-",
    ]

    try:
        result_lufs = subprocess.run(
            cmd_lufs,
            capture_output=True,
            text=True,
            timeout=120,
        )
        stderr_lufs = result_lufs.stderr

        # ebur128 在 stderr 末尾输出汇总段，格式：
        #   Integrated loudness:
        #     I:         -18.5 LUFS
        #     Threshold: -28.5 LUFS
        # 先定位 "Integrated loudness:" 段，再从后续行提取 "I: -XX.X LUFS"
        lufs_parsed = False
        integrated_section = False
        for line in stderr_lufs.splitlines():
            if "Integrated loudness:" in line:
                integrated_section = True
                continue
            if integrated_section:
                # 匹配 "    I:         -18.5 LUFS" 格式（允许正负数、小数）
                m = re.search(r"^\s+I:\s+([-+]?\d+\.?\d*)\s+LUFS", line)
                if m:
                    raw_val = m.group(1).strip()
                    # 处理 "-inf" 等特殊值（ebur128 静音时输出 -inf）
                    if raw_val.lower() in ("-inf", "inf", "nan"):
                        qa_lufs = -99.0
                        warnings.append(
                            "QA LUFS: 检测到 -inf 响度（文件可能为静音），已记录为 -99.0 dBLUFS。"
                        )
                    else:
                        qa_lufs = float(raw_val)

                    qa_lufs_in_range = QA_LUFS_MIN <= qa_lufs <= QA_LUFS_MAX
                    lufs_parsed = True

                    if qa_lufs_in_range:
                        logger.info(
                            "[FFmpegPostProcessor] QA LUFS: %.1f dBLUFS ✅（范围 %s ~ %s）",
                            qa_lufs, QA_LUFS_MIN, QA_LUFS_MAX,
                        )
                    else:
                        msg = (
                            f"QA LUFS: {qa_lufs:.1f} dBLUFS 超出范围（{QA_LUFS_MIN} ~ {QA_LUFS_MAX}）。"
                            "非阻塞，已记录。"
                        )
                        warnings.append(msg)
                        logger.warning("[FFmpegPostProcessor] %s", msg)
                    break
                # 离开 Integrated loudness 段（遇到下一个非缩进块标题）
                elif line and not line.startswith(" ") and not line.startswith("\t"):
                    integrated_section = False

        if not lufs_parsed:
            warnings.append("QA LUFS: 未能从 ebur128 输出解析 LUFS 值，已跳过。")
            logger.warning("[FFmpegPostProcessor] QA LUFS: 未能解析 ebur128 LUFS 输出。")

    except subprocess.TimeoutExpired:
        warnings.append("QA LUFS 检测超时（120s），已跳过。")
        logger.warning("[FFmpegPostProcessor] QA LUFS 检测超时，已跳过。")

    # ------------------------------------------------------------------
    # 7. 汇总返回
    # ------------------------------------------------------------------
    return {
        "success": True,
        "output_path": output_path,
        "output_duration_sec": output_duration,
        "qa_silence_detected": qa_silence_detected,
        "qa_silence_details": qa_silence_details,
        "qa_lufs": qa_lufs,
        "qa_lufs_in_range": qa_lufs_in_range,
        "warnings": warnings,
    }


# =============================================================================
# 单元测试入口（PM 验证用）
# =============================================================================

if __name__ == "__main__":
    import os

    print("=" * 60)
    print("FFmpegPostProcessor — 单元测试")
    print("=" * 60)

    # 测试参数
    INPUT_PATH = (
        "test_output/manualtest/sq_upgrade_ab_test/"
        "20260304_113630/bgm_v4_simple.mp3"
    )
    OUTPUT_PATH = "/tmp/bgm_test_output.mp3"
    TARGET_DURATION_SEC = 180.0
    VOLUME = 0.7

    # 解析为绝对路径（相对于项目根目录）
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_input_path = os.path.join(project_root, INPUT_PATH)

    print(f"\n输入文件: {abs_input_path}")
    print(f"输出文件: {OUTPUT_PATH}")
    print(f"目标时长: {TARGET_DURATION_SEC}s")
    print(f"音量系数: {VOLUME}")

    if not os.path.exists(abs_input_path):
        print(f"\n❌ 错误: 输入文件不存在: {abs_input_path}")
        print("请确认测试文件路径正确。")
        exit(1)

    # 先检测输入文件时长
    print("\n[Step 0] 检测输入文件时长...")
    try:
        input_dur = get_audio_duration(abs_input_path)
        print(f"  输入文件时长: {input_dur:.2f}s")
    except RuntimeError as e:
        print(f"  ❌ 失败: {e}")
        exit(1)

    # 执行处理
    print("\n[Step 1-3] 开始 FFmpeg 处理（切水印 + 裁剪 + 淡入淡出 + 音量）...")
    result = process_bgm(
        input_path=abs_input_path,
        output_path=OUTPUT_PATH,
        target_duration_sec=TARGET_DURATION_SEC,
        volume=VOLUME,
    )

    # 打印完整 dict
    print("\n返回结果:")
    print("-" * 40)
    for key, value in result.items():
        if key == "warnings":
            print(f"  {key}: [{len(value)} 条]")
            for w in value:
                print(f"    - {w}")
        elif key == "error":
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
    print("-" * 40)

    if result.get("success"):
        print(f"\n✅ 处理成功!")
        print(f"   输出文件: {result['output_path']}")
        print(f"   输出时长: {result['output_duration_sec']:.2f}s")
        print(f"   QA 静音: {'⚠️  检测到静音段' if result['qa_silence_detected'] else '✅ 无异常'}")
        print(f"   QA LUFS: {result['qa_lufs']:.1f} dBLUFS {'✅' if result['qa_lufs_in_range'] else '⚠️  超出范围'}")
        if result["warnings"]:
            print(f"   ⚠️  警告: {len(result['warnings'])} 条（见上方 warnings 列表）")
    else:
        print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")
