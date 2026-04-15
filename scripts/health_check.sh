#!/bin/bash
# health_check.sh — 检查 VPS 服务健康状态
#
# 用法:
#   手动执行:  bash scripts/health_check.sh
#   定时检查:  加入 crontab，每 5 分钟执行一次
#   crontab:   */5 * * * * /path/to/scripts/health_check.sh >> /var/log/xuhua_health.log 2>&1

HEALTH_URL="https://prefaceai.mov/api/health"
TIMEOUT=10

response=$(curl -s --max-time "$TIMEOUT" "$HEALTH_URL" 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): FAILED - curl error (exit=$exit_code) URL=$HEALTH_URL"
    exit 1
fi

if echo "$response" | grep -q "healthy"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): OK - $HEALTH_URL -> $response"
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S'): FAILED - unexpected response: $response"
    # 未来可以加通知（邮件/微信/钉钉）
    # 示例: curl -X POST "https://oapi.dingtalk.com/robot/send?access_token=XXX" \
    #   -H "Content-Type: application/json" \
    #   -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"序话Story 健康检查失败: $response\"}}"
    exit 1
fi
