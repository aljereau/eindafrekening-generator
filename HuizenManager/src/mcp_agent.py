import asyncio
import os
from typing import List, Dict, Any, Callable, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPSQLAgent:
    """
    Standard MCP Client that connects to an MCP SQLite Server.
    Uses the official 'mcp' Python SDK to communicate via stdio.
    """
    
    def __init__(self, db_path: str, llm_callback: Callable[[List[Dict]], str]):
        self.db_path = os.path.abspath(db_path)
        self.llm_callback = llm_callback
        
    async def _run_mcp_query(self, sql_query: str) -> List[Dict]:
        """
        Connects to the MCP server and executes the query using the standard protocol.
        """
        # Define server parameters (npx command)
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "mcp-server-sqlite-npx", self.db_path],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()
                
                # List tools to find the right one (usually 'read_query')
                tools = await session.list_tools()
                query_tool = next((t for t in tools.tools if t.name == "read_query"), None)
                
                if not query_tool:
                    raise Exception(f"Tool 'read_query' not found on MCP server. Available: {[t.name for t in tools.tools]}")
                
                # Execute tool
                result = await session.call_tool("read_query", arguments={"query": sql_query})
                
                # Parse result (MCP returns TextContent or similar)
                # Usually result.content is a list of content blocks
                if result.content and len(result.content) > 0:
                    text_content = result.content[0].text
                    import json
                    try:
                        parsed_results = json.loads(text_content)
                        # 3. Check for execution errors
                        # API might return [{"error": "..."}] or [{"result": "Error: ..."}]
                        if isinstance(parsed_results, list) and len(parsed_results) > 0:
                            first_row = parsed_results[0]
                            if "error" in first_row:
                                raise Exception(first_row["error"])
                            if "result" in first_row and str(first_row["result"]).startswith("Error:"):
                                raise Exception(first_row["result"])
                        return parsed_results
                    except json.JSONDecodeError:
                        # If not JSON, it might be a single string result or an error message
                        # Try to detect error messages even if not JSON
                        if text_content.strip().lower().startswith("error:"):
                            raise Exception(text_content.strip())
                        return [{"result": text_content}] # Fallback if not JSON
                return []

    def process_query(self, user_question: str) -> Dict:
        """
        Synchronous wrapper for the async MCP interaction.
        """
        return asyncio.run(self._process_query_async(user_question))

    async def _process_query_async(self, user_question: str) -> Dict:
        """
        Async logic: NL -> SQL (LLM) -> Execute (MCP Server).
        """
        # We need schema for the LLM to generate SQL.
        # Ideally we ask the MCP server for schema too!
        # server-sqlite has 'list_tables' and 'describe_table'?
        # For speed, let's just use a cached schema or ask server.
        # Let's try to ask server for schema to be fully "MCP native".
        
        schema_text = "Schema loading..."
        
        # Connect to get schema first
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "mcp-server-sqlite-npx", self.db_path],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Get tables
                tables_result = await session.call_tool("list_tables", arguments={})
                # Parse tables... this might be verbose. 
                # For now, to save time/complexity in this turn, I will rely on the 
                # fact that we know the schema or can fetch it via standard SQL if needed.
                # But let's stick to the previous pattern: use IntelligenceAPI for schema (fast local) 
                # OR just run a query to get schema via MCP.
                # "SELECT sql FROM sqlite_master" works via read_query too!
                
                schema_result = await session.call_tool("read_query", arguments={"query": "SELECT sql FROM sqlite_master WHERE type='table'"})
                if schema_result.content:
                    schema_text = schema_result.content[0].text
        
        system_prompt = f"""
        You are a SQL Generator.
        Task: Convert the user's question into a valid SQLite query.
        
        Schema:
        {schema_text}
        
        CRITICAL RULES:
        1. Output ONLY the raw SQL query.
        2. DO NOT output any text, explanations, or markdown before or after the SQL.
        3. Start the response immediately with 'SELECT'.
        4. Use DATE('now') for current date.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Generate SQL (Client-side Intelligence)
                sql_query = self.llm_callback(messages)
                
                # Robust Parsing for Chatty Models
                import re
                
                # 1. Try to find content in ```sql ... ``` blocks
                code_blocks = re.findall(r'```sql\s*(.*?)\s*```', sql_query, re.DOTALL)
                if not code_blocks:
                    # Try generic code blocks
                    code_blocks = re.findall(r'```\s*(.*?)\s*```', sql_query, re.DOTALL)
                    
                if code_blocks:
                    # Use the last block as it's usually the final answer
                    sql_query = code_blocks[-1].strip()
                else:
                    # 2. If no blocks, try to find a raw SELECT statement
                    clean_query = sql_query.strip()
                    if not clean_query.upper().startswith("SELECT"):
                        # Try to find the first SELECT
                        match = re.search(r'(SELECT.*)', sql_query, re.IGNORECASE | re.DOTALL)
                        if match:
                            sql_query = match.group(1).strip()
                
                # Final cleanup
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
                
                print(f"🔍 MCP Generated SQL (Attempt {attempt+1}): {sql_query}")
                
                # Execute via MCP Server
                results = await self._run_mcp_query(sql_query)
                
                # Format with tabulate if results exist
                formatted_table = ""
                if results and isinstance(results, list) and len(results) > 0:
                    try:
                        from tabulate import tabulate
                        # Assuming results is a list of dicts
                        headers = results[0].keys()
                        rows = [r.values() for r in results]
                        formatted_table = tabulate(rows, headers=headers, tablefmt="psql")
                    except ImportError:
                        formatted_table = "Tabulate not installed."
                    except Exception as e:
                        formatted_table = f"Error formatting table: {e}"

                return {
                    "success": True,
                    "sql": sql_query,
                    "results": results,
                    "formatted_table": formatted_table
                }
                
            except Exception as e:
                last_error = str(e)
                print(f"⚠️ SQL Execution Failed: {last_error}")
                
                # Feed error back to LLM for correction
                messages.append({"role": "assistant", "content": sql_query})
                messages.append({"role": "user", "content": f"The query failed with error: {last_error}. Please fix the SQL and try again. Return ONLY the fixed SQL."})
                
        return {"success": False, "error": f"Failed after {max_retries} attempts. Last error: {last_error}"}
