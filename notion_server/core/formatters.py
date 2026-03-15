"""
Property and Block Formatters
Handles conversion between Notion's API format and human-readable formats.
"""

from typing import Dict, Any, List, Optional


class PropertyFormatter:
    """Format Notion properties for display and input."""
    
    @staticmethod
    def extract_title(properties: Dict[str, Any]) -> str:
        """
        Extract title text from properties.
        Tries common title property names, then any title type.
        
        Args:
            properties: Notion page properties
            
        Returns:
            Title text or "Untitled"
        """
        # Try common names
        for key in ["Name", "Title", "name", "title"]:
            if key in properties:
                prop = properties[key]
                if prop.get("type") == "title":
                    title_array = prop.get("title", [])
                    if title_array and isinstance(title_array, list):
                        return "".join(t.get("plain_text", "") for t in title_array)
        
        # Fallback: find any title type
        for prop in properties.values():
            if prop.get("type") == "title":
                title_array = prop.get("title", [])
                if title_array:
                    return "".join(t.get("plain_text", "") for t in title_array)
        
        return "Untitled"
    
    @staticmethod
    def format_for_display(properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format properties for human-readable display.
        Extracts plain text and values from Notion's complex property structure.
        
        Args:
            properties: Raw Notion properties
            
        Returns:
            Simplified key-value dict
        """
        formatted = {}
        
        for key, prop in properties.items():
            prop_type = prop.get("type")
            
            if prop_type == "title":
                title_array = prop.get("title", [])
                formatted[key] = "".join(t.get("plain_text", "") for t in title_array)
                
            elif prop_type == "rich_text":
                text_array = prop.get("rich_text", [])
                formatted[key] = "".join(t.get("plain_text", "") for t in text_array)
                
            elif prop_type == "number":
                formatted[key] = prop.get("number")
                
            elif prop_type == "select":
                select = prop.get("select")
                formatted[key] = select.get("name") if select else None
                
            elif prop_type == "multi_select":
                multi = prop.get("multi_select", [])
                formatted[key] = [item.get("name") for item in multi]
                
            elif prop_type == "date":
                date = prop.get("date")
                if date:
                    formatted[key] = {
                        "start": date.get("start"),
                        "end": date.get("end"),
                    }
                else:
                    formatted[key] = None
                    
            elif prop_type == "checkbox":
                formatted[key] = prop.get("checkbox")
                
            elif prop_type == "url":
                formatted[key] = prop.get("url")
                
            elif prop_type == "email":
                formatted[key] = prop.get("email")
                
            elif prop_type == "phone_number":
                formatted[key] = prop.get("phone_number")
                
            elif prop_type == "status":
                status = prop.get("status")
                formatted[key] = status.get("name") if status else None
                
            elif prop_type == "people":
                people = prop.get("people", [])
                formatted[key] = [p.get("name") or p.get("id") for p in people]
                
            elif prop_type == "files":
                files = prop.get("files", [])
                formatted[key] = [f.get("name") for f in files]
                
            elif prop_type == "relation":
                relations = prop.get("relation", [])
                formatted[key] = [r.get("id") for r in relations]
                
            elif prop_type == "rollup":
                rollup = prop.get("rollup", {})
                rollup_type = rollup.get("type")
                formatted[key] = f"<rollup:{rollup_type}>"
                
            elif prop_type == "formula":
                formula = prop.get("formula", {})
                formula_type = formula.get("type")
                if formula_type in ["string", "number", "boolean", "date"]:
                    formatted[key] = formula.get(formula_type)
                else:
                    formatted[key] = f"<formula:{formula_type}>"
                    
            elif prop_type == "created_time":
                formatted[key] = prop.get("created_time")
                
            elif prop_type == "created_by":
                user = prop.get("created_by", {})
                formatted[key] = user.get("name") or user.get("id")
                
            elif prop_type == "last_edited_time":
                formatted[key] = prop.get("last_edited_time")
                
            elif prop_type == "last_edited_by":
                user = prop.get("last_edited_by", {})
                formatted[key] = user.get("name") or user.get("id")
                
            else:
                # Unknown type - show as placeholder
                formatted[key] = f"<{prop_type}>"
        
        return formatted


class BlockFormatter:
    """Format Notion blocks for display and input."""
    
    @staticmethod
    def extract_text(block: Dict[str, Any]) -> str:
        """
        Extract plain text from a block.
        
        Args:
            block: Notion block object
            
        Returns:
            Plain text content
        """
        block_type = block.get("type")
        if not block_type:
            return ""
        
        block_data = block.get(block_type, {})
        rich_text = block_data.get("rich_text", [])
        
        return "".join(t.get("plain_text", "") for t in rich_text)
    
    @staticmethod
    def to_markdown(blocks: List[Dict[str, Any]]) -> str:
        """
        Convert Notion blocks to markdown.
        
        Args:
            blocks: List of Notion block objects
            
        Returns:
            Markdown string
        """
        lines = []
        
        for block in blocks:
            block_type = block.get("type")
            text = BlockFormatter.extract_text(block)
            
            if block_type == "paragraph":
                lines.append(text)
                
            elif block_type == "heading_1":
                lines.append(f"# {text}")
                
            elif block_type == "heading_2":
                lines.append(f"## {text}")
                
            elif block_type == "heading_3":
                lines.append(f"### {text}")
                
            elif block_type == "bulleted_list_item":
                lines.append(f"- {text}")
                
            elif block_type == "numbered_list_item":
                lines.append(f"1. {text}")
                
            elif block_type == "to_do":
                checked = block.get("to_do", {}).get("checked", False)
                checkbox = "[x]" if checked else "[ ]"
                lines.append(f"{checkbox} {text}")
                
            elif block_type == "toggle":
                lines.append(f"▸ {text}")
                
            elif block_type == "quote":
                lines.append(f"> {text}")
                
            elif block_type == "code":
                lang = block.get("code", {}).get("language", "")
                lines.append(f"```{lang}\n{text}\n```")
                
            elif block_type == "callout":
                icon = block.get("callout", {}).get("icon", {})
                emoji = icon.get("emoji", "💡") if icon.get("type") == "emoji" else "💡"
                lines.append(f"{emoji} {text}")
                
            elif block_type == "divider":
                lines.append("---")
                
            elif text:
                lines.append(text)
        
        return "\n\n".join(lines)
    
    @staticmethod
    def from_markdown(markdown: str) -> List[Dict[str, Any]]:
        """
        Convert markdown to Notion blocks.
        Handles headings, lists, quotes, to-dos, dividers, and fenced code blocks.

        Args:
            markdown: Markdown string

        Returns:
            List of Notion block objects
        """
        def _rt(content: str) -> List[Dict[str, Any]]:
            return [{"type": "text", "text": {"content": content}}]

        blocks = []
        lines = markdown.split("\n")

        in_code = False
        code_lang = ""
        code_lines: List[str] = []

        for raw_line in lines:
            line = raw_line.strip()

            # --- Inside a fenced code block ---
            if in_code:
                if line == "```":
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": _rt("\n".join(code_lines)),
                            "language": code_lang or "plain text",
                        },
                    })
                    in_code = False
                    code_lines = []
                    code_lang = ""
                else:
                    code_lines.append(raw_line)  # preserve indentation
                continue

            # --- Fence open ---
            if line.startswith("```"):
                in_code = True
                code_lang = line[3:].strip()
                code_lines = []
                continue

            if not line:
                continue

            if line.startswith("# "):
                blocks.append({"object": "block", "type": "heading_1",
                                "heading_1": {"rich_text": _rt(line[2:])}})
            elif line.startswith("## "):
                blocks.append({"object": "block", "type": "heading_2",
                                "heading_2": {"rich_text": _rt(line[3:])}})
            elif line.startswith("### "):
                blocks.append({"object": "block", "type": "heading_3",
                                "heading_3": {"rich_text": _rt(line[4:])}})
            elif line.startswith("- ") or line.startswith("* "):
                blocks.append({"object": "block", "type": "bulleted_list_item",
                                "bulleted_list_item": {"rich_text": _rt(line[2:])}})
            elif line.startswith("> "):
                blocks.append({"object": "block", "type": "quote",
                                "quote": {"rich_text": _rt(line[2:])}})
            elif line.startswith("[ ] ") or line.startswith("[x] "):
                blocks.append({"object": "block", "type": "to_do",
                                "to_do": {"rich_text": _rt(line[4:]),
                                          "checked": line.startswith("[x]")}})
            elif line == "---":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            else:
                blocks.append({"object": "block", "type": "paragraph",
                                "paragraph": {"rich_text": _rt(line)}})

        # Flush unclosed fence as a code block rather than silently dropping it
        if in_code and code_lines:
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": _rt("\n".join(code_lines)),
                    "language": code_lang or "plain text",
                },
            })

        return blocks