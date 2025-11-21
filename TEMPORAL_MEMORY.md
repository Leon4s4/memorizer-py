# Temporal Memory Support

## Overview

The memory system now supports time-based memories and comparisons for tracking changes over time.

## New Feature: `event_date`

Memories can now have an `event_date` field that represents when the event described in the memory occurred (as opposed to `created_at` which is when the memory was stored).

### Example Use Case: Todo List Tracking

```python
# Store today's todo status (2025-11-10)
{
  "type": "daily-status",
  "title": "Todo List - 2025-11-10",
  "text": "10 PBIs in progress, 1 blocked",
  "event_date": "2025-11-10T00:00:00Z",
  "tags": ["todo", "progress", "daily-snapshot"]
}

# Store next day's status (2025-11-11)
{
  "type": "daily-status",
  "title": "Todo List - 2025-11-11",
  "text": "10 PBIs in progress, 0 blocked",
  "event_date": "2025-11-11T00:00:00Z",
  "tags": ["todo", "progress", "daily-snapshot"]
}
```

## How to Use (Current Implementation)

### 1. Store Temporal Memories via MCP

```json
{
  "method": "tools/call",
  "params": {
    "name": "store",
    "arguments": {
      "type": "daily-status",
      "title": "Todo Progress - Nov 10",
      "text": "Today (2025-11-10): 10 PBIs in progress, 1 blocked",
      "source": "LLM",
      "tags": ["todo", "progress", "2025-11-10"],
      "eventDate": "2025-11-10"
    }
  }
}
```

### 2. Query Progress Over Time

**Current approach (using tags):**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "query": "todo progress blocked",
      "filterTags": ["todo", "progress"],
      "limit": 10
    }
  }
}
```

The hybrid search will find all todo-related memories sorted by relevance.

### 3. LLM Comparison

The LLM can then compare the results:

**User:** "How is my progress? Compare last two days"

**LLM searches and finds:**
- 2025-11-10: 10 PBIs, 1 blocked
- 2025-11-11: 10 PBIs, 0 blocked

**LLM response:** "Great progress! You cleared your blocked item. You went from 1 blocked PBI on Nov 10 to 0 blocked on Nov 11, while maintaining 10 PBIs in progress."

## Implementation Status

✅ **Completed:**
- Added `event_date` field to Memory model
- Added `event_date` to MemoryCreate
- Model changes support temporal data

⏳ **TODO (Future Enhancement):**
- Date range filtering in search (start_date, end_date)
- Dedicated MCP tool for time-series queries
- Automatic time-based grouping and comparison
- Support for ISO date strings in MCP tools

## Workaround for Now

**Best Practice:** Use descriptive tags and text for temporal queries:

```javascript
// Store memories with date in tags and text
{
  "title": "Daily Status - 2025-11-10",
  "text": "2025-11-10: 10 PBIs in progress, 1 blocked",
  "tags": ["daily-status", "2025-11-10", "todo"],
  "type": "status-snapshot"
}
```

Then search with:
```javascript
{
  "query": "daily status todo November 2025",
  "filterTags": ["daily-status"],
  "limit": 30
}
```

The hybrid search (70% semantic + 30% keyword) will find matching memories, and the LLM can parse dates from the text to compare them.

## Future API

Once fully implemented, you'll be able to:

```javascript
// Search with date range
{
  "query": "todo progress",
  "startDate": "2025-11-01",
  "endDate": "2025-11-30",
  "filterTags": ["daily-status"]
}

// Dedicated comparison tool
{
  "method": "tools/call",
  "params": {
    "name": "compare_temporal",
    "arguments": {
      "query": "todo progress",
      "dates": ["2025-11-10", "2025-11-11"]
    }
  }
}
```

## Why This Works Now

Even without full date filtering, your use case works because:

1. **Hybrid search** finds memories with matching keywords ("todo", "progress", "blocked")
2. **Tags** help filter to specific categories
3. **Text content** includes dates that the LLM can parse
4. **LLM comparison** can extract and compare numeric data from retrieved memories

The system is ready for your todo list tracking - just include dates in your memory text and tags!
