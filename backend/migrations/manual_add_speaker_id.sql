-- 手动迁移脚本：为 transcripts 表增加 speaker_id 字段
-- Sprint 2: 多说话人识别（Diarization）

-- 添加 speaker_id 列
ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS speaker_id VARCHAR(32);

-- 创建索引（可选，加速按说话人查询）
CREATE INDEX IF NOT EXISTS idx_transcripts_speaker_id ON transcripts(speaker_id);

-- 说明：
-- speaker_id 格式："SPEAKER_00", "SPEAKER_01", "SPEAKER_02"
-- 初始值为 NULL，由 diarization 服务在对话结束后自动填充



