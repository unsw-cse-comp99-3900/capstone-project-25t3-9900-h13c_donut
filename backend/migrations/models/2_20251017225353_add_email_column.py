from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD "email" VARCHAR(256);
        ALTER TABLE "transcripts" ADD "audio_url" TEXT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" DROP COLUMN "email";
        ALTER TABLE "transcripts" DROP COLUMN "audio_url";"""


MODELS_STATE = (
    "eJztmv9v2joQwP8VlJ86qasKa7vqaZoElG5sLTy14b1p0xSZxIDVxKaJ81pU8b8/2/nuOB"
    "lhlCZaf2nhfJfYn7v47hyeNIdY0PaOJh50tb9aTxoGDmQfMvLDlgaWy0TKBRRMbaHoMw0h"
    "AVOPusCkTDgDtgeZyIKe6aIlRQQzKfZtmwuJyRQRniciH6N7HxqUzCFdiIn8+MnECFvwEX"
    "rR1+WdMUPQtjLzRBa/t5AbdLUUsslkeHEpNPntpoZJbN/BifZyRRcEx+q+j6wjbsPH5hBD"
    "F1BopZbBZxkuNxIFM2YC6vownqqVCCw4A77NYWgfZj42OYOWuBP/c/JRq4DHJJijRZhyFk"
    "/rYFXJmoVU47fqf+7eHLw7eyNWSTw6d8WgIKKthSGgIDAVXBOQ3I/icw5nfwFcNc60jQSV"
    "Tfh5cEaYtmOnOeDRsCGe0wX72jk9K4H5T/dG8GRaAihh0R3E/Cgc6gRjHGwCEjoA2VUoxg"
    "ZbIQwBxQQjlQRh8jQ2huESeN4DcS1jAbxFFZY5w92E5f6hnm4E9bQE6qkM1SV2pac70t8f"
    "QrGh/MbOmIXY3iQw28Vx2c6FpelCvmID0DzHCzZCkQPVLLOWElErND2KPtQ0RNkarDG2V+"
    "GuU0JXH14PbvXu9d98JY7n3dsCUVcf8JGOkK4k6YHsifgirX+H+ucW/9r6Ph4N5OQW6+nf"
    "NT4n4FNiYPJgACuVQSJpBGbNS4rZXSoXcsEUmHcPgO0fmZFUBBD8H6t3AGfn5YOgF5pffr"
    "2BtlBSuDssrfqpS9XT4esoiiNp5HhOinRIEbv8kNNxZAnAYC5mze/N76TCoqhIZWzFlWnO"
    "V68VaqMrVIpotQQWGzSysGp3zjfJX53z4gTGx7IZDJgmxIrsVQwxsWhmKbUJxGKEOYBin6"
    "nCLzbYYxk1cyGscRnlUeBuV0ZlLV/LqBqUUZnWl0Hbxq1pux04df87d0N8GC271ImW74qS"
    "yfCgmXfkEFO1D2UzyY8oyCG18xybEfv3ttM+eX9y/u7s5JypiKnEkvclzh2OdGlv4x2sUa"
    "3kS5nssu570aj/RZmX672yAPP0LokL0Rx/hSvBcMjmAbCpKu6kg+vaUst1VUzsgoe4gUiH"
    "BVseWxSkQanRve13LwbaepN+ld0BB7P8zW5Vjy/ULKrP2qumoCg61Syy4j5V8lF9utTCvV"
    "65WSl2+DCsX/TAfyf7e3FT6sH7CuBC7a1y40uUqjtOjshjihgo+qceITYEuCDcUmYSuimz"
    "ey52cSTuOjn2xuOrTDXYG+pS9zS57g1YVyXyJ1NCwdafJyoaIsNRbO7FMZgy+UOLNNZvVG"
    "OWGPyhxCh8VHR1OpMWHL2F+k05Mypr4Abf9MzTGh1tHFx3v73J9G9X49GnSD31MPevxj35"
    "HM63EDF8V7EVFkPNGDXkTHPfYNOH/hX7MIXpaz+WobKDvqy5b70Opf5MES5V+7Tn7E260E"
    "XmQlP0JeHIYVlPAhKd13akdnm5uB3hEal8UItfUKRMmpKt9/BjGf5oVIAYqjcTYPv4eJNX"
    "PMfHxe94+FguEVPlq8Yvt+NRYQKm6neNE8wW+MNCJj1s2cijP+uJtYQiX3V5sSPXNVKm5h"
    "foqVL1PtPL+n+UODI8"
)
