import os
from dotenv import dotenv_values

# Read .env directly (without relying on load_dotenv)
env_values = dotenv_values(".env")
print("dotenv_values:", env_values)

# Now load and test os.getenv
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", encoding="utf-8")
print("os.getenv:", os.getenv("TRANSPORTSTACK_API_KEY"))


