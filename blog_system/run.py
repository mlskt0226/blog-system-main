# run.py (в blog-system-main/)
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blog_system.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)
