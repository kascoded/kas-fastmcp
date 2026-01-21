#!/usr/bin/env python3
"""
Verify Notion token and basic API connectivity.
Quick diagnostic tool for token issues.
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import NotionConfig
from notion_server.core import NotionClient


def verify_token_format():
    """Verify token is loaded and has correct format."""
    print("=" * 70)
    print("NOTION TOKEN VERIFICATION")
    print("=" * 70)
    
    print("\n1. Checking token in environment...")
    
    if not NotionConfig.TOKEN:
        print("   ❌ NOTION_TOKEN not found")
        print("\n   Create .env file with:")
        print("     NOTION_TOKEN=ntn_your_token_here")
        return False
    
    token = NotionConfig.TOKEN
    print(f"   ✓ Token found")
    print(f"     Length: {len(token)} characters")
    print(f"     Preview: {token[:15]}...{token[-5:]}")
    
    # Check format
    if token.startswith("ntn_"):
        print(f"   ✓ Format: New format (ntn_)")
    elif token.startswith("secret_"):
        print(f"   ✓ Format: Legacy format (secret_)")
    else:
        print(f"   ❌ Invalid format: should start with 'ntn_' or 'secret_'")
        return False
    
    # Check for common issues
    issues = []
    if token != token.strip():
        issues.append("Token has whitespace (remove it)")
    if '"' in token or "'" in token:
        issues.append("Token has quotes (remove them)")
    if ' ' in token:
        issues.append("Token has spaces (remove them)")
    
    if issues:
        print(f"\n   ⚠️  Issues found:")
        for issue in issues:
            print(f"       • {issue}")
        return False
    
    print(f"   ✓ No formatting issues")
    return True


async def test_token_with_api():
    """Test token with actual Notion API call."""
    print("\n2. Testing token with Notion API...")
    
    client = NotionClient()
    
    try:
        # Test with search endpoint (most permissive)
        result = await client.post("search", {"page_size": 1})
        
        print(f"   ✓ Token is VALID!")
        print(f"   ✓ API connection successful")
        
        # Check if we got any results
        results = result.get("results", [])
        if results:
            print(f"   ✓ Found {len(results)} accessible page(s)")
        else:
            print(f"   ⚠️  No pages accessible yet")
            print(f"       Add integration to your databases")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        
        if "401" in error_str or "Unauthorized" in error_str:
            print(f"   ❌ Token is INVALID (401 Unauthorized)")
            print(f"\n   The token was rejected by Notion.")
            print(f"   Get a new token:")
            print(f"     1. Go to: https://www.notion.so/my-integrations")
            print(f"     2. Click your integration")
            print(f"     3. Copy 'Internal Integration Token'")
            print(f"     4. Update NOTION_TOKEN in .env")
            
        elif "404" in error_str:
            print(f"   ❌ Endpoint not found (404)")
            print(f"   This shouldn't happen with /search")
            
        else:
            print(f"   ❌ Unexpected error: {error_str}")
        
        return False


async def main():
    """Run all verification steps."""
    
    # Step 1: Verify token format
    if not verify_token_format():
        print("\n" + "=" * 70)
        print("❌ TOKEN FORMAT INVALID")
        print("=" * 70)
        return False
    
    # Step 2: Test with API
    if not await test_token_with_api():
        print("\n" + "=" * 70)
        print("❌ TOKEN VERIFICATION FAILED")
        print("=" * 70)
        return False
    
    # Success!
    print("\n" + "=" * 70)
    print("✓ TOKEN VERIFICATION PASSED")
    print("=" * 70)
    print("\nYour token works! If you get 401 errors later:")
    print("  → Integration not added to specific database")
    print("  → Go to database → ... menu → Connections")
    print("  → Add your integration")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
