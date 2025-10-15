from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "username" VARCHAR(256) NOT NULL UNIQUE,
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
    "is_final" BOOL NOT NULL DEFAULT True,
    "start_ms" INT,
    "end_ms" INT,
    "text" TEXT NOT NULL,
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
    "eJztmm1v4jgQgP8Kyqeu1KsK23ar02oloPSW2xZObbhb7WoVmcSA1WDT2LkWVfz3s513x8"
    "kRFmjQ9ksL45nEfmbsmUl4MebEgS49GVHoGb83XgwM5pB/yMiPGwZYLBKpEDAwdqWizzWk"
    "BIwp84DNuHACXAq5yIHU9tCCIYK5FPuuK4TE5ooITxORj9GjDy1GppDN5ES+/+BihB34DG"
    "n0dfFgTRB0ncw8kSPuLeUWWy6kbDTqX11LTXG7sWUT15/jRHuxZDOCY3XfR86JsBFjU4ih"
    "Bxh0UssQswyXG4mCGXMB83wYT9VJBA6cAN8VMIyPEx/bgkFD3kn8OftkVMBjEyzQIswEi5"
    "dVsKpkzVJqiFt1P7fvjt5fvJOrJJRNPTkoiRgraQgYCEwl1wSk8KP8nMPZnQFPjzNto0Dl"
    "E94NzgjTZuyMOXi2XIinbMa/ts4vSmD+3b6TPLmWBEp4dAcxPwiHWsGYAJuAXABKn4jnWD"
    "NAZ1Vo5gy3gzQSJEyT7bkbqOdrQT0vgXquQvWIWykyI/39IZSb4Sd2dRZic53AbBbHZTMX"
    "lrYHxYotwPIcr/gIQ3OoZ5m1VIg6oelJ9KGmIcrX4AyxuwyPlBK6Zv+2d2+2b/8SK5lT+u"
    "hKRG2zJ0ZaUrpUpEeqJ+KLNP7pm58b4mvj23DQUw/mWM/8Zog5AZ8RC5MnCzip0y+SRmBW"
    "Ih1OHlLnuBCMgf3wBPj5kRlJRQDB//JcDQQ7mg+CTmh+/eUOulJJ4+6wLOimLlVPh6+iKI"
    "6kkeMFKdIiRezyQ/PWXJUADKZy1uLe4k46LJpqSsVWXFXlfPVWXR10dcUQq5bAYoONMliI"
    "6dVqgGbrcp381bosTmBiLJvBgG1DrMlexRATi8MspdaBWIwwB1CeM1X4xQZ7LKMmHoQ1Lq"
    "MoA95mZVTW8q2MqkEZlXYs5NA2cWvabgtO3f/JfSA+jJZd6kTH92TJZFFo5x3Zx0zvQ9VM"
    "8SMKckjtPMdnxP/91mqefTi7fH9xdslV5FRiyYcS5/YHpnK2iQ7WqlbypUy2Wfe9atT/T5"
    "mX672yAPP0rokH0RR/gUvJsM/nAbCtK+6Uh661pZbrqrjYA09xA5EOC748vijIglKjfd9t"
    "X/WM1Tr9Kr8DDmb5k92qGV/osKjutFdNQdF0qllkxX2q4qP6dKmFZ732sNKc8GFYv+rD6q"
    "2c78VNKYWPFcCF2hvlxtcoVbecHBHlihho+qcOIS4EuCDcUmYKujG32xW7OBK3nRw7w+FN"
    "phrs9E2lexrddnq8q5L5kyuh4OjPE5UNkTXXHO7FMZgy+UWLNN5vVGOWGPyixBh81nR1Jp"
    "cWPHoL9Q/lmVFZA9f7amZ2a/Ro4+i2/fVdpn+7GQ7+iNRTm7l7M+yob5JSz6Yrtgsa07e2"
    "IUNlC+3D4b6cOVbaCE24VG0ndllCt6GH7JmhKZ/DkdLSGSQ6b1Vz7dJHcdUsIlK7UYufo6"
    "dMDiWp7OE3HWJrVIAYqh8mwObp6TpvIk5Pi19FiLFcImbaN2J/3g8HhQmY6V+JjTBf4HcH"
    "2ey44SLKftQTawlFseryYketa5RMLS7Q0aXqfaaX1X88+V3Y"
)
