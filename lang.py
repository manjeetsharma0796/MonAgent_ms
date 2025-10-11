


import json
import getpass
import os
from dotenv import load_dotenv
from langchain.tools import tool
import serpapi
load_dotenv() 

if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("GOOGLE_API_KEY")


from langchain.chat_models import init_chat_model

# model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
# res = model.invoke("Hello, world!")
# print(res.content)

from web3 import Web3

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



# Web search tool using SerpAPI
@tool
def web_search(query: str) -> str:
    """
    Search the web using SerpAPI and return the top result snippet.
    """
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        return "SerpAPI key not set. Please set SERPAPI_API_KEY in your environment."
    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": 1
    }
    try:
        client = serpapi.Client(api_key=api_key)
        results = client.search(params)
        results = results.as_dict() if hasattr(results, 'as_dict') else results
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "organic_results" in results and results["organic_results"]:
            snippet = results["organic_results"][0].get("snippet")
            if snippet:
                return snippet
            return results["organic_results"][0].get("title", "No result found.")
        return "No relevant web result found."
    except Exception as e:
        return f"Web search failed: {e}"


# EVM chain RPC endpoints (add more as needed)
EVM_CHAINS = {
    "polygon": {
        "rpc": "https://polygon-rpc.com/",
        "explorer_api": "https://api.polygonscan.com/api",
        "explorer_key_env": "POLYGONSCAN_API_KEY"
    },
    "ethereum": {
        "rpc": "https://ethereum.publicnode.com",
        "explorer_api": "https://api.etherscan.io/api",
        "explorer_key_env": "ETHERSCAN_API_KEY"
    },
    "bsc": {
        "rpc": "https://bsc-dataseed.binance.org/",
        "explorer_api": "https://api.bscscan.com/api",
        "explorer_key_env": "BSCSCAN_API_KEY"
    },
    "arbitrum": {
        "rpc": "https://arb1.arbitrum.io/rpc",
        "explorer_api": "https://api.arbiscan.io/api",
        "explorer_key_env": "ARBISCAN_API_KEY"
    },
    "u2u_mainnet": {
        "rpc": "https://rpc-mainnet.u2u.xyz",
        "explorer_api": "",
        "explorer_key_env": ""
    },
    "u2u_testnet": {
        "rpc": "https://rpc-nebulas-testnet.u2u.xyz",
        "explorer_api": "",
        "explorer_key_env": ""
    },
    # Add more EVM chains here
}


# Minimal ERC-20 ABI for balance and metadata
ERC20_ABI = [
  {
    "constant": True,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "type": "function",
  },
  {
    "constant": True,
    "inputs": [],
    "name": "decimals",
    "outputs": [{"name": "", "type": "uint8"}],
    "type": "function",
  },
  {
    "constant": True,
    "inputs": [],
    "name": "symbol",
    "outputs": [{"name": "", "type": "string"}],
    "type": "function",
  },
]

# Common stablecoin addresses by chain
TOKEN_MAP = {
  "ethereum": {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  },
  "polygon": {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xC2132D05D31c914a87C6611C10748AEb04B58e8F",
  },
  "bsc": {
    "USDC": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
    "USDT": "0x55d398326f99059fF775485246999027B3197955",
  },
  "arbitrum": {
    "USDC": "0xFF970A61A04b1cA14834A43f5de4533eBDDB5CC8",  # USDC.e
    "USDT": "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",
  },
  "u2u_mainnet": {
  },
  "u2u_testnet": {
    "USDC": "0xfb11bba87bc7f418448df1fabb9400cafd590e6f",
    "USDT": "0x88ed59f4d491c7b90fe4efe6734c25193e1ca6ec",
  },
}

def _get_w3(chain: str) -> Web3:
  chain = chain.lower()
  rpc = EVM_CHAINS.get(chain, {}).get("rpc")
  if not rpc:
    raise ValueError(f"Unsupported chain: {chain}")
  return Web3(Web3.HTTPProvider(rpc))

def _get_native_symbol(chain: str) -> str:
  return {
    "polygon": "MATIC",
    "ethereum": "ETH",
    "bsc": "BNB",
    "arbitrum": "ETH",
    "u2u_mainnet": "U2U",
    "u2u_testnet": "U2U",
  }.get(chain, "Native")

def _erc20_balance(w3: Web3, token_address: str, wallet: str) -> tuple[float, int, str]:
  contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
  raw = contract.functions.balanceOf(Web3.to_checksum_address(wallet)).call()
  try:
    decimals = contract.functions.decimals().call()
  except Exception:
    decimals = 18
  try:
    symbol = contract.functions.symbol().call()
  except Exception:
    symbol = "TOKEN"
  human = raw / (10 ** decimals)
  return human, decimals, symbol

@tool
def get_balance(address: str, chain: str = "polygon", token: str | None = None) -> str:
  """
  Get balance for a wallet address on any supported EVM blockchain chain.
  
  Supported chains: polygon, ethereum, bsc, arbitrum, u2u_mainnet, u2u_testnet
  
  Parameters:
  - address: Wallet address to check balance for
  - chain: Blockchain network (default: "polygon"). 
    Use "u2u_mainnet" for U2U mainnet, "u2u_testnet" for U2U testnet
  - token: Token to check balance for
    - None or "native": Returns native token balance (MATIC, ETH, BNB, U2U)
    - Symbol (e.g., "USDC", "USDT"): Uses predefined token addresses for that chain
    - Contract address: Queries any ERC-20 token directly by contract address
  
  Examples:
  - "Get balance of 0x123... on u2u mainnet" -> chain="u2u_mainnet"
  - "Check U2U balance for wallet 0x123..." -> chain="u2u_mainnet", token="native"
  - "Show USDC balance on U2U" -> chain="u2u_mainnet", token="USDC"
  """
  try:
    w3 = _get_w3(chain)
  except Exception as e:
    return f"Unsupported chain or RPC error: {e}"
  if not Web3.is_address(address):
    return "Invalid wallet address."
  if token is None or str(token).lower() == "native":
    try:
      wei = w3.eth.get_balance(address)
      return f"{wei / 1e18} {_get_native_symbol(chain.lower())}"
    except Exception as e:
      return f"Failed to fetch native balance: {e}"
  token_str = str(token)
  # Resolve symbol to address if needed
  token_address = None
  if Web3.is_address(token_str):
    token_address = token_str
  else:
    token_address = TOKEN_MAP.get(chain.lower(), {}).get(token_str.upper())
  if not token_address:
    return f"Unknown token '{token}'. Provide a contract address or supported symbol."
  try:
    bal, _, sym = _erc20_balance(w3, token_address, address)
    return f"{bal} {sym}"
  except Exception as e:
    return f"Failed to fetch token balance: {e}"

# Helper to get balances for native token, USDC, and USDT only
# @tool
@tool
def get_main_balances(address: str, chain: str = "polygon") -> str:
    """
    Get main token balances (native + USDC + USDT) for a wallet address on any supported EVM chain.
    
    Supported chains: polygon, ethereum, bsc, arbitrum, u2u_mainnet, u2u_testnet
    
    Parameters:
    - address: Wallet address to check balances for
    - chain: Blockchain network (default: "polygon")
      Use "u2u_mainnet" for U2U mainnet, "u2u_testnet" for U2U testnet
    
    Returns:
    - Native token balance (MATIC, ETH, BNB, U2U)
    - USDC balance (if available on the chain)
    - USDT balance (if available on the chain)
    
    Examples:
    - "Show main balances for 0x123... on U2U mainnet" -> chain="u2u_mainnet"
    - "Get U2U wallet overview" -> chain="u2u_mainnet"
    - "Check all main tokens for wallet 0x123..." -> uses default chain
    """
    from web3 import Web3
    chain = chain.lower()
    if chain not in EVM_CHAINS:
        return f"Unsupported chain: {chain}. Supported: {list(EVM_CHAINS.keys())}"
    if not Web3.is_address(address):
        return "Invalid wallet address."
    # Native token balance
    try:
        w3 = _get_w3(chain)
        wei = w3.eth.get_balance(address)
        native_balance = wei / 1e18
        native_symbol = _get_native_symbol(chain)
    except Exception as e:
        return f"Failed to fetch native balance: {e}"
    # USDC & USDT via on-chain calls
    summary = [f"Native: {native_balance} {native_symbol}"]
    for sym in ["USDC", "USDT"]:
        token_addr = TOKEN_MAP.get(chain, {}).get(sym)
        if not token_addr:
            continue
        try:
            bal, _, _ = _erc20_balance(w3, token_addr, address)
            summary.append(f"{sym}: {bal}")
        except Exception:
            # Skip token if call fails
            pass
    return "\n".join(summary)

@tool
def get_wallet_transactions(address: str, chain: str = "polygon", limit: int = 10) -> str:
    """
    Show recent transactions (native and token) for a wallet address on any supported EVM chain.
    
    Supported chains: polygon, ethereum, bsc, arbitrum, u2u_mainnet, u2u_testnet
    
    Parameters:
    - address: Wallet address to get transaction history for
    - chain: Blockchain network (default: "polygon")
      Use "u2u_mainnet" for U2U mainnet, "u2u_testnet" for U2U testnet
    - limit: Maximum number of transactions to return (default: 10)
    
    Returns:
    - Transaction hash, direction (IN/OUT), value, block number, and timestamp
    
    Examples:
    - "Show transactions for 0x123... on U2U mainnet" -> chain="u2u_mainnet"
    - "Get U2U transaction history" -> chain="u2u_mainnet"
    - "Show last 20 transactions for wallet 0x123..." -> limit=20
    
    Note: Requires explorer API key for transaction data. U2U chains may have limited explorer support.
    """
    from web3 import Web3
    import requests
    chain = chain.lower()
    if chain not in EVM_CHAINS:
        return f"Unsupported chain: {chain}. Supported: {list(EVM_CHAINS.keys())}"
    if not Web3.is_address(address):
        return "Invalid wallet address."
    explorer_api = EVM_CHAINS[chain]["explorer_api"]
    api_key = os.environ.get(EVM_CHAINS[chain]["explorer_key_env"], "")
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "sort": "desc"
    }
    if api_key:
        params["apikey"] = api_key
        try:
            resp = requests.get(explorer_api, params=params, timeout=10)
            data = resp.json()
            if data.get("status") != "1":
                return f"No transactions found or error: {data.get('message')}"
            txs = data["result"][:limit]
            summary = []
            for tx in txs:
                direction = "IN" if tx["to"].lower() == address.lower() else "OUT"
                value = int(tx["value"]) / 1e18
                summary.append(f"{tx['hash'][:10]}... | {direction} | {value} | block: {tx['blockNumber']} | time: {tx['timeStamp']}")
            return "\n".join(summary)
        except Exception as e:
            return f"Failed to fetch transactions: {e}"
    else:
        return f"No explorer API key set for {chain}. Please set the appropriate API key in the environment."

tools = [add, sub, mul, web_search, get_balance, get_main_balances, get_wallet_transactions]

#From Youtube video https://youtu.be/zCwuAlpQKTM
from langchain.chat_models import init_chat_model

#ChatGoogleGenerativeAI(model="gemini-2.0-flash").bind_tools(tools)
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder

llm = init_chat_model(model="gemini-2.0-flash",  model_provider="google_genai")


prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful blockchain and web search agent. You can check wallet balances, transaction history, and search the web. You support multiple blockchain networks including Polygon, Ethereum, BSC, Arbitrum, and U2U (both mainnet and testnet). When users mention 'U2U mainnet' or 'U2U', use chain='u2u_mainnet'. When they mention 'U2U testnet', use chain='u2u_testnet'. Be friendly and chatty like a human. If you don't know something, say 'I don't know' or 'I am not sure'. Never reveal that you are an AI or mention your model."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])
agent = create_tool_calling_agent(llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# response = agent_executor.invoke({"input": "What balance of 0xB702203B9FD0ee85aeDB9d314C075D480d716635"})
__all__ = ["agent_executor"]

