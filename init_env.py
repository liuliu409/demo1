import os

ENV_FILE = ".env"

default_env_content = """# Environment variables for FastAPI Export Service
DATA_DIR=data
TEMP_DIR=temp_exports
"""

def init_env():
    if os.path.exists(ENV_FILE):
        print(f"{ENV_FILE} đã tồn tại.")
        choice = input("Bạn có muốn ghi đè nội dung file .env không? (y/n): ").strip().lower()
        if choice != "y":
            print("Giữ nguyên file .env cũ.")
            return
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(default_env_content)
    print(f"Đã tạo file {ENV_FILE} với nội dung mặc định.")

if __name__ == "__main__":
    init_env()
