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
    "eJztmm1v4jgQgP8Kyqeu1KsgQMutVicBpbvctnBqw91qV6vIJAasBocmzrWo4r+f7bw7To"
    "6wlBKJLy2MZxL7mYlnxuFVWdomtNyLiQsd5WPtVcFgCemHlPy8poDVKpYyAQFTiyt6VINL"
    "wNQlDjAIFc6A5UIqMqFrOGhFkI2pFHuWxYS2QRURnsciD6MnD+rEnkOy4BP58ZOKETbhC3"
    "TDr6tHfYagZabmiUx2by7XyXrFZZPJ8PqGa7LbTXXDtrwljrVXa7KwcaTueci8YDZsbA4x"
    "dACBZmIZbJbBckORP2MqII4Ho6mascCEM+BZDIbyaeZhgzGo8TuxP60/lBJ4DBsztAgTxu"
    "J1468qXjOXKuxW/S/d+7Pm5Qe+Stslc4cPciLKhhsCAnxTzjUGyfzIP2dw9hfAkeNM2ghQ"
    "6YTfBmeIaTd2yhK86BbEc7KgX9X2ZQHMv7v3nCfV4kBtGt1+zI+CIdUfY2BjkHAJkFWGYm"
    "SwE8IAUEQwVIkRxk9jZRiugOs+246pL4C7KMMyY7ifsDw81PZWUNsFUNsiVMe2Sj3dof7h"
    "EPIN5Rd2xjTExjaB2ciPy0YmLA0HshXrgGQ5XtMRgpZQzjJtKRA1A9OL8MORhihdgznG1j"
    "rYdQroasO7wYPWvfuLrWTpuk8WR9TVBmxE5dK1ID0TPRFdpPbPUPtSY19r38ejgZjcIj3t"
    "u8LmBDxi69h+1oGZyCChNASzYSXF7DGRC5lgCozHZ0D3j9RIIgJs/C+tdwBj52aDoBeY33"
    "y9hxZXkrg7KK36iUsdp8M3YRSH0tDxjJSt2nnsskNLdSlKAAZzPmt2b3YnGRZJRSpiy69M"
    "M746VaiVrlAJIuUSWGRQycKqoXa2yV9qJz+BsbF0BgOGAbEke+VDjC2qWUptAzEfYQYg32"
    "fK8IsMDlhGzRwIj7iMcglwdiuj0panMuoIyqhU60uh7eLWpN0enHr4nbsiPgyXXehE03N4"
    "yaS70Mg6coiJ3IeimeBH5OeQo/McnRH995vaaF21Os3LVoeq8KlEkqsC5w5HmrC3sQ5WL1"
    "fyJUz2Wfe9a9T/T5mX6b3SALP0bmwHojn+Ctec4ZDOA2BDVtwJB9dHSy3TVVGxA56jBiIZ"
    "FnR5dFGQ+KVG96HfvR4om236VXoH7M/yF7tVLbpQtai+aa+agCLpVNPI8vtUwUfH06Xm7v"
    "XSzUqywwdh/a4H/nvZ3/ObUhc+lQAXaO+UG9+jVN1zckQuVcRA0j/1bNuCAOeEW8JMQDel"
    "dsfJrgBMbzy+TVWDvaEmdE+Tu96AdlU8f1Il5G/9WaK8IdKXss0dzfPDMGFVrTrtd1VtNq"
    "/UevOy025dXbU79Sgms0NFwdkbfmY0U9SzeGljUhpubHNCW4CWwBdJn6hRac5hXqBflVOo"
    "opZw8E1LPf/hYcnZXffbh1RHeDsefQ7VE9tD/3bcE0/2PBPZuueUOpxKGVXzlLSutrY5n6"
    "Jq+SdUfFDYWFcQPOa0cvk801aVBNpUt8DZVHNhsiHhrWniPUzJ1lhiemqRU1T20CpX90Xk"
    "udAyS8KlbOv8lu1iFzrIWCiSVjEYOS9qE0Gsc+oQ91/+vFmHyCJS+qDmp5GESVXKnQP8fo"
    "k9GmVqG1+9mgAb9fpWVU29oKipSxIxkb79/fNhPMpNwET++neC6QJ/mMgg5zULueTncWIt"
    "oMhWXVyGixW3kKnZBXqyVH3I9LL5D69grS4="
)
