import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

# From your list_models.py, this is the 2026 stable workhorse
MODEL_ID = "gemini-2.5-flash"


async def run_investigation(query: str):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Define how to launch your 'Hands' (the MCP Server)
    server_params = StdioServerParameters(
        command="python",  # Or python3.13
        args=["commander_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            # Initialize the connection between Brain and Hands
            await mcp_session.initialize()

            # 1. Pull the 'Tool Menu' from your server and format it for Gemini
            # mcp_tools = await mcp_session.list_tools()
            # gemini_tools = [
            #     types.Tool(function_declarations=[
            #         types.FunctionDeclaration(
            #             name=t.name,
            #             description=t.description,
            #             parameters=t.inputSchema
            #         ) for t in mcp_tools.tools
            #     ])
            # ]

            # --- restructure for Gemini 2.5 ---
            # 1. Pull the 'Tool Menu' and sanitize it for Gemini 2026
            mcp_tools = await mcp_session.list_tools()
            gemini_tools = []

            for t in mcp_tools.tools:
                sanitized_params = t.inputSchema.copy()

                # Check for both snake_case and camelCase 'additional properties'
                for key in ["additional_properties", "additionalProperties"]:
                    if key in sanitized_params:
                        del sanitized_params[key]

                if "properties" in sanitized_params:
                    for prop in sanitized_params["properties"].values():
                        if isinstance(prop, dict):
                            for key in ["additional_properties", "additionalProperties"]:
                                if key in prop:
                                    del prop[key]

                gemini_tools.append(
                    types.Tool(function_declarations=[
                        types.FunctionDeclaration(
                            name=t.name,
                            description=t.description,
                            parameters=sanitized_params
                        )
                    ])
                )
            # --- End of restructure for Gemini 2.5 ---

            # 2. Start the Agentic Loop
            print(f"🚀 User Query: {query}")
            messages = [types.Content(role="user", parts=[types.Part(text=query)])]

            while True:
                # Ask Gemini what to do
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=messages,
                    config=types.GenerateContentConfig(tools=gemini_tools)
                )

                # Save Gemini's thought/decision
                messages.append(response.candidates[0].content)

                # Check if Gemini wants to use a tool
                tool_calls = [p.function_call for p in response.candidates[0].content.parts if p.function_call]

                if not tool_calls:
                    # If no tools are needed, Gemini has found the final answer
                    print(f"\n🏁 Final SRE Report:\n{response.text}")
                    break

                # If Gemini called tools, execute them one by one
                for call in tool_calls:
                    print(f"🛠️  AI is using tool: {call.name}({call.args})")

                    # Call the actual Python function in commander_server.py
                    result = await mcp_session.call_tool(call.name, call.args)
                    print(f"📊 Result: {result.content[0].text}")

                    # Feed the result back to Gemini so it can 'think' again
                    messages.append(types.Content(
                        role="user",
                        parts=[types.Part.from_function_response(
                            name=call.name,
                            response={'result': result.content[0].text}
                        )]
                    ))


if __name__ == "__main__":
    # Test an open-ended investigation
    asyncio.run(run_investigation("Check the cluster health. If anything is wrong, find out why."))