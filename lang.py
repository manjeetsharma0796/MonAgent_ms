import json
import getpass
import os
from dotenv import load_dotenv
from langchain.tools import tool
load_dotenv() 

print(os.environ.get("GOOGLE_API_KEY"))

if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("GOOGLE_API_KEY")


from langchain.chat_models import init_chat_model

# model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
# res = model.invoke("Hello, world!")
# print(res.content)
from web3 import Web3

# Polygon RPC endpoint
POLYGON_RPC = "https://polygon-rpc.com/"
w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))

# USDC contract address on Polygon
USDC_ADDRESS = Web3.to_checksum_address("0x1379E8886A944d2D9d440b3d88DF536Aea08d9F3")

# Minimal ERC20 ABI to get balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

@tool
def get_usdc_balance(address: str) -> str:
  """
    Fetch the USDC token balance for a given wallet address on the Polygon blockchain.

    Parameters:
    -----------
    address : str
        The wallet address (Ethereum-style hex string) to query the USDC balance for.

    Returns:
    --------
    str
        A human-readable string showing the USDC balance for the address on Polygon.
        Returns an error message if the address is invalid or the query fails.

    Example:
    --------
    >>> get_usdc_balance_polygon("0x1234...abcd")
    "USDC balance of 0x1234...abcd on Polygon: 150.25 USDC"
  """
  if not Web3.is_address(address):
      return "Invalid wallet address."

  address = Web3.to_checksum_address(address)
  contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
  balance = contract.functions.balanceOf(address).call()

    # USDC has 6 decimals
  decimals = 6
  readable_balance = balance / (10 ** decimals)

  return f"USDC balance of {address} on Polygon: {readable_balance} USDC"


@tool
def add(a: int, b: int) -> int:
    """Adds two numbers together"""
    return a + b

@tool
def sub(a: int, b: int) -> int:
    """Substract two numbers together"""
    return a - b

@tool
def mul(a: int, b: int) -> int:
    """Multiplies two numbers together"""
    return a * b


tools = [add, sub, mul, get_usdc_balance]

#From Youtube video https://youtu.be/zCwuAlpQKTM
from langchain.chat_models import init_chat_model

#ChatGoogleGenerativeAI(model="gemini-2.0-flash").bind_tools(tools)
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
print("eoijfowiejfwoifj")
llm = init_chat_model(model="gemini-2.0-flash",  model_provider="google_genai")

prompt = ChatPromptTemplate.from_messages([
    ("system", "you are helpful agent"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])
agent = create_tool_calling_agent(llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# response = agent_executor.invoke({"input": "What balance of 0xB702203B9FD0ee85aeDB9d314C075D480d716635"})
response = agent_executor.invoke({"input": "what ist he sum of 1 and 2?"})


print(response['output'])

