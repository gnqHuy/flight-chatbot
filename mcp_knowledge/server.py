# mcp_knowledge/server.py
from constants import mcp, logger, HOST, PORT

import tools

from utils.database import init_db

init_db()

if __name__ == "__main__":
    logger.info(f"🚀 Starting KnowledgeServer at http://{HOST}:{PORT}/sse")
    
    mcp.run(transport="sse")