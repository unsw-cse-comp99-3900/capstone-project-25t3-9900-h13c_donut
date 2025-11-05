from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "username" VARCHAR(256) NOT NULL UNIQUE,
    "email" VARCHAR(256),
    "password_hash" VARCHAR(255) NOT NULL,
    "role" VARCHAR(16) NOT NULL DEFAULT 'user',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_users_usernam_266d85" ON "users" ("username");
CREATE TABLE IF NOT EXISTS "conversations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "title" VARCHAR(128),
    "accent" VARCHAR(8) NOT NULL,
    "model" VARCHAR(16) NOT NULL DEFAULT 'free',
    "started_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ended_at" TIMESTAMPTZ,
    "duration_sec" INT,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "transcripts" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "seq" INT NOT NULL,
    "is_final" BOOL NOT NULL,
    "start_ms" BIGINT,
    "end_ms" BIGINT,
    "text" TEXT NOT NULL,
    "audio_url" VARCHAR(1024),
    "speaker_id" VARCHAR(32),
    "conversation_id" UUID NOT NULL REFERENCES "conversations" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "license_keys" (
    "id" UUID NOT NULL PRIMARY KEY,
    "key_hash" VARCHAR(64) NOT NULL UNIQUE,
    "key_type" VARCHAR(16) NOT NULL DEFAULT 'paid',
    "expires_at" TIMESTAMPTZ,
    "is_used" BOOL NOT NULL DEFAULT False,
    "used_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "used_by_id" UUID REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_license_key_key_has_ad953a" ON "license_keys" ("key_hash");
COMMENT ON TABLE "license_keys" IS '购买 / 升级的兑换密钥。只存 hash，不存明文。';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "L4HwIgXFg="
)
