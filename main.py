import os
from dotenv import load_dotenv
from modules.core import Bot


if __name__ == "__main__":
    load_dotenv()
    Bot(owner_id=int(os.getenv("OWNER_ID"))).run(os.getenv("TOKEN"))
