# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-01-20

### 🎉 Major Refactor - Production-Ready Architecture

This release represents a complete overhaul of the MCP server with focus on maintainability, testability, and scalability.

### Added

- **Core Modules** (`core/`)
  - `NotionClient` - Async HTTP client with comprehensive error handling
  - `SchemaManager` - Schema fetching and caching
  - `PropertyFormatter` - Property display formatting
  - `BlockFormatter` - Markdown ↔ Notion blocks conversion

- **Validation System** (`utils/validators.py`)
  - `PropertyValidator` - Validates properties against Notion schemas
  - Validates property types, select options, read-only fields
  - Comprehensive error messages

- **Split Tools** (`tools/`)
  - `query.py` - Search and discovery operations (5 tools)
  - `pages.py` - CRUD operations (4 tools)
  - `content.py` - Content operations (2 tools)

- **Configuration**
  - YAML-based database configuration (`databases.yaml`)
  - Dynamic configuration loading
  - Template files (`.env.example`, `databases.yaml.example`)

- **Testing Infrastructure**
  - Connection testing scripts
  - Validation testing utilities
  - Comprehensive error diagnostics

- **Documentation**
  - Comprehensive README
  - Architecture documentation
  - Code examples and troubleshooting

### Changed

- **Configuration Management**
  - Moved from hardcoded env vars to YAML configuration
  - No more hardcoded database names
  - Dynamic database discovery
  - Title property defaults to "title" (was "Name")

- **Architecture**
  - Removed circular dependencies
  - Separated core logic from MCP concerns
  - Immutable configuration (no runtime mutation)
  - Clean, linear dependency flow

- **Error Handling**
  - Better error messages from `NotionClient`
  - Context-aware error responses
  - Helpful suggestions for common issues

- **Property Handling**
  - Smarter title extraction (tries multiple property names)
  - Complete property type coverage
  - Better formatting for display

### Removed

- Hardcoded database fallbacks in config
- Config mutation in `_ensure_data_source_id`
- Monolithic `notion_api.py` (split into focused modules)
- Unnecessary duplicate code

### Fixed

- Circular import issues
- Config mutation bugs
- Missing property types in formatter
- Incomplete error handling

### Technical Debt Cleared

- ✅ No hardcoded values
- ✅ No circular dependencies
- ✅ No config mutation
- ✅ Separated concerns
- ✅ Testable core modules

## [1.0.0] - 2025-11-XX

### Initial Release

- Basic MCP server with Notion integration
- FastMCP-based implementation
- Support for Notion API 2025-09-03
- Query, create, update, and search operations
- Basic property and content handling

---

## Version History

### Versioning Scheme

This project follows [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0) - Breaking changes
- **Minor** (0.X.0) - New features, backwards compatible
- **Patch** (0.0.X) - Bug fixes, backwards compatible

### Upgrade Guides

#### 1.x → 2.0

**Required Actions:**

1. **Create `databases.yaml`**
   ```bash
   cp databases.yaml.example databases.yaml
   # Add your database configurations
   ```

2. **Update `.env` (if needed)**
   - Token format unchanged
   - API version unchanged
   - Old env vars for databases no longer used

3. **Restart server**
   ```bash
   bash run_mcp.sh
   ```

**Breaking Changes:**
- None for tool users! All tools have same signatures
- Configuration now requires `databases.yaml`
- Tools look for "title" property by default (was "Name")

**Benefits:**
- Better architecture
- Easier to maintain
- Ready for scaling
- Validation system
- Better error messages

---

## Roadmap

### v2.1.0 (Planned)
- [ ] MCP validation integration (fix protocol issue)
- [ ] Enhanced markdown support (tables, callouts, dividers)
- [ ] Batch operations
- [ ] Better async error handling

### v2.2.0 (Future)
- [ ] Webhook support
- [ ] Multi-workspace support
- [ ] Advanced filtering DSL
- [ ] Property templates

### v3.0.0 (Vision)
- [ ] Plugin system
- [ ] Custom formatters
- [ ] Database synchronization
- [ ] Real-time updates
