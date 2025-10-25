"""Streamlit UI for Memorizer - Styled to match original Bootstrap UI."""
import streamlit as st
import json
from datetime import datetime
from uuid import uuid4

from models import Memory, MemoryCreate, MemorySearchRequest, RelationshipType
from services import get_storage_service, get_llm_service
from config import settings

# Page config - matching original UI
st.set_page_config(
    page_title="Memory Manager - Memorizer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match Bootstrap UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
    }

    /* Sidebar styling to match dark sidebar */
    [data-testid="stSidebar"] {
        background-color: #212529;
    }

    [data-testid="stSidebar"] .element-container {
        color: white;
    }

    /* Memory card styling */
    .memory-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
    }

    .memory-card:hover {
        box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
        transition: box-shadow 0.2s ease-in-out;
    }

    .memory-card-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #212529;
    }

    .memory-card-preview {
        color: #6c757d;
        font-size: 0.875rem;
        margin-bottom: 0.75rem;
        line-height: 1.5;
    }

    .badge {
        display: inline-block;
        padding: 0.35em 0.65em;
        font-size: 0.75em;
        font-weight: 600;
        line-height: 1;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.375rem;
        margin: 0.25rem;
    }

    .badge-primary {
        background-color: #0d6efd;
    }

    .badge-success {
        background-color: #198754;
    }

    .badge-secondary {
        background-color: #6c757d;
    }

    /* Stats card styling */
    .stats-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        padding: 1.5rem;
        text-align: center;
    }

    .stats-value {
        font-size: 2rem;
        font-weight: bold;
        color: #0d6efd;
    }

    .stats-label {
        font-size: 0.875rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Search card styling */
    .search-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }

    /* Button styling to match Bootstrap */
    .stButton button {
        border-radius: 0.375rem;
        font-weight: 500;
    }

    /* Page header */
    .page-header {
        margin-bottom: 2rem;
    }

    .page-title {
        font-size: 1.75rem;
        font-weight: 500;
        color: #212529;
        margin-bottom: 0.25rem;
    }

    .page-subtitle {
        color: #6c757d;
        font-size: 1rem;
    }

    /* Footer styling */
    .footer {
        text-align: center;
        padding: 1.5rem 0;
        margin-top: 3rem;
        border-top: 1px solid #dee2e6;
        color: #6c757d;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services."""
    return get_storage_service(), get_llm_service()

storage, llm = get_services()

# Sidebar - matching original UI structure
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: white; margin-bottom: 0.25rem;">
            🧠 Memorizer
        </h2>
        <p style="color: rgba(255, 255, 255, 0.6); font-size: 0.875rem; margin: 0;">
            Memory Management System
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    page = st.radio(
        "Navigation",
        [
            "📋 All Memories",
            "➕ Create Memory",
            "📊 Statistics",
            "🔧 Tools",
            "⚙️ System Config"
        ],
        label_visibility="collapsed"
    )

    st.markdown('<hr style="border-color: rgba(255, 255, 255, 0.3); margin: 1.5rem 0;">', unsafe_allow_html=True)

    # Quick stats in sidebar
    stats = storage.get_stats()
    st.markdown(f"""
    <div style="text-align: center;">
        <p style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem; margin: 0.5rem 0;">
            <i class="fas fa-database"></i> Total Memories: <strong style="color: white;">{stats.total_memories}</strong>
        </p>
        <p style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem; margin: 0.5rem 0;">
            <i class="fas fa-tags"></i> Unique Tags: <strong style="color: white;">{stats.unique_tags}</strong>
        </p>
        <p style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem; margin: 0.5rem 0;">
            <i class="fas fa-link"></i> Relationships: <strong style="color: white;">{stats.total_relationships}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border-color: rgba(255, 255, 255, 0.3); margin: 1.5rem 0;">', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center;">
        <p style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem;">
            <i class="fas fa-database"></i> ChromaDB + Vector Search
        </p>
    </div>
    """, unsafe_allow_html=True)


# Helper function to display memory card matching Bootstrap style
def display_memory_card(memory, show_similarity=False):
    """Display a memory card matching the original Bootstrap UI style."""

    # Use Streamlit components instead of raw HTML to avoid rendering issues
    with st.container():
        # Card styling
        st.markdown('<div class="memory-card">', unsafe_allow_html=True)

        # Title and type badge
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f'<h6 class="memory-card-title">{memory.title or "Untitled"}</h6>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<span class="badge badge-primary">{memory.type}</span>', unsafe_allow_html=True)

        # Preview text - use st.text to avoid HTML issues
        preview_text = memory.text if memory.text else str(memory.content)
        if len(preview_text) > 200:
            preview_text = preview_text[:200] + "..."
        st.caption(preview_text)

        # Tags
        if memory.tags:
            tags_html = " ".join([f'<span class="badge badge-secondary">{tag}</span>' for tag in memory.tags])
            st.markdown(tags_html, unsafe_allow_html=True)

        # Source and confidence
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"👤 {memory.source}")
        with col2:
            st.caption(f"📊 {memory.confidence:.0%}")

        # Timestamp
        st.caption(f"🕐 {memory.created_at.strftime('%Y-%m-%d %H:%M')}")

        # Similarity
        if show_similarity and memory.similarity:
            st.success(f"Similarity: {memory.similarity:.0%}")

        # ID
        st.caption(f"ID: `{memory.id}`")

        st.markdown('</div>', unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👁️ View", key=f"view_{memory.id}", use_container_width=True):
            st.session_state[f"expanded_{memory.id}"] = True
    with col2:
        if st.button("✏️ Edit", key=f"edit_{memory.id}", use_container_width=True):
            st.info("Edit functionality coming soon")
    with col3:
        if st.button("🗑️ Delete", key=f"delete_{memory.id}", use_container_width=True, type="secondary"):
            if storage.delete(memory.id):
                st.success("Memory deleted!")
                st.rerun()

    # Expandable details
    if st.session_state.get(f"expanded_{memory.id}"):
        with st.expander("Full Details", expanded=True):
            st.json(memory.model_dump(exclude={'embedding', 'embedding_metadata', 'relationships'}), expanded=False)
            if st.button("Close", key=f"close_{memory.id}"):
                st.session_state[f"expanded_{memory.id}"] = False
                st.rerun()


# Main content area
if page == "📋 All Memories":
    # Page header matching original UI
    st.markdown("""
    <div class="page-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 class="page-title">
                    🧠 Memory Manager
                </h1>
                <p class="page-subtitle">Manage your AI agent memories with vector search capabilities</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Vector search card - matching original UI
    st.markdown('<div class="search-card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([5, 2, 2])
    with col1:
        search_query = st.text_input(
            "Vector search",
            placeholder="Vector search memories...",
            label_visibility="collapsed",
            key="vector_search"
        )
    with col2:
        min_similarity = st.number_input(
            "Min similarity",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.01,
            label_visibility="collapsed",
            key="min_sim"
        )
    with col3:
        search_clicked = st.button("🔍 Vector Search", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Search results or recent memories
    if search_clicked and search_query:
        with st.spinner("Searching..."):
            results = storage.search(query=search_query, limit=20)
            # Filter by similarity
            filtered_results = [m for m in results if m.similarity and (1 - m.similarity) >= min_similarity]

            st.success(f"Found {len(filtered_results)} memories")

            # Display in grid layout
            for memory in filtered_results:
                display_memory_card(memory, show_similarity=True)
    else:
        # Page size selector
        st.markdown('<div class="search-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            page_size = st.selectbox(
                "Items per page:",
                [10, 20, 50, 100],
                index=1,
                key="page_size"
            )
        with col2:
            st.markdown(f'<div style="text-align: right; padding-top: 0.5rem;"><span style="color: #6c757d;">Total: {stats.total_memories} memories</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # List all memories
        memories = storage.list_all(limit=page_size)

        st.markdown(f"<h5>Recent Memories ({len(memories)})</h5>", unsafe_allow_html=True)

        for memory in memories:
            display_memory_card(memory, show_similarity=False)

elif page == "➕ Create Memory":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">➕ Create New Memory</h1>
        <p class="page-subtitle">Add a new memory to the system</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="search-card">', unsafe_allow_html=True)

    with st.form("create_memory"):
        col1, col2 = st.columns(2)
        with col1:
            mem_type = st.text_input("Type *", placeholder="e.g., conversation, document, reference")
        with col2:
            source = st.text_input("Source *", placeholder="e.g., user, system, LLM")

        title = st.text_input("Title", placeholder="Leave empty for auto-generation")

        text = st.text_area(
            "Text Content *",
            height=200,
            placeholder="Enter the memory content here..."
        )

        tags_input = st.text_input(
            "Tags (comma-separated)",
            placeholder="tag1, tag2, tag3"
        )

        confidence = st.slider("Confidence", 0.0, 1.0, 1.0, 0.05)

        submitted = st.form_submit_button("💾 Create Memory", type="primary", use_container_width=True)

        if submitted:
            if not mem_type or not source or not text:
                st.error("Type, Source, and Text are required fields")
            else:
                try:
                    tags = [t.strip() for t in tags_input.split(",") if t.strip()]

                    memory = Memory(
                        type=mem_type,
                        content={"text": text},
                        text=text,
                        source=source,
                        title=title if title else None,
                        tags=tags,
                        confidence=confidence
                    )

                    created = storage.create(memory)

                    # Generate title if not provided
                    if not title and llm.is_available():
                        with st.spinner("Generating title..."):
                            gen_title = llm.generate_title(text)
                            if gen_title:
                                storage.update(created.id, {'title': gen_title})
                                created.title = gen_title

                    st.success(f"✅ Memory created successfully!")
                    st.info(f"**ID:** `{created.id}`")
                    if created.title:
                        st.info(f"**Title:** {created.title}")

                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

elif page == "📊 Statistics":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📊 System Statistics</h1>
        <p class="page-subtitle">Overview of memory system metrics</p>
    </div>
    """, unsafe_allow_html=True)

    # Main stats in cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-value">{stats.total_memories}</div>
            <div class="stats-label">Total Memories</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-value">{stats.unique_tags}</div>
            <div class="stats-label">Unique Tags</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-value">{stats.total_relationships}</div>
            <div class="stats-label">Relationships</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-value">{stats.avg_confidence:.0%}</div>
            <div class="stats-label">Avg Confidence</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Secondary stats
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="search-card">', unsafe_allow_html=True)
        st.markdown("### Tag Distribution")
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
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="search-card">', unsafe_allow_html=True)
        st.markdown("### Type Distribution")
        type_counts = {}
        for memory in all_memories:
            type_counts[memory.type] = type_counts.get(memory.type, 0) + 1
        if type_counts:
            st.bar_chart(type_counts)
        else:
            st.info("No memories found")
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "🔧 Tools":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">🔧 Tools</h1>
        <p class="page-subtitle">System maintenance and utilities</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="search-card">', unsafe_allow_html=True)

    st.markdown("### Generate Titles")
    st.caption("Generate titles for all memories that don't have one using the LLM")

    if st.button("🤖 Generate Titles for Untitled Memories", type="primary"):
        if not llm.is_available():
            st.error("LLM is not available")
        else:
            all_memories = storage.list_all(limit=1000)
            untitled = [m for m in all_memories if not m.title]

            if not untitled:
                st.info("All memories already have titles!")
            else:
                progress = st.progress(0)
                status = st.empty()

                for idx, memory in enumerate(untitled):
                    status.text(f"Processing {idx + 1}/{len(untitled)}...")
                    progress.progress((idx + 1) / len(untitled))

                    try:
                        title = llm.generate_title(memory.text or str(memory.content))
                        if title:
                            storage.update(memory.id, {'title': title})
                    except Exception as e:
                        st.warning(f"Failed for {memory.id}: {e}")

                status.text("Done!")
                st.success(f"Generated {len(untitled)} titles!")
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

elif page == "⚙️ System Config":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">⚙️ System Configuration</h1>
        <p class="page-subtitle">View system settings and configuration</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="search-card">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Application Settings")
        st.markdown(f"**App Name:** {settings.app_name}")
        st.markdown(f"**Version:** {settings.app_version}")
        st.markdown(f"**Environment:** {settings.environment}")
        st.markdown(f"**LLM Available:** {'✅ Yes' if llm.is_available() else '❌ No'}")

    with col2:
        st.markdown("### Vector Search Settings")
        st.markdown(f"**Embedding Model:** {settings.embedding_model}")
        st.markdown(f"**Embedding Dimension:** {settings.embedding_dimension}")
        st.markdown(f"**Search Limit:** {settings.search_limit}")
        st.markdown(f"**Similarity Threshold:** {settings.similarity_threshold:.2%}")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="search-card">', unsafe_allow_html=True)
    st.markdown("### Storage Paths")
    st.code(f"ChromaDB: {settings.chroma_dir}", language="text")
    st.code(f"Models: {settings.models_dir}", language="text")
    st.code(f"Data: {settings.data_dir}", language="text")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <div style="margin-bottom: 0.5rem;">
        <small>Made with ❤️ using Python & ChromaDB</small>
    </div>
    <div>
        <small>Memorizer v{version} - Self-contained memory system with vector search</small>
    </div>
</div>
""".format(version=settings.app_version), unsafe_allow_html=True)
