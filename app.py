"""Streamlit UI for Memorizer."""
import streamlit as st
import json
from datetime import datetime
from uuid import uuid4

from models import Memory, MemoryCreate, MemorySearchRequest, RelationshipType
from services import get_storage_service, get_llm_service
from config import settings

# Page config
st.set_page_config(
    page_title="Memorizer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services."""
    return get_storage_service(), get_llm_service()

storage, llm = get_services()


# Sidebar
with st.sidebar:
    st.title("🧠 Memorizer")
    st.caption(f"Version {settings.app_version}")

    st.divider()

    page = st.radio(
        "Navigation",
        ["🔍 Search", "➕ Add Memory", "📊 Statistics", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.divider()

    # Quick stats
    stats = storage.get_stats()
    st.metric("Total Memories", stats.total_memories)
    st.metric("Unique Tags", stats.unique_tags)
    st.metric("Relationships", stats.total_relationships)


# Main content area
if page == "🔍 Search":
    st.header("Search Memories")

    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Search query",
            placeholder="Enter your search query...",
            label_visibility="collapsed"
        )
    with col2:
        limit = st.number_input("Results", min_value=1, max_value=50, value=10)

    # Tag filter
    all_memories = storage.list_all(limit=1000)
    all_tags = sorted(set(tag for m in all_memories for tag in m.tags))
    selected_tags = st.multiselect("Filter by tags", all_tags)

    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if query:
            with st.spinner("Searching..."):
                results = storage.search(
                    query=query,
                    limit=limit,
                    tags=selected_tags if selected_tags else None
                )

                st.success(f"Found {len(results)} memories")

                # Display results
                for idx, memory in enumerate(results):
                    with st.expander(
                        f"**{memory.title or 'Untitled'}** "
                        f"(Similarity: {memory.similarity:.2%})",
                        expanded=(idx == 0)
                    ):
                        # Memory details
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"**Type:** {memory.type}")
                        with col2:
                            st.caption(f"**Source:** {memory.source}")
                        with col3:
                            st.caption(f"**Confidence:** {memory.confidence:.2%}")

                        # Tags
                        if memory.tags:
                            st.caption("**Tags:** " + ", ".join([f"`{tag}`" for tag in memory.tags]))

                        # Content
                        st.caption("**Content:**")
                        st.json(memory.content, expanded=False)

                        # Text preview
                        if memory.text:
                            st.caption("**Text Preview:**")
                            st.text_area(
                                "Text",
                                memory.text[:500] + ("..." if len(memory.text) > 500 else ""),
                                height=100,
                                disabled=True,
                                label_visibility="collapsed"
                            )

                        # Metadata
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption(f"**Created:** {memory.created_at.strftime('%Y-%m-%d %H:%M')}")
                        with col2:
                            st.caption(f"**Updated:** {memory.updated_at.strftime('%Y-%m-%d %H:%M')}")

                        # Actions
                        st.divider()
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("🗑️ Delete", key=f"delete_{memory.id}"):
                                if storage.delete(memory.id):
                                    st.success("Memory deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete memory")
                        with col2:
                            st.caption(f"ID: `{memory.id}`")

        else:
            st.warning("Please enter a search query")

    # Recent memories
    st.divider()
    st.subheader("Recent Memories")

    recent = storage.list_all(limit=10)
    for memory in recent:
        with st.expander(f"{memory.title or 'Untitled'} - {memory.type}"):
            st.caption(f"**Source:** {memory.source}")
            if memory.tags:
                st.caption("**Tags:** " + ", ".join([f"`{tag}`" for tag in memory.tags]))
            st.json(memory.content, expanded=False)


elif page == "➕ Add Memory":
    st.header("Add New Memory")

    with st.form("add_memory_form"):
        # Basic fields
        col1, col2 = st.columns(2)
        with col1:
            memory_type = st.text_input("Type*", placeholder="e.g., note, document, code")
        with col2:
            source = st.text_input("Source*", placeholder="e.g., user-input, api, file")

        title = st.text_input("Title (optional)", placeholder="Leave empty for auto-generation")

        # Content
        st.caption("**Content (JSON format):**")
        content_input = st.text_area(
            "Content",
            height=200,
            placeholder='{"key": "value", "description": "Your content here"}',
            label_visibility="collapsed"
        )

        # Tags
        tags_input = st.text_input(
            "Tags (comma-separated)",
            placeholder="tag1, tag2, tag3"
        )

        # Confidence
        confidence = st.slider("Confidence", 0.0, 1.0, 1.0, 0.1)

        # Submit button
        submitted = st.form_submit_button("💾 Save Memory", type="primary", use_container_width=True)

        if submitted:
            # Validation
            errors = []
            if not memory_type:
                errors.append("Type is required")
            if not source:
                errors.append("Source is required")
            if not content_input:
                errors.append("Content is required")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    # Parse content
                    try:
                        content = json.loads(content_input)
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format in content")
                        st.stop()

                    # Parse tags
                    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

                    # Create memory
                    memory = Memory(
                        type=memory_type,
                        content=content,
                        source=source,
                        tags=tags,
                        confidence=confidence,
                        title=title if title else None
                    )

                    # Save to storage
                    created = storage.create(memory)

                    # Generate title if not provided
                    if not title and llm.is_available():
                        with st.spinner("Generating title..."):
                            generated_title = llm.generate_title(created.text or str(content))
                            if generated_title:
                                storage.update(created.id, {'title': generated_title})
                                created.title = generated_title

                    st.success(f"✅ Memory created successfully!")
                    st.info(f"**ID:** `{created.id}`")
                    if created.title:
                        st.info(f"**Title:** {created.title}")

                    # Clear form (workaround)
                    st.balloons()

                except Exception as e:
                    st.error(f"Error creating memory: {e}")


elif page == "📊 Statistics":
    st.header("Memory System Statistics")

    stats = storage.get_stats()

    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Memories", stats.total_memories)
    with col2:
        st.metric("With Titles", stats.memories_with_titles)
    with col3:
        st.metric("Without Titles", stats.memories_without_titles)
    with col4:
        st.metric("Relationships", stats.total_relationships)

    st.divider()

    # Secondary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Unique Tags", stats.unique_tags)
    with col2:
        st.metric("Unique Types", stats.unique_types)
    with col3:
        st.metric("Avg Confidence", f"{stats.avg_confidence:.2%}")
    with col4:
        st.metric("LLM Status", "✅ Available" if llm.is_available() else "❌ Unavailable")

    st.divider()

    # Dates
    if stats.oldest_memory and stats.newest_memory:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Oldest Memory", stats.oldest_memory.strftime('%Y-%m-%d'))
        with col2:
            st.metric("Newest Memory", stats.newest_memory.strftime('%Y-%m-%d'))

    st.divider()

    # Tag distribution
    st.subheader("Tag Distribution")
    all_memories = storage.list_all(limit=1000)
    tag_counts = {}
    for memory in all_memories:
        for tag in memory.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if tag_counts:
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        st.bar_chart({tag: count for tag, count in sorted_tags})
    else:
        st.info("No tags found")

    # Type distribution
    st.subheader("Type Distribution")
    type_counts = {}
    for memory in all_memories:
        type_counts[memory.type] = type_counts.get(memory.type, 0) + 1

    if type_counts:
        st.bar_chart(type_counts)
    else:
        st.info("No memories found")


elif page == "⚙️ Settings":
    st.header("System Settings")

    st.subheader("Configuration")

    # Display current configuration
    config_data = {
        "App Name": settings.app_name,
        "Version": settings.app_version,
        "Environment": settings.environment,
        "Embedding Model": settings.embedding_model,
        "Embedding Dimension": settings.embedding_dimension,
        "LLM Model Path": settings.llm_model_path,
        "LLM Available": "Yes" if llm.is_available() else "No",
        "Search Limit": settings.search_limit,
        "Similarity Threshold": f"{settings.similarity_threshold:.2%}",
        "Fallback Threshold": f"{settings.fallback_threshold:.2%}",
        "Tag Boost": f"{settings.tag_boost:.2%}",
    }

    for key, value in config_data.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.caption(f"**{key}:**")
        with col2:
            st.text(str(value))

    st.divider()

    st.subheader("System Actions")

    # Generate titles for untitled memories
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🤖 Generate Titles", type="primary", use_container_width=True):
            if not llm.is_available():
                st.error("LLM is not available. Cannot generate titles.")
            else:
                all_memories = storage.list_all(limit=1000)
                untitled = [m for m in all_memories if not m.title]

                if not untitled:
                    st.info("All memories have titles!")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for idx, memory in enumerate(untitled):
                        status_text.text(f"Generating title {idx + 1}/{len(untitled)}...")
                        progress_bar.progress((idx + 1) / len(untitled))

                        try:
                            title = llm.generate_title(memory.text or str(memory.content))
                            if title:
                                storage.update(memory.id, {'title': title})
                        except Exception as e:
                            st.warning(f"Failed to generate title for {memory.id}: {e}")

                    status_text.text("Done!")
                    st.success(f"Generated titles for {len(untitled)} memories!")
                    st.rerun()

    with col2:
        st.caption("Generate titles for all memories that don't have one using the LLM")

    st.divider()

    # Database info
    st.subheader("Storage Information")
    st.caption(f"**ChromaDB Path:** `{settings.chroma_dir}`")
    st.caption(f"**Models Path:** `{settings.models_dir}`")
    st.caption(f"**Data Path:** `{settings.data_dir}`")


# Footer
st.divider()
st.caption(f"Memorizer v{settings.app_version} - Self-contained memory system with vector search")
