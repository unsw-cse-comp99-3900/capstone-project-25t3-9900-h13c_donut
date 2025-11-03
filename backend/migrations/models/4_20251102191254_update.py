from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
COMMENT ON TABLE "license_keys" IS '购买 / 升级的兑换密钥。只存 hash，不存明文。';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "license_keys";"""


MODELS_STATE = (
    "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"
)
