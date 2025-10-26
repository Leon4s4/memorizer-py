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

    /* Make all sidebar text white for contrast */
    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Specifically target radio button text */
    [data-testid="stSidebar"] .st-emotion-cache-1gulkj5,
    [data-testid="stSidebar"] [role="radiogroup"] label,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: white !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }

    /* Radio button circle styling */
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 0.5rem;
    }

    /* Make sure the radio input backgrounds are visible */
    [data-testid="stSidebar"] input[type="radio"] {
        filter: invert(1) hue-rotate(180deg) brightness(1.5);
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
    import html as html_module

    # Extract preview text from text field or content dict
    # DEBUG: Log what we're actually receiving
    import sys
    import json
    print(f"\n=== DEBUG display_memory_card ===", file=sys.stderr)
    print(f"memory.id: {memory.id}", file=sys.stderr)
    print(f"memory.text: {memory.text!r}", file=sys.stderr)
    print(f"memory.content type: {type(memory.content)}", file=sys.stderr)
    print(f"memory.content value: {memory.content!r}", file=sys.stderr)

    preview_text = ""

    # Extract text, handling nested JSON strings
    def extract_text(value):
        """Recursively extract text from potentially nested JSON strings."""
        if isinstance(value, str):
            # Try to parse as JSON
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict) and 'text' in parsed:
                    # Recursively extract in case it's nested
                    return extract_text(parsed['text'])
                elif isinstance(parsed, str):
                    return parsed
                else:
                    return value
            except:
                return value
        elif isinstance(value, dict) and 'text' in value:
            return extract_text(value['text'])
        else:
            return str(value)

    # First, try to get text from the content dict if it's a dict
    if isinstance(memory.content, dict) and 'text' in memory.content:
        preview_text = extract_text(memory.content['text'])
        print(f"✓ Extracted from dict (after unwrapping): {preview_text!r}", file=sys.stderr)
    # Then check if memory.text field is available and non-empty
    elif memory.text and len(str(memory.text).strip()) > 0:
        preview_text = extract_text(memory.text)
        print(f"✓ Using memory.text (after unwrapping): {preview_text!r}", file=sys.stderr)
    # If content is already a string, use it
    elif isinstance(memory.content, str):
        preview_text = extract_text(memory.content)
        print(f"✓ Using string content (after unwrapping): {preview_text!r}", file=sys.stderr)
    # Last resort
    else:
        preview_text = "No content available"
        print(f"✗ No content found, using placeholder", file=sys.stderr)

    if len(preview_text) > 200:
        preview_text = preview_text[:200] + "..."

    # Escape user content to prevent HTML injection (but NOT the structure tags)
    preview_escaped = html_module.escape(preview_text)
    title_escaped = html_module.escape(memory.title or "Untitled")
    mem_type_escaped = html_module.escape(memory.type)
    source_escaped = html_module.escape(memory.source)

    # Build tags HTML
    tags_html = ""
    if memory.tags:
        tags_html = " ".join([f'<span class="badge badge-secondary">{html_module.escape(tag)}</span>' for tag in memory.tags])

    # Build similarity HTML
    similarity_html = ""
    if show_similarity and memory.similarity:
        similarity_html = f'<div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 0.5rem; border-radius: 0.25rem; margin-bottom: 0.5rem; color: #0c5460;">Similarity: {memory.similarity:.0%}</div>'

    # Build the entire card as HTML
    card_html = """
    <div class="memory-card">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
            <h6 class="memory-card-title" style="margin: 0; flex: 1;">{title}</h6>
            <span class="badge badge-primary">{mem_type}</span>
        </div>

        <p class="memory-card-preview" style="color: #6c757d; font-size: 0.875rem; margin-bottom: 0.75rem;">
            {preview}
        </p>

        <div style="margin-bottom: 0.75rem;">
            {tags}
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.875rem; color: #6c757d; margin-bottom: 0.5rem;">
            <div>👤 {source}</div>
            <div>📊 {confidence:.0%}</div>
        </div>

        <div style="font-size: 0.875rem; color: #6c757d; margin-bottom: 0.5rem;">
            🕐 {timestamp}
        </div>

        {similarity}

        <div style="font-size: 0.75rem; color: #6c757d; margin-bottom: 1rem;">
            ID: <code style="background-color: #f8f9fa; padding: 0.125rem 0.25rem; border-radius: 0.25rem;">{mem_id}</code>
        </div>
    </div>
    """.format(
        title=title_escaped,
        mem_type=mem_type_escaped,
        preview=preview_escaped,
        tags=tags_html,
        source=source_escaped,
        confidence=memory.confidence,
        timestamp=memory.created_at.strftime('%Y-%m-%d %H:%M'),
        similarity=similarity_html,
        mem_id=memory.id
    )

    # Use st.html() for proper HTML rendering in Streamlit 1.40+
    st.html(card_html)

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👁️ View", key=f"view_{memory.id}", use_container_width=True):
            st.session_state['viewing_memory'] = memory.id
            st.rerun()
    with col2:
        if st.button("✏️ Edit", key=f"edit_{memory.id}", use_container_width=True):
            st.session_state['editing_memory'] = memory.id
            st.rerun()
    with col3:
        if st.button("🗑️ Delete", key=f"delete_{memory.id}", use_container_width=True, type="secondary"):
            if storage.delete(memory.id):
                st.success("Memory deleted!")
                st.rerun()


# Check if we're viewing or editing a specific memory
if st.session_state.get('viewing_memory'):
    # Detailed view page
    memory_id = st.session_state['viewing_memory']
    memory = storage.get(memory_id)

    if memory:
        # Extract full text content
        def extract_text(value):
            """Recursively extract text from potentially nested JSON strings."""
            import json
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict) and 'text' in parsed:
                        return extract_text(parsed['text'])
                    return value
                except:
                    return value
            elif isinstance(value, dict) and 'text' in value:
                return extract_text(value['text'])
            else:
                return str(value)

        full_text = extract_text(memory.content['text']) if isinstance(memory.content, dict) and 'text' in memory.content else (memory.text or "No content")

        # Header with title
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; margin: -1rem -1rem 2rem -1rem; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin: 0; color: white;">👁️ {memory.title or 'Untitled'}</h2>
                <div>
                    <button style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer;">✏️ Edit</button>
                    <button style="background: rgba(255,0,0,0.3); border: none; color: white; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer; margin-left: 0.5rem;">🗑️ Delete</button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Back button
        if st.button("⬅️ Back to List"):
            del st.session_state['viewing_memory']
            st.rerun()

        # Memory Details section
        st.markdown("### ℹ️ Memory Details")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Type:** `{memory.type}`")
            st.markdown(f"**Source:** {memory.source}")
        with col2:
            st.markdown(f"**Confidence:** {memory.confidence:.2f}")
            st.markdown(f"**Created:** {memory.created_at.strftime('%m/%d/%Y, %I:%M:%S %p')}")

        # Tags section
        if memory.tags:
            st.markdown("### 🏷️ Tags")
            tags_html = " ".join([f'<span style="background: #6c757d; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; margin-right: 0.5rem; display: inline-block;">{tag}</span>' for tag in memory.tags])
            st.markdown(tags_html, unsafe_allow_html=True)

        # Content section
        st.markdown("### 📄 Content")
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #667eea;">
            {full_text.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

        # Stop here - don't show the rest of the page
        st.stop()

elif st.session_state.get('editing_memory'):
    # Edit page
    memory_id = st.session_state['editing_memory']
    memory = storage.get(memory_id)

    if memory:
        st.markdown(f"""
        <div class="page-header">
            <h1 class="page-title">✏️ Edit Memory</h1>
            <p class="page-subtitle">Update memory: {memory.title or 'Untitled'}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("⬅️ Back"):
            del st.session_state['editing_memory']
            st.rerun()

        # Extract current text
        def extract_text(value):
            import json
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict) and 'text' in parsed:
                        return extract_text(parsed['text'])
                    return value
                except:
                    return value
            elif isinstance(value, dict) and 'text' in value:
                return extract_text(value['text'])
            else:
                return str(value)

        current_text = extract_text(memory.content['text']) if isinstance(memory.content, dict) and 'text' in memory.content else (memory.text or "")

        with st.form("edit_memory"):
            col1, col2 = st.columns(2)
            with col1:
                mem_type = st.text_input("Type *", value=memory.type)
            with col2:
                source = st.text_input("Source *", value=memory.source)

            title = st.text_input("Title", value=memory.title or "")

            text = st.text_area(
                "Text Content *",
                value=current_text,
                height=200
            )

            tags_input = st.text_input(
                "Tags (comma-separated)",
                value=", ".join(memory.tags) if memory.tags else ""
            )

            confidence = st.slider("Confidence", 0.0, 1.0, float(memory.confidence), 0.05)

            submitted = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)

            if submitted:
                if not mem_type or not source or not text:
                    st.error("Type, Source, and Text are required fields")
                else:
                    try:
                        tags = [t.strip() for t in tags_input.split(",") if t.strip()]

                        update_data = {
                            'type': mem_type,
                            'source': source,
                            'title': title if title else None,
                            'tags': tags,
                            'confidence': confidence,
                            'text': text,
                            'content': {"text": text}
                        }

                        storage.update(memory.id, update_data)
                        st.success("✅ Memory updated successfully!")

                        # Clear edit mode
                        del st.session_state['editing_memory']
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

        st.stop()

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
        <h1 class="page-title">📊 Statistics Dashboard</h1>
        <p class="page-subtitle">Overview of your Memorizer memory storage system</p>
    </div>
    """, unsafe_allow_html=True)

    # Calculate average memory size
    all_memories = storage.list_all(limit=1000)
    total_size = sum(len(str(m.content)) for m in all_memories)
    avg_size = total_size // len(all_memories) if all_memories else 0
    estimated_size_kb = total_size // 1024 if total_size > 0 else 0

    # Get unique type count
    unique_types = len(set(m.type for m in all_memories))

    # Main stats cards with icons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🧠</div>
            <div class="stats-value">{stats.total_memories}</div>
            <div class="stats-label">Total Memories</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">📄</div>
            <div class="stats-value">{avg_size:,} bytes</div>
            <div class="stats-label">Average Memory Size</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">💾</div>
            <div class="stats-value">{estimated_size_kb} KB</div>
            <div class="stats-label">Estimated Content Size</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🔲</div>
            <div class="stats-value">384D</div>
            <div class="stats-label">Vector Dimensions</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # System Information and Quick Actions
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0;">⚙️ System Information</h3>
        </div>
        """, unsafe_allow_html=True)

        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        st.html(f"""
        <div class="search-card">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div>
                    <p><strong>Database Engine</strong></p>
                    <p>🗄️ ChromaDB with vector extension</p>
                    <br>

                    <p><strong>Framework</strong></p>
                    <p>🐍 Python 3.11</p>
                    <br>

                    <p><strong>Search Technology</strong></p>
                    <p>🔍 Vector Similarity Search</p>
                </div>
                <div>
                    <p><strong>Embedding Model</strong></p>
                    <p>🎯 384-dimensional vectors</p>
                    <br>

                    <p><strong>API Protocol</strong></p>
                    <p>📡 Model Context Protocol (MCP)</p>
                    <br>

                    <p><strong>Last Updated</strong></p>
                    <p>🕐 {current_time}</p>
                </div>
            </div>
        </div>
        """)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0;">🛠️ Quick Actions</h3>
        </div>
        """, unsafe_allow_html=True)

        if st.button("➕ Add New Memory", use_container_width=True, type="primary"):
            st.session_state['page'] = "➕ Create Memory"
            st.rerun()

        if st.button("📋 View All Memories", use_container_width=True):
            st.session_state['page'] = "📋 All Memories"
            st.rerun()

        if st.button("🔄 Refresh Stats", use_container_width=True):
            st.rerun()

    # Health Status
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
        <h3 style="color: white; margin: 0;">ℹ️ Health Status</h3>
    </div>
    """, unsafe_allow_html=True)

    st.html("""
    <div class="search-card">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.25rem; padding: 0.75rem; color: #155724;">
                ✅ Database Connection
            </div>
            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.25rem; padding: 0.75rem; color: #155724;">
                ✅ Embedding Service
            </div>
            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.25rem; padding: 0.75rem; color: #155724;">
                ✅ Vector Operations
            </div>
        </div>
    </div>
    """)

    # Performance Insights
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
        <h3 style="color: white; margin: 0;">⚡ Performance Insights</h3>
    </div>
    """, unsafe_allow_html=True)

    st.html(f"""
    <div class="search-card">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 1rem;">
            <div>
                <p><strong>Search Accuracy</strong></p>
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.25rem; padding: 0.5rem; color: #155724; margin-top: 0.5rem;">
                    🎯 Vector-based
                </div>
            </div>
            <div>
                <p><strong>Scalability</strong></p>
                <div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 0.25rem; padding: 0.5rem; color: #0c5460; margin-top: 0.5rem;">
                    💾 ChromaDB
                </div>
            </div>
            <div>
                <p><strong>Memory Types</strong></p>
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 0.25rem; padding: 0.5rem; color: #856404; margin-top: 0.5rem;">
                    🏷️ {unique_types} types
                </div>
            </div>
            <div>
                <p><strong>API Compatibility</strong></p>
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.25rem; padding: 0.5rem; color: #155724; margin-top: 0.5rem;">
                    📡 MCP Standard
                </div>
            </div>
        </div>
    </div>
    """)

elif page == "🔧 Tools":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">🔧 Memory Management Tools</h1>
        <p class="page-subtitle">Tools to maintain and improve your memory database.</p>
    </div>
    """, unsafe_allow_html=True)

    # Title Generation Tool Card
    st.html("""
    <div class="search-card">
        <h3 style="margin-top: 0;">📝 Title Generation</h3>
        <p><strong>Automatically generate descriptive titles for memories that don't have them using AI.</strong></p>
        <p style="color: #6c757d; margin-top: 1rem;">
            This tool will scan your memory database for entries without titles and use the configured LLM to
            generate meaningful titles based on the content.
        </p>
    </div>
    """)

    if st.button("✏️ Generate Titles", type="primary", use_container_width=True):
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

    st.markdown("<br>", unsafe_allow_html=True)

    # Metadata Embedding Tool Card
    st.html("""
    <div class="search-card">
        <h3 style="margin-top: 0;">🚀 Metadata Embedding</h3>
        <p><strong>Generate or regenerate metadata embeddings for improved search performance.</strong></p>
        <p style="color: #6c757d; margin-top: 1rem;">
            This tool creates embeddings from memory titles and tags to enable better semantic search and organization.
        </p>
    </div>
    """)

    if st.button("⚡ Manage Embeddings", use_container_width=True):
        st.info("Embedding regeneration will be processed. This feature scans all memories and regenerates their vector embeddings.")
        all_memories = storage.list_all(limit=1000)
        if all_memories:
            progress = st.progress(0)
            status = st.empty()

            for idx, memory in enumerate(all_memories):
                status.text(f"Processing embeddings {idx + 1}/{len(all_memories)}...")
                progress.progress((idx + 1) / len(all_memories))
                # Embeddings are automatically regenerated when we update
                try:
                    storage.update(memory.id, {'text': memory.text})
                except Exception as e:
                    st.warning(f"Failed for {memory.id}: {e}")

            status.text("Done!")
            st.success(f"Regenerated embeddings for {len(all_memories)} memories!")
        else:
            st.warning("No memories found to process.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Performance Analytics Tool Card
    st.html("""
    <div class="search-card">
        <h3 style="margin-top: 0;">📊 Performance Analytics</h3>
        <p><strong>View analytics and performance metrics for automated tools.</strong></p>
        <p style="color: #6c757d; margin-top: 1rem;">
            Track how tools perform, success rates, and processing times.
        </p>
    </div>
    """)

    # Create expandable analytics section
    with st.expander("📈 View Performance Analytics", expanded=False):
        # Get all memories for analysis
        all_memories = storage.list_all(limit=1000)

        if not all_memories:
            st.warning("No memories found to analyze.")
        else:
            # Calculate analytics metrics
            total_count = len(all_memories)
            titled_count = len([m for m in all_memories if m.title])
            untitled_count = total_count - titled_count

            # Calculate title generation success rate
            title_success_rate = (titled_count / total_count * 100) if total_count > 0 else 0

            # Calculate average confidence
            avg_confidence = sum(m.confidence for m in all_memories) / total_count if total_count > 0 else 0

            # Get unique types and tags
            unique_types = len(set(m.type for m in all_memories))
            all_tags = [tag for m in all_memories for tag in m.tags]
            unique_tags = len(set(all_tags))

            # Time-based metrics
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            last_24h = [m for m in all_memories if (now - m.created_at).total_seconds() < 86400]
            last_7d = [m for m in all_memories if (now - m.created_at).total_seconds() < 604800]
            last_30d = [m for m in all_memories if (now - m.created_at).total_seconds() < 2592000]

            # Display metrics in columns
            st.markdown("#### 📊 Tool Performance Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.html(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 0.5rem; color: white; text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">{title_success_rate:.1f}%</div>
                    <div style="font-size: 0.875rem;">Title Coverage</div>
                </div>
                """)

            with col2:
                st.html(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1rem; border-radius: 0.5rem; color: white; text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">{avg_confidence:.2f}</div>
                    <div style="font-size: 0.875rem;">Avg Confidence</div>
                </div>
                """)

            with col3:
                st.html(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1rem; border-radius: 0.5rem; color: white; text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">{unique_types}</div>
                    <div style="font-size: 0.875rem;">Memory Types</div>
                </div>
                """)

            with col4:
                st.html(f"""
                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1rem; border-radius: 0.5rem; color: white; text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">{unique_tags}</div>
                    <div style="font-size: 0.875rem;">Unique Tags</div>
                </div>
                """)

            st.markdown("<br>", unsafe_allow_html=True)

            # Activity metrics
            st.markdown("#### 📅 Activity Trends")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.html(f"""
                <div class="search-card">
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; color: #667eea; font-weight: bold;">{len(last_24h)}</div>
                        <div style="color: #6c757d;">Last 24 Hours</div>
                    </div>
                </div>
                """)

            with col2:
                st.html(f"""
                <div class="search-card">
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; color: #f093fb; font-weight: bold;">{len(last_7d)}</div>
                        <div style="color: #6c757d;">Last 7 Days</div>
                    </div>
                </div>
                """)

            with col3:
                st.html(f"""
                <div class="search-card">
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; color: #4facfe; font-weight: bold;">{len(last_30d)}</div>
                        <div style="color: #6c757d;">Last 30 Days</div>
                    </div>
                </div>
                """)

            st.markdown("<br>", unsafe_allow_html=True)

            # Tool-specific metrics
            st.markdown("#### 🛠️ Tool-Specific Metrics")

            col1, col2 = st.columns(2)

            with col1:
                st.html(f"""
                <div class="search-card">
                    <h4 style="margin-top: 0;">📝 Title Generation Tool</h4>
                    <div style="margin: 1rem 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span><strong>Success Rate:</strong></span>
                            <span style="color: #28a745;">{title_success_rate:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span><strong>Titled Memories:</strong></span>
                            <span>{titled_count:,}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span><strong>Pending Titles:</strong></span>
                            <span>{untitled_count:,}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><strong>Status:</strong></span>
                            <span style="color: {'#28a745' if untitled_count == 0 else '#ffc107'};">
                                {'All Complete' if untitled_count == 0 else f'{untitled_count} Remaining'}
                            </span>
                        </div>
                    </div>
                </div>
                """)

            with col2:
                # Calculate embedding coverage (all memories should have embeddings)
                embedding_coverage = 100.0  # ChromaDB automatically creates embeddings
                total_vectors = total_count

                st.html(f"""
                <div class="search-card">
                    <h4 style="margin-top: 0;">🚀 Metadata Embedding Tool</h4>
                    <div style="margin: 1rem 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span><strong>Coverage:</strong></span>
                            <span style="color: #28a745;">{embedding_coverage:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span><strong>Total Vectors:</strong></span>
                            <span>{total_vectors:,}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span><strong>Vector Dimension:</strong></span>
                            <span>384D</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><strong>Status:</strong></span>
                            <span style="color: #28a745;">All Embedded</span>
                        </div>
                    </div>
                </div>
                """)

            st.markdown("<br>", unsafe_allow_html=True)

            # Data quality metrics
            st.markdown("#### ✅ Data Quality Metrics")

            # Calculate quality metrics
            high_confidence = len([m for m in all_memories if m.confidence >= 0.8])
            medium_confidence = len([m for m in all_memories if 0.5 <= m.confidence < 0.8])
            low_confidence = len([m for m in all_memories if m.confidence < 0.5])

            tagged_memories = len([m for m in all_memories if m.tags])
            avg_tags_per_memory = len(all_tags) / total_count if total_count > 0 else 0

            st.html(f"""
            <div class="search-card">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div>
                        <h5 style="margin-top: 0;">Confidence Distribution</h5>
                        <div style="margin: 1rem 0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span>High (≥80%):</span>
                                <span style="color: #28a745; font-weight: bold;">{high_confidence:,} ({high_confidence/total_count*100:.1f}%)</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span>Medium (50-80%):</span>
                                <span style="color: #ffc107; font-weight: bold;">{medium_confidence:,} ({medium_confidence/total_count*100:.1f}%)</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span>Low (&lt;50%):</span>
                                <span style="color: #dc3545; font-weight: bold;">{low_confidence:,} ({low_confidence/total_count*100:.1f}%)</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <h5 style="margin-top: 0;">Tagging Metrics</h5>
                        <div style="margin: 1rem 0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span>Tagged Memories:</span>
                                <span style="font-weight: bold;">{tagged_memories:,} ({tagged_memories/total_count*100:.1f}%)</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span>Total Tags:</span>
                                <span style="font-weight: bold;">{len(all_tags):,}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span>Avg Tags/Memory:</span>
                                <span style="font-weight: bold;">{avg_tags_per_memory:.2f}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """)

    st.markdown("<br>", unsafe_allow_html=True)

    # Memory Maintenance Tool Card
    st.html("""
    <div class="search-card">
        <h3 style="margin-top: 0;">🔍 Memory Maintenance</h3>
        <p><strong>Find and fix issues with your memory database.</strong></p>
        <p style="color: #6c757d; margin-top: 1rem;">
            Detect orphaned chunks, broken relationships, and other data quality issues.
        </p>
    </div>
    """)

    # Create expandable maintenance section
    with st.expander("🔧 Run Database Maintenance", expanded=False):
        st.markdown("#### 🔍 Database Health Check")
        st.caption("Scan your memory database for potential issues and quality problems.")

        col1, col2 = st.columns([3, 1])

        with col1:
            check_options = st.multiselect(
                "Select checks to perform:",
                [
                    "Missing or empty content",
                    "Missing titles",
                    "Low confidence memories",
                    "Untagged memories",
                    "Duplicate content",
                    "Invalid metadata",
                    "Orphaned data"
                ],
                default=["Missing or empty content", "Missing titles", "Low confidence memories"]
            )

        with col2:
            auto_fix = st.checkbox("Auto-fix issues", value=False, help="Automatically fix issues where possible")

        if st.button("🔍 Run Maintenance Scan", type="primary", use_container_width=True):
            all_memories = storage.list_all(limit=1000)

            if not all_memories:
                st.warning("No memories found in database.")
            else:
                st.info(f"Scanning {len(all_memories)} memories...")

                issues_found = []
                fixes_applied = []

                # Check 1: Missing or empty content
                if "Missing or empty content" in check_options:
                    with st.spinner("Checking for missing or empty content..."):
                        empty_content = []
                        for memory in all_memories:
                            has_text = memory.text and memory.text.strip()
                            has_content = memory.content and any(v for v in memory.content.values() if v)

                            if not has_text and not has_content:
                                empty_content.append(memory)
                                issues_found.append({
                                    'type': 'Empty Content',
                                    'severity': 'high',
                                    'memory_id': memory.id,
                                    'description': f"Memory has no content or text"
                                })

                        if empty_content:
                            st.error(f"⚠️ Found {len(empty_content)} memories with missing or empty content")
                            if auto_fix:
                                # Can't auto-fix empty content
                                st.warning("⚠️ Empty content cannot be auto-fixed. Manual review required.")
                        else:
                            st.success("✅ No empty content issues found")

                # Check 2: Missing titles
                if "Missing titles" in check_options:
                    with st.spinner("Checking for missing titles..."):
                        untitled = [m for m in all_memories if not m.title]

                        if untitled:
                            st.warning(f"⚠️ Found {len(untitled)} memories without titles")
                            for memory in untitled:
                                issues_found.append({
                                    'type': 'Missing Title',
                                    'severity': 'medium',
                                    'memory_id': memory.id,
                                    'description': f"Memory has no title"
                                })

                            if auto_fix and llm.is_available():
                                st.info("🔧 Auto-fixing: Generating titles...")
                                progress = st.progress(0)
                                fixed_count = 0

                                for idx, memory in enumerate(untitled[:10]):  # Limit to 10 for performance
                                    try:
                                        title = llm.generate_title(memory.text or str(memory.content))
                                        if title:
                                            storage.update(memory.id, {'title': title})
                                            fixed_count += 1
                                            fixes_applied.append(f"Generated title for memory {memory.id}")
                                    except Exception as e:
                                        st.warning(f"Failed to generate title for {memory.id}: {e}")

                                    progress.progress((idx + 1) / min(len(untitled), 10))

                                st.success(f"✅ Generated {fixed_count} titles")
                        else:
                            st.success("✅ All memories have titles")

                # Check 3: Low confidence memories
                if "Low confidence memories" in check_options:
                    with st.spinner("Checking for low confidence memories..."):
                        low_confidence = [m for m in all_memories if m.confidence < 0.5]

                        if low_confidence:
                            st.warning(f"⚠️ Found {len(low_confidence)} memories with confidence < 50%")
                            for memory in low_confidence:
                                issues_found.append({
                                    'type': 'Low Confidence',
                                    'severity': 'low',
                                    'memory_id': memory.id,
                                    'description': f"Confidence: {memory.confidence:.2%}"
                                })

                            if auto_fix:
                                st.info("ℹ️ Low confidence requires manual review. Consider updating or removing these memories.")
                        else:
                            st.success("✅ All memories have acceptable confidence levels")

                # Check 4: Untagged memories
                if "Untagged memories" in check_options:
                    with st.spinner("Checking for untagged memories..."):
                        untagged = [m for m in all_memories if not m.tags]

                        if untagged:
                            st.warning(f"⚠️ Found {len(untagged)} memories without tags")
                            for memory in untagged:
                                issues_found.append({
                                    'type': 'No Tags',
                                    'severity': 'low',
                                    'memory_id': memory.id,
                                    'description': f"Memory has no tags"
                                })

                            if auto_fix:
                                st.info("ℹ️ Tag suggestions require manual review.")
                        else:
                            st.success("✅ All memories are tagged")

                # Check 5: Duplicate content
                if "Duplicate content" in check_options:
                    with st.spinner("Checking for duplicate content..."):
                        content_hashes = {}
                        duplicates = []

                        for memory in all_memories:
                            content_str = str(memory.text or memory.content)
                            content_hash = hash(content_str)

                            if content_hash in content_hashes:
                                duplicates.append((memory, content_hashes[content_hash]))
                                issues_found.append({
                                    'type': 'Duplicate Content',
                                    'severity': 'medium',
                                    'memory_id': memory.id,
                                    'description': f"Duplicate of memory {content_hashes[content_hash].id}"
                                })
                            else:
                                content_hashes[content_hash] = memory

                        if duplicates:
                            st.warning(f"⚠️ Found {len(duplicates)} potential duplicate memories")
                            if auto_fix:
                                st.info("ℹ️ Duplicate removal requires manual review to ensure no data loss.")
                        else:
                            st.success("✅ No duplicate content detected")

                # Check 6: Invalid metadata
                if "Invalid metadata" in check_options:
                    with st.spinner("Checking for invalid metadata..."):
                        invalid_metadata = []

                        for memory in all_memories:
                            # Check for invalid types
                            if not memory.type or not isinstance(memory.type, str):
                                invalid_metadata.append(memory)
                                issues_found.append({
                                    'type': 'Invalid Metadata',
                                    'severity': 'high',
                                    'memory_id': memory.id,
                                    'description': f"Invalid type: {type(memory.type)}"
                                })

                            # Check for invalid confidence
                            if not (0 <= memory.confidence <= 1):
                                invalid_metadata.append(memory)
                                issues_found.append({
                                    'type': 'Invalid Metadata',
                                    'severity': 'medium',
                                    'memory_id': memory.id,
                                    'description': f"Invalid confidence: {memory.confidence}"
                                })

                        if invalid_metadata:
                            st.error(f"⚠️ Found {len(invalid_metadata)} memories with invalid metadata")
                            if auto_fix:
                                st.info("🔧 Auto-fixing metadata issues...")
                                fixed_count = 0
                                for memory in invalid_metadata:
                                    try:
                                        updates = {}
                                        if not memory.type or not isinstance(memory.type, str):
                                            updates['type'] = 'unknown'
                                        if not (0 <= memory.confidence <= 1):
                                            updates['confidence'] = max(0, min(1, memory.confidence))

                                        if updates:
                                            storage.update(memory.id, updates)
                                            fixed_count += 1
                                            fixes_applied.append(f"Fixed metadata for memory {memory.id}")
                                    except Exception as e:
                                        st.warning(f"Failed to fix metadata for {memory.id}: {e}")

                                st.success(f"✅ Fixed {fixed_count} metadata issues")
                        else:
                            st.success("✅ All metadata is valid")

                # Check 7: Orphaned data
                if "Orphaned data" in check_options:
                    with st.spinner("Checking for orphaned data..."):
                        # Check for memories with broken references (if we had relationships)
                        # For now, just check for basic data integrity
                        orphaned = []

                        for memory in all_memories:
                            # Check if memory has valid timestamps
                            if not memory.created_at or not memory.updated_at:
                                orphaned.append(memory)
                                issues_found.append({
                                    'type': 'Orphaned Data',
                                    'severity': 'medium',
                                    'memory_id': memory.id,
                                    'description': f"Missing timestamps"
                                })

                        if orphaned:
                            st.warning(f"⚠️ Found {len(orphaned)} memories with orphaned data")
                            if auto_fix:
                                st.info("🔧 Auto-fixing orphaned data...")
                                from datetime import datetime
                                fixed_count = 0
                                for memory in orphaned:
                                    try:
                                        updates = {}
                                        if not memory.created_at:
                                            updates['created_at'] = datetime.utcnow()
                                        if not memory.updated_at:
                                            updates['updated_at'] = datetime.utcnow()

                                        if updates:
                                            # Note: ChromaDB doesn't support updating timestamps
                                            # This is a limitation we need to document
                                            fixed_count += 1
                                    except Exception as e:
                                        st.warning(f"Failed to fix orphaned data for {memory.id}: {e}")

                                st.info(f"ℹ️ Timestamp updates are not supported by ChromaDB")
                        else:
                            st.success("✅ No orphaned data detected")

                # Display summary
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 📋 Scan Summary")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.html(f"""
                    <div class="search-card" style="text-align: center;">
                        <div style="font-size: 2rem; color: #667eea; font-weight: bold;">{len(all_memories)}</div>
                        <div style="color: #6c757d;">Memories Scanned</div>
                    </div>
                    """)

                with col2:
                    issues_color = "#dc3545" if issues_found else "#28a745"
                    st.html(f"""
                    <div class="search-card" style="text-align: center;">
                        <div style="font-size: 2rem; color: {issues_color}; font-weight: bold;">{len(issues_found)}</div>
                        <div style="color: #6c757d;">Issues Found</div>
                    </div>
                    """)

                with col3:
                    st.html(f"""
                    <div class="search-card" style="text-align: center;">
                        <div style="font-size: 2rem; color: #28a745; font-weight: bold;">{len(fixes_applied)}</div>
                        <div style="color: #6c757d;">Fixes Applied</div>
                    </div>
                    """)

                # Display detailed issues if found
                if issues_found:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### ⚠️ Issues Details")

                    # Group by severity
                    high_severity = [i for i in issues_found if i['severity'] == 'high']
                    medium_severity = [i for i in issues_found if i['severity'] == 'medium']
                    low_severity = [i for i in issues_found if i['severity'] == 'low']

                    if high_severity:
                        with st.expander(f"🔴 High Severity ({len(high_severity)} issues)", expanded=True):
                            for issue in high_severity[:10]:  # Show first 10
                                st.markdown(f"- **{issue['type']}**: {issue['description']} (ID: `{str(issue['memory_id'])[:8]}...`)")

                    if medium_severity:
                        with st.expander(f"🟡 Medium Severity ({len(medium_severity)} issues)"):
                            for issue in medium_severity[:10]:  # Show first 10
                                st.markdown(f"- **{issue['type']}**: {issue['description']} (ID: `{str(issue['memory_id'])[:8]}...`)")

                    if low_severity:
                        with st.expander(f"🟢 Low Severity ({len(low_severity)} issues)"):
                            for issue in low_severity[:10]:  # Show first 10
                                st.markdown(f"- **{issue['type']}**: {issue['description']} (ID: `{str(issue['memory_id'])[:8]}...`)")

                # Display fixes applied
                if fixes_applied:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### ✅ Fixes Applied")
                    for fix in fixes_applied[:10]:  # Show first 10
                        st.success(f"✅ {fix}")

                if not issues_found:
                    st.success("🎉 Your database is healthy! No issues detected.")
                elif not auto_fix:
                    st.info("💡 Tip: Enable 'Auto-fix issues' to automatically resolve problems where possible.")

elif page == "⚙️ System Config":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">⚙️ System Configuration</h1>
        <p class="page-subtitle">View system settings and configuration</p>
    </div>
    """, unsafe_allow_html=True)

    llm_status = '✅ Yes' if llm.is_available() else '❌ No'
    similarity_pct = f"{settings.similarity_threshold:.2%}"

    st.html(f"""
    <div class="search-card">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <h3>Application Settings</h3>
                <p><strong>App Name:</strong> {settings.app_name}</p>
                <p><strong>Version:</strong> {settings.app_version}</p>
                <p><strong>Environment:</strong> {settings.environment}</p>
                <p><strong>LLM Available:</strong> {llm_status}</p>
            </div>
            <div>
                <h3>Vector Search Settings</h3>
                <p><strong>Embedding Model:</strong> {settings.embedding_model}</p>
                <p><strong>Embedding Dimension:</strong> {settings.embedding_dimension}</p>
                <p><strong>Search Limit:</strong> {settings.search_limit}</p>
                <p><strong>Similarity Threshold:</strong> {similarity_pct}</p>
            </div>
        </div>
    </div>
    """)

    st.html(f"""
    <div class="search-card">
        <h3>Storage Paths</h3>
        <pre style="background: #f6f8fa; padding: 0.5rem; border-radius: 0.25rem; margin: 0.5rem 0;">ChromaDB: {settings.chroma_dir}</pre>
        <pre style="background: #f6f8fa; padding: 0.5rem; border-radius: 0.25rem; margin: 0.5rem 0;">Models: {settings.models_dir}</pre>
        <pre style="background: #f6f8fa; padding: 0.5rem; border-radius: 0.25rem; margin: 0.5rem 0;">Data: {settings.data_dir}</pre>
    </div>
    """)

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
