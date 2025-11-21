"""MCP (Model Context Protocol) Server for Memorizer.

This allows AI assistants like Claude to store and retrieve memories.
"""
import asyncio
import logging
from typing import Any
from uuid import UUID
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from models import Memory, MemoryCreate, RelationshipCreate, RelationshipType
from services import get_storage_service, get_llm_service
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
storage = get_storage_service()
llm = get_llm_service()

# Create MCP server
app = Server("memorizer")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="store",
            description=(
                "Store a new memory in the database, optionally creating a relationship to another memory. "
                "Use this to save reference material, how-to guides, coding standards, or any information "
                "you (the LLM) may want to refer to when completing tasks. Include as much context as possible, "
                "such as markdown, code samples, and detailed explanations. Create relationships to link related "
                "reference materials or examples."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "The type of memory (e.g., 'conversation', 'document', 'reference', 'how-to', etc.). Use 'reference' or 'how-to' for reusable knowledge."
                    },
                    "text": {
                        "type": "string",
                        "description": "Plain text (markdown, code, prose, etc.) that you want to store and embed."
                    },
                    "source": {
                        "type": "string",
                        "description": "The source of the memory (e.g., 'user', 'system', 'LLM', etc.). Use 'LLM' if you are storing knowledge for your own future use."
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the memory. This is required and must not be null or empty."
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags to categorize the memory. Use tags like 'coding-standard', 'unit-test', 'reference', 'how-to', etc. to make retrieval easier.",
                        "default": []
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score for the memory (0.0 to 1.0)",
                        "default": 1.0,
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "relatedTo": {
                        "type": "string",
                        "description": "Optionally, the ID of a related memory. Use this to link related reference materials, how-tos, or examples.",
                        "format": "uuid"
                    },
                    "relationshipType": {
                        "type": "string",
                        "description": "Optionally, the type of relationship to create (e.g., 'example-of', 'explains', 'related-to'). Use relationships to connect related knowledge.",
                        "enum": ["related-to", "example-of", "explains", "contradicts", "depends-on", "supersedes"]
                    },
                    "eventDate": {
                        "type": "string",
                        "description": "Optional ISO 8601 date string (YYYY-MM-DD) for when this event/memory occurred. Use for tracking daily status, progress over time, or temporal comparisons.",
                        "format": "date"
                    }
                },
                "required": ["type", "text", "source", "title"]
            }
        ),
        Tool(
            name="search",
            description=(
                "Search for memories similar to the provided text. Use this to retrieve reference material, "
                "how-tos, or examples relevant to the current task. Filtering by tags can help narrow down "
                "to specific types of knowledge."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The text to search for similar memories. Use natural language queries that are close to the expected content. Include key terms and context from the user's question. For example, if the user asks 'what is my name', search for 'user name' or 'my name', not just 'name'."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "minSimilarity": {
                        "type": "number",
                        "description": "Minimum similarity threshold (0.0 to 1.0). Use 0.6-0.7 for general queries. Lower values (0.4-0.5) work better for short queries or when searching for specific facts. Higher values (0.8+) for very precise matches.",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "filterTags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags to filter memories (e.g., 'reference', 'how-to', 'coding-standard')",
                        "default": []
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get",
            description=(
                "Retrieve a specific memory by ID. Use this to fetch a particular reference, how-to, "
                "or example by its unique identifier."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "The ID of the memory to retrieve. Use this to fetch a specific piece of reference or how-to information."
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_many",
            description=(
                "Fetch multiple memories by their IDs. Use this to retrieve a set of related reference materials, "
                "how-tos, or examples."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "string", "format": "uuid"},
                        "description": "The list of memory IDs to fetch. Use this to retrieve multiple related pieces of knowledge at once."
                    }
                },
                "required": ["ids"]
            }
        ),
        Tool(
            name="delete",
            description=(
                "Delete a memory by ID. Use this to remove outdated or incorrect reference or how-to information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "The ID of the memory to delete. Use this to remove a specific piece of knowledge."
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="create_relationship",
            description=(
                "Create a relationship between two memories. Use this to link related reference materials, "
                "how-tos, or examples (e.g., 'example-of', 'explains', 'related-to'). Relationships help "
                "organize knowledge for easier retrieval and understanding."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fromId": {
                        "type": "string",
                        "format": "uuid",
                        "description": "The ID of the source memory (e.g., the reference or how-to that is providing context)"
                    },
                    "toId": {
                        "type": "string",
                        "format": "uuid",
                        "description": "The ID of the target memory (e.g., the example or related reference)"
                    },
                    "type": {
                        "type": "string",
                        "description": "The type of relationship (e.g., 'example-of', 'explains', 'related-to'). Use relationships to connect and organize knowledge.",
                        "enum": ["related-to", "example-of", "explains", "contradicts", "depends-on", "supersedes"]
                    }
                },
                "required": ["fromId", "toId", "type"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls from the MCP client."""

    try:
        if name == "store":
            return await handle_store(arguments)
        elif name == "search":
            return await handle_search(arguments)
        elif name == "get":
            return await handle_get(arguments)
        elif name == "get_many":
            return await handle_get_many(arguments)
        elif name == "delete":
            return await handle_delete(arguments)
        elif name == "create_relationship":
            return await handle_create_relationship(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_store(args: dict[str, Any]) -> list[TextContent]:
    """Handle the 'store' tool."""
    from datetime import datetime

    # Parse event_date if provided
    event_date = None
    if "eventDate" in args and args["eventDate"]:
        try:
            event_date = datetime.fromisoformat(args["eventDate"])
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid eventDate format: {args['eventDate']}, error: {e}")

    # Create memory
    memory = Memory(
        type=args["type"],
        content={"text": args["text"]},
        text=args["text"],
        source=args["source"],
        title=args["title"],
        tags=args.get("tags", []),
        confidence=args.get("confidence", 1.0),
        event_date=event_date
    )

    # Store in database
    created = storage.create(memory)

    # Handle relationship if specified
    if "relatedTo" in args and "relationshipType" in args:
        try:
            related_id = UUID(args["relatedTo"])
            rel = RelationshipCreate(
                from_memory_id=created.id,
                to_memory_id=related_id,
                type=RelationshipType(args["relationshipType"])
            )
            storage.create_relationship(rel)
        except Exception as e:
            logger.warning(f"Failed to create relationship: {e}")

    result = (
        f"Memory stored successfully with ID: {created.id}\n"
        f"Title: {created.title}\n"
        f"Type: {created.type}\n"
        f"Tags: {', '.join(created.tags)}\n\n"
        f"💡 You might want to call `create_relationship` to associate this memory with another memory for better context retrieval."
    )

    return [TextContent(type="text", text=result)]


async def handle_search(args: dict[str, Any]) -> list[TextContent]:
    """Handle the 'search' tool."""
    query = args["query"]
    limit = args.get("limit", 10)
    min_similarity = args.get("minSimilarity", 0.7)
    filter_tags = args.get("filterTags", [])

    logger.info(f"Search query: {query}, limit: {limit}, threshold: {min_similarity}, tags: {filter_tags}")

    # Search memories with user-specified threshold
    # Storage service handles filtering and fallback
    memories = storage.search(
        query=query,
        limit=limit,
        tags=filter_tags if filter_tags else None,
        threshold=min_similarity,
        use_fallback=True
    )

    if not memories:
        return [TextContent(
            type="text",
            text="No memories found matching your query, even with a relaxed similarity threshold. Try using different search terms or lowering the similarity threshold further."
        )]

    # Format results
    result_lines = [f"Found {len(memories)} memories:", ""]

    # Collect related memory IDs
    related_ids = set()

    for memory in memories:
        result_lines.append(f"ID: {memory.id}")
        if memory.title:
            result_lines.append(f"Title: {memory.title}")
        result_lines.append(f"Type: {memory.type}")
        result_lines.append(f"Text: {memory.text}")
        result_lines.append(f"Source: {memory.source}")
        result_lines.append(f"Tags: {', '.join(memory.tags) if memory.tags else 'none'}")
        result_lines.append(f"Confidence: {memory.confidence:.2f}")

        if memory.similarity:
            percent = 100 * memory.similarity
            result_lines.append(f"Similarity: {percent:.1f}%")

        # List relationships
        if memory.relationships:
            result_lines.append(f"🔗 Relationships ({len(memory.relationships)}):")
            for rel in memory.relationships:
                related_id = rel.to_memory_id if rel.from_memory_id == memory.id else rel.from_memory_id
                direction = "→" if rel.from_memory_id == memory.id else "←"
                result_lines.append(f"  • [{rel.type.upper()}] {direction} [ID: {related_id}]")
                related_ids.add(related_id)

        result_lines.append(f"Created: {memory.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        result_lines.append("")

    # Suggest loading related memories
    if related_ids:
        result_lines.append("💡 Suggestion: These memories have relationships to other memories in the database.")
        result_lines.append(f"Consider using get_many with these IDs to load related context: {list(related_ids)}")
        result_lines.append("This can provide additional relevant information and context for your task.")

    return [TextContent(type="text", text="\n".join(result_lines))]


async def handle_get(args: dict[str, Any]) -> list[TextContent]:
    """Handle the 'get' tool."""
    memory_id = UUID(args["id"])
    memory = storage.get(memory_id)

    if not memory:
        return [TextContent(type="text", text=f"Memory with ID {memory_id} not found.")]

    result_lines = [
        f"ID: {memory.id}",
    ]

    if memory.title:
        result_lines.append(f"Title: {memory.title}")

    result_lines.extend([
        f"Type: {memory.type}",
        f"Text: {memory.text}",
        f"Source: {memory.source}",
        f"Tags: {', '.join(memory.tags) if memory.tags else 'none'}",
        f"Confidence: {memory.confidence:.2f}",
    ])

    # Collect related memory IDs
    related_ids = set()

    # List relationships
    if memory.relationships:
        result_lines.append(f"🔗 Relationships ({len(memory.relationships)}):")
        for rel in memory.relationships:
            related_id = rel.to_memory_id if rel.from_memory_id == memory.id else rel.from_memory_id
            direction = "→" if rel.from_memory_id == memory.id else "←"
            result_lines.append(f"  • [{rel.type.upper()}] {direction} [ID: {related_id}]")
            related_ids.add(related_id)

    result_lines.extend([
        f"Created: {memory.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Updated: {memory.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
    ])

    # Suggest loading related memories
    if related_ids:
        result_lines.extend([
            "",
            "💡 Suggestion: This memory has relationships to other memories in the database.",
            f"Consider using get_many with these IDs to load related context: {list(related_ids)}",
            "This can provide additional relevant information and context for your task."
        ])

    return [TextContent(type="text", text="\n".join(result_lines))]


async def handle_get_many(args: dict[str, Any]) -> list[TextContent]:
    """Handle the 'get_many' tool."""
    ids = [UUID(id_str) for id_str in args["ids"]]

    memories = []
    for memory_id in ids:
        memory = storage.get(memory_id)
        if memory:
            memories.append(memory)

    if not memories:
        return [TextContent(type="text", text="No memories found for the provided IDs.")]

    result_lines = [f"Found {len(memories)} memories:", ""]

    # Collect all related memory IDs
    related_ids = set()

    for memory in memories:
        result_lines.append(f"ID: {memory.id}")
        if memory.title:
            result_lines.append(f"Title: {memory.title}")
        result_lines.extend([
            f"Type: {memory.type}",
            f"Text: {memory.text}",
            f"Source: {memory.source}",
            f"Tags: {', '.join(memory.tags) if memory.tags else 'none'}",
            f"Confidence: {memory.confidence:.2f}",
        ])

        # List relationships
        if memory.relationships:
            result_lines.append(f"🔗 Relationships ({len(memory.relationships)}):")
            for rel in memory.relationships:
                related_id = rel.to_memory_id if rel.from_memory_id == memory.id else rel.from_memory_id
                direction = "→" if rel.from_memory_id == memory.id else "←"
                result_lines.append(f"  • [{rel.type.upper()}] {direction} [ID: {related_id}]")

                # Only add if not already in our fetched list
                if related_id not in ids:
                    related_ids.add(related_id)

        result_lines.append(f"Created: {memory.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        result_lines.append("")

    # Suggest loading related memories
    if related_ids:
        result_lines.extend([
            "💡 Suggestion: These memories have relationships to other memories not included in this result.",
            f"Consider using get_many with these additional IDs to load more related context: {list(related_ids)}",
            "This can provide additional relevant information and context for your task."
        ])

    return [TextContent(type="text", text="\n".join(result_lines))]


async def handle_delete(args: dict[str, Any]) -> list[TextContent]:
    """Handle the 'delete' tool."""
    memory_id = UUID(args["id"])
    success = storage.delete(memory_id)

    if success:
        return [TextContent(type="text", text=f"Memory with ID {memory_id} deleted successfully.")]
    else:
        return [TextContent(type="text", text=f"Memory with ID {memory_id} not found or could not be deleted.")]


async def handle_create_relationship(args: dict[str, Any]) -> list[TextContent]:
    """Handle the 'create_relationship' tool."""
    from_id = UUID(args["fromId"])
    to_id = UUID(args["toId"])
    rel_type = RelationshipType(args["type"])

    # Verify both memories exist
    if not storage.get(from_id):
        return [TextContent(type="text", text=f"Source memory with ID {from_id} not found.")]
    if not storage.get(to_id):
        return [TextContent(type="text", text=f"Target memory with ID {to_id} not found.")]

    # Create relationship
    rel = RelationshipCreate(
        from_memory_id=from_id,
        to_memory_id=to_id,
        type=rel_type
    )

    created = storage.create_relationship(rel)

    return [TextContent(
        type="text",
        text=f"Relationship created: {created.id} from {created.from_memory_id} to {created.to_memory_id} (type: {created.type.value})"
    )]


async def main():
    """Run the MCP server."""
    logger.info("Starting Memorizer MCP server...")
    logger.info(f"Storage: {settings.chroma_dir}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info(f"LLM available: {llm.is_available()}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
