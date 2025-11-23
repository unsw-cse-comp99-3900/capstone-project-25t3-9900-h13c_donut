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
    "prefix" VARCHAR(8),
    "suffix_last4" VARCHAR(4),
    "expires_at" TIMESTAMPTZ,
    "is_used" BOOL NOT NULL DEFAULT False,
    "used_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "used_by_id" UUID REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_license_key_key_has_ad953a" ON "license_keys" ("key_hash");
COMMENT ON TABLE "license_keys" IS '购买 / 升级的兑换密钥。';
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
)
