"""FastAPI backend for REST API and MCP server."""
import logging
from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from models import (
    Memory,
    MemoryCreate,
    MemoryUpdate,
    MemorySearchRequest,
    MemorySearchResponse,
    RelationshipCreate,
    MemoryStats
)
from services import get_storage_service, get_llm_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background scheduler
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Memorizer API...")

    # Start background jobs if enabled
    if settings.enable_background_jobs:
        scheduler.add_job(
            generate_missing_titles,
            'interval',
            minutes=30,
            id='title_generation'
        )
        scheduler.start()
        logger.info("Background jobs started")

    yield

    # Shutdown
    if settings.enable_background_jobs:
        scheduler.shutdown()
        logger.info("Background jobs stopped")

    logger.info("Memorizer API stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Self-contained memory system with vector search and LLM capabilities",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Background job functions
def generate_missing_titles():
    """Background job to generate titles for memories without titles."""
    logger.info("Running title generation job...")
    storage = get_storage_service()
    llm = get_llm_service()

    if not llm.is_available():
        logger.warning("LLM not available, skipping title generation")
        return

    # Get memories without titles
    all_memories = storage.list_all(limit=1000)
    untitled = [m for m in all_memories if not m.title]

    logger.info(f"Found {len(untitled)} memories without titles")

    # Process in batches
    batch_size = settings.title_generation_batch_size
    for i in range(0, len(untitled), batch_size):
        batch = untitled[i:i + batch_size]

        for memory in batch:
            try:
                title = llm.generate_title(memory.text or str(memory.content))
                if title:
                    storage.update(memory.id, {'title': title})
                    logger.info(f"Generated title for {memory.id}: {title}")
            except Exception as e:
                logger.error(f"Error generating title for {memory.id}: {e}")

    logger.info("Title generation job completed")


# Health check
@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


# Statistics
@app.get("/api/stats", response_model=MemoryStats)
async def get_stats():
    """Get memory system statistics."""
    storage = get_storage_service()
    return storage.get_stats()


# Memory CRUD endpoints
@app.post("/api/memories", response_model=Memory, status_code=201)
async def create_memory(memory_create: MemoryCreate, background_tasks: BackgroundTasks):
    """Create a new memory."""
    try:
        storage = get_storage_service()

        # Create memory object
        memory = Memory(
            type=memory_create.type,
            content=memory_create.content,
            source=memory_create.source,
            tags=memory_create.tags,
            confidence=memory_create.confidence,
            title=memory_create.title
        )

        # Store memory
        created_memory = storage.create(memory)

        # Create relationships if provided
        for rel_data in memory_create.relationships:
            relationship = RelationshipCreate(**rel_data)
            storage.create_relationship(relationship)

        # Generate title in background if not provided
        if not memory_create.title:
            background_tasks.add_task(generate_title_for_memory, created_memory.id)

        return created_memory

    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_title_for_memory(memory_id: UUID):
    """Background task to generate title for a memory."""
    try:
        storage = get_storage_service()
        llm = get_llm_service()

        memory = storage.get(memory_id)
        if not memory or memory.title:
            return

        title = llm.generate_title(memory.text or str(memory.content))
        if title:
            storage.update(memory_id, {'title': title})
            logger.info(f"Generated title for {memory_id}: {title}")

    except Exception as e:
        logger.error(f"Error in background title generation for {memory_id}: {e}")


@app.get("/api/memories/{memory_id}", response_model=Memory)
async def get_memory(memory_id: UUID):
    """Get a memory by ID."""
    storage = get_storage_service()
    memory = storage.get(memory_id)

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    return memory


@app.get("/api/memories", response_model=list[Memory])
async def list_memories(limit: int = 100, offset: int = 0):
    """List all memories with pagination."""
    if limit > settings.search_max_limit:
        limit = settings.search_max_limit

    storage = get_storage_service()
    return storage.list_all(limit=limit, offset=offset)


@app.put("/api/memories/{memory_id}", response_model=Memory)
async def update_memory(memory_id: UUID, memory_update: MemoryUpdate):
    """Update a memory."""
    storage = get_storage_service()

    updates = memory_update.model_dump(exclude_unset=True)
    updated_memory = storage.update(memory_id, updates)

    if not updated_memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    return updated_memory


@app.delete("/api/memories/{memory_id}", status_code=204)
async def delete_memory(memory_id: UUID):
    """Delete a memory."""
    storage = get_storage_service()

    if not storage.delete(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")

    return None


# Search endpoint
@app.post("/api/search", response_model=MemorySearchResponse)
async def search_memories(search_request: MemorySearchRequest):
    """Search memories using semantic similarity."""
    storage = get_storage_service()

    limit = min(search_request.limit, settings.search_max_limit)

    memories = storage.search(
        query=search_request.query,
        limit=limit,
        tags=search_request.tags if search_request.tags else None
    )

    # Load relationships if requested
    if search_request.include_relationships:
        for memory in memories:
            memory.relationships = storage.get_relationships(memory.id)

    return MemorySearchResponse(
        memories=memories,
        total=len(memories),
        query=search_request.query
    )


# Relationship endpoints
@app.post("/api/relationships", response_model=dict, status_code=201)
async def create_relationship(relationship: RelationshipCreate):
    """Create a relationship between memories."""
    storage = get_storage_service()

    # Verify both memories exist
    if not storage.get(relationship.from_memory_id):
        raise HTTPException(status_code=404, detail="Source memory not found")
    if not storage.get(relationship.to_memory_id):
        raise HTTPException(status_code=404, detail="Target memory not found")

    created = storage.create_relationship(relationship)
    return {"id": str(created.id), "message": "Relationship created"}


@app.get("/api/memories/{memory_id}/relationships")
async def get_memory_relationships(memory_id: UUID):
    """Get relationships for a memory."""
    storage = get_storage_service()

    memory = storage.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    relationships = storage.get_relationships(memory_id)
    return {"relationships": relationships}


# Configuration endpoint
@app.get("/api/config")
async def get_config():
    """Get system configuration."""
    llm = get_llm_service()

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "embedding_model": settings.embedding_model,
        "embedding_dimension": settings.embedding_dimension,
        "llm_available": llm.is_available(),
        "search_limit": settings.search_limit,
        "similarity_threshold": settings.similarity_threshold
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
