from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "transcripts" RENAME TO "transcript";
        ALTER TABLE "transcript" ALTER COLUMN "audio_url" TYPE VARCHAR(1024) USING "audio_url"::VARCHAR(1024);
        ALTER TABLE "transcript" ALTER COLUMN "is_final" DROP DEFAULT;
        ALTER TABLE "transcript" ALTER COLUMN "start_ms" TYPE BIGINT USING "start_ms"::BIGINT;
        ALTER TABLE "transcript" ALTER COLUMN "end_ms" TYPE BIGINT USING "end_ms"::BIGINT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "transcript" RENAME TO "transcripts";
        ALTER TABLE "transcript" ALTER COLUMN "audio_url" TYPE TEXT USING "audio_url"::TEXT;
        ALTER TABLE "transcript" ALTER COLUMN "is_final" SET DEFAULT True;
        ALTER TABLE "transcript" ALTER COLUMN "start_ms" TYPE INT USING "start_ms"::INT;
        ALTER TABLE "transcript" ALTER COLUMN "end_ms" TYPE INT USING "end_ms"::INT;"""


MODELS_STATE = (
    "eJztmm1v4jgQgP8Kyqeu1KsgQMutVicBpbvctnBqw91qV6vIJAasJg5NnGtRxX8/23lPnB"
    "xhKU0kvrQwnknsZyaeGYdXybR0aDgXMwfa0sfGq4SBCemHhPy8IYH1OpIyAQFzgyu6VINL"
    "wNwhNtAIFS6A4UAq0qGj2WhNkIWpFLuGwYSWRhURXkYiF6MnF6rEWkKy4hP58ZOKEdbhC3"
    "SCr+tHdYGgoSfmiXR2by5XyWbNZbPZ+PqGa7LbzVXNMlwTR9rrDVlZOFR3XaRfMBs2toQY"
    "2oBAPbYMNkt/uYHImzEVENuF4VT1SKDDBXANBkP6tHCxxhg0+J3Yn84fUgk8moUZWoQJY/"
    "G69VYVrZlLJXar4Zf+/Vn78gNfpeWQpc0HORFpyw0BAZ4p5xqBZH7knzM4hytgi3HGbVJQ"
    "6YTfBmeAaT92kgleVAPiJVnRr3L3sgDm3/17zpNqcaAWjW4v5if+kOyNMbARSGgCZJShGB"
    "rshdAHFBIMVCKE0dNYG4Zr4DjPlq2rK+CsyrDMGB4mLI8PtbsT1G4B1G4aqm0ZpZ7uQP94"
    "CPmG8gs7YxJia5fAbOXHZSsTlpoN2YpVQLIcr+kIQSYUs0xapojqvulF8KGiIUrXoE+xsf"
    "F3nQK6yvhu9KD07/5iKzEd58ngiPrKiI3IXLpJSc/Snggv0vhnrHxpsK+N79PJKJ3cQj3l"
    "u8TmBFxiqdh6VoEeyyCBNACzZSXF4jGWC5lgDrTHZ0D3j8RILAIs/C+tdwBj52SDYOCb33"
    "y9hwZXErjbL62GsUtV0+HbIIoDaeB4RsqSrTx22SFTNtMSgMGSz5rdm91JhEVQkaax5Vem"
    "GV+dKtRaV6gEkXIJLDSoZWHVknu75C+5l5/A2FgygwFNg1iQvfIhRhb1LKV2gZiPMAOQ7z"
    "Nl+IUGRyyjFjaEFS6jHALs/cqopOWpjKpAGZVofSm0fdwatzuAU4+/c9fEh8GyC52ouzYv"
    "mVQHallHjjER+zBtlvIj8nJI5TxHZ0T//Sa3OledXvuy06MqfCqh5KrAueOJktrbWAerli"
    "v5YiaHrPveNer/p8zL9F5JgFl6N5YN0RJ/hRvOcEznAbAmKu5SB9eVpZbpqqjYBs9hAxEP"
    "C7o8uihIvFKj/zDsX4+k7S79Kr0D9mb5i92qEl6oXlTftFeNQRF0qklk+X0qSepVpknN3e"
    "qFe5Vgg/ej+l3P+w+yvef3pA58KgHO194rNb5HpXrg3IgcqoiBoH0aWJYBAc4Jt5hZCt2c"
    "2lWTXQGYwXR6mygGB2Ml1TzN7gYj2lTx9EmVkLfzZ4nyfkg1RXs7WuaHYcyqXmXa77Lcbl"
    "/JzfZlr9u5uur2mmFMZoeKgnMw/sxoJqhn8dK+pDTcyOaEtgAtgS+CNlGh0pyzPF+/LodQ"
    "RR3h6JuSeP6Ds5Kzu/63D4mG8HY6+Ryox7aH4e10kD7Yc3Vkqa5d6mwqYVTPQ9Km3NnleI"
    "qq5R9Q8cHUm77Yu4OS7ZzA9NTWJagcoL2r78uz81SbJwiXsu3eW7Y4fWgjbSUJ2ht/5Lyo"
    "tQGRzqmtqVxlnt/WsIgUPqj5uSRmUpccfYTf3LBHo0xC9tTrCbDVbO6UipsFmbgpSMRE+M"
    "byz4fpJDcBE/EryxmmC/yhI42cNwzkkJ/VxFpAka26uHZMl4mpTM0uMBCl6mOml+1/sl9C"
    "vw=="
)
