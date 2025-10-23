import json
import os
from dotenv import load_dotenv
from langchain.tools import tool
import serpapi
load_dotenv() 

# Check for required API key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required. Please set it in your environment.")


from langchain.chat_models import init_chat_model

# model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
# res = model.invoke("Hello, world!")
# print(res.content)

from web3 import Web3
from eth_account import Account
from eth_utils import to_checksum_address

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
        return json.dumps({
            "action_type": "web_search_result",
            "status": "error",
            "message": "SerpAPI key not set. Please set SERPAPI_API_KEY in your environment."
        })
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
            snippet = results["answer_box"]["answer"]
        elif "organic_results" in results and results["organic_results"]:
            snippet = results["organic_results"][0].get("snippet", "No snippet found.")
        else:
            snippet = "No relevant web result found."

        return json.dumps({
            "action_type": "web_search_result",
            "status": "success",
            "query": query,
            "result_snippet": snippet
        })
    except Exception as e:
        return json.dumps({
            "action_type": "web_search_result",
            "status": "error",
            "query": query,
            "error": f"Web search failed: {e}"
        })


# EVM chain RPC endpoints (add more as needed)
# Corrected Ethereum RPC and U2U RPCs (removed trailing spaces)
EVM_CHAINS = {
    "polygon": {
        "rpc": "https://polygon-rpc.com/",  # Confirmed from webpage
        "chain_id": 137,
        "explorer_api": "https://api.polygonscan.com/api",
        "explorer_key_env": "POLYGONSCAN_API_KEY",
        "native_symbol": "MATIC" # Added for gas fee estimation
    },
    "ethereum": {
        "rpc": "https://ethereum-rpc.publicnode.com", # Corrected from webpage info
        "chain_id": 1,
        "explorer_api": "https://api.etherscan.io/api",
        "explorer_key_env": "ETHERSCAN_API_KEY",
        "native_symbol": "ETH"
    },
    "bsc": {
        "rpc": "https://bsc-dataseed.binance.org/", # Standard BSC endpoint
        "chain_id": 56,
        "explorer_api": "https://api.bscscan.com/api",
        "explorer_key_env": "BSCSCAN_API_KEY",
        "native_symbol": "BNB"
    },
    "arbitrum": {
        "rpc": "https://arb1.arbitrum.io/rpc", # Standard Arbitrum endpoint
        "chain_id": 42161,
        "explorer_api": "https://api.arbiscan.io/api",
        "explorer_key_env": "ARBISCAN_API_KEY",
        "native_symbol": "ETH"
    },
    "u2u_mainnet": {
        "rpc": "https://rpc-mainnet.u2u.xyz", # Removed trailing spaces
        "chain_id": 39,
        "explorer_api": "",
        "explorer_key_env": "",
        "native_symbol": "U2U"
    },
    "u2u_testnet": {
        "rpc": "https://rpc-nebulas-testnet.u2u.xyz", # Removed trailing spaces
        "chain_id": 2484,
        "explorer_api": "",
        "explorer_key_env": "",
        "native_symbol": "U2U"
    },
    "monad_testnet": {
        "rpc": "https://testnet-rpc.monad.xyz",  # Monad testnet RPC
        "chain_id": 1234,  # Monad testnet chain ID (placeholder)
        "explorer_api": "",
        "explorer_key_env": "",
        "native_symbol": "MONAD"
    },
    # Add more EVM chains here
}


# Minimal ERC-20 ABI for balance, transfer, and approval
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
  {
    "constant": False,
    "inputs": [
      {"name": "spender", "type": "address"},
      {"name": "value", "type": "uint256"}
    ],
    "name": "approve",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
  },
  {
    "constant": False,
    "inputs": [
      {"name": "to", "type": "address"},
      {"name": "value", "type": "uint256"}
    ],
    "name": "transfer",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
  }
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
    # Add USDC/USDT addresses for U2U mainnet if available
  },
  "u2u_testnet": {
    "USDC": "0xfb11bba87bc7f418448df1fabb9400cafd590e6f",
    "USDT": "0x88ed59f4d491c7b90fe4efe6734c25193e1ca6ec", # Corrected typo from initial code
  },
}

def _get_w3(chain: str) -> Web3:
  chain = chain.lower()
  rpc = EVM_CHAINS.get(chain, {}).get("rpc")
  if not rpc:
    raise ValueError(f"Unsupported chain: {chain}")
  return Web3(Web3.HTTPProvider(rpc))

def _get_native_symbol(chain: str) -> str:
  return EVM_CHAINS.get(chain, {}).get("native_symbol", "Native")

def _get_chain_id(chain: str) -> int:
  return EVM_CHAINS.get(chain, {}).get("chain_id", 0)

def _erc20_balance(w3: Web3, token_address: str, wallet: str) -> tuple[float, int, str]:
  contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
  raw = contract.functions.balanceOf(Web3.to_checksum_address(wallet)).call()
  try:
    decimals = contract.functions.decimals().call()
  except Exception:
    # Default to 18 decimals if the call fails
    decimals = 18
  try:
    symbol = contract.functions.symbol().call()
  except Exception:
    # Default to "TOKEN" if the call fails
    symbol = "TOKEN"
  # Convert raw balance to human-readable format
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
  - "show USDC balance on U2U" -> chain="u2u_mainnet", token="USDC"
  """
  try:
    w3 = _get_w3(chain)
  except Exception as e:
    return json.dumps({
        "action_type": "balance_query",
        "status": "error",
        "query_type": "generic_balance",
        "address": address,
        "chain": chain,
        "token": token,
        "error": f"Unsupported chain or RPC error: {e}"
    })
  
  if not Web3.is_address(address):
    return json.dumps({
        "action_type": "balance_query",
        "status": "error",
        "query_type": "generic_balance",
        "address": address,
        "chain": chain,
        "token": token,
        "error": "Invalid wallet address."
    })
  
  if token is None or str(token).lower() == "native":
    try:
      wei = w3.eth.get_balance(address)
      balance = wei / 1e18
      symbol = _get_native_symbol(chain.lower())
      return json.dumps({
          "action_type": "balance_query",
          "status": "success",
          "query_type": "native_balance",
          "address": address,
          "chain": chain,
          "balance": balance,
          "symbol": symbol,
          "message": f"Balance: {balance} {symbol}"
      })
    except Exception as e:
      return json.dumps({
          "action_type": "balance_query",
          "status": "error",
          "query_type": "native_balance",
          "address": address,
          "chain": chain,
          "error": f"Failed to fetch native balance: {e}"
      })
  
  token_str = str(token)
  # Resolve symbol to address if needed
  token_address = None
  if Web3.is_address(token_str):
    token_address = token_str
  else:
    token_address = TOKEN_MAP.get(chain.lower(), {}).get(token_str.upper())
  
  if not token_address:
    return json.dumps({
        "action_type": "balance_query",
        "status": "error",
        "query_type": "token_balance",
        "address": address,
        "chain": chain,
        "token": token,
        "error": f"Unknown token '{token}'. Provide a contract address or supported symbol."
    })
  
  try:
    bal, _, sym = _erc20_balance(w3, token_address, address)
    return json.dumps({
        "action_type": "balance_query",
        "status": "success",
        "query_type": "token_balance",
        "address": address,
        "chain": chain,
        "token_address": token_address,
        "balance": bal,
        "symbol": sym,
        "message": f"Balance: {bal} {sym}"
    })
  except Exception as e:
    return json.dumps({
        "action_type": "balance_query",
        "status": "error",
        "query_type": "token_balance",
        "address": address,
        "chain": chain,
        "token_address": token_address,
        "error": f"Failed to fetch token balance: {e}"
    })

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
        return json.dumps({
            "action_type": "balance_query",
            "status": "error",
            "query_type": "main_balances",
            "address": address,
            "chain": chain,
            "error": f"Unsupported chain: {chain}. Supported: {list(EVM_CHAINS.keys())}"
        })
    if not Web3.is_address(address):
        return json.dumps({
            "action_type": "balance_query",
            "status": "error",
            "query_type": "main_balances",
            "address": address,
            "chain": chain,
            "error": "Invalid wallet address."
        })
    # Native token balance
    try:
        w3 = _get_w3(chain)
        wei = w3.eth.get_balance(address)
        native_balance = wei / 1e18
        native_symbol = _get_native_symbol(chain)
    except Exception as e:
        return json.dumps({
            "action_type": "balance_query",
            "status": "error",
            "query_type": "main_balances",
            "address": address,
            "chain": chain,
            "error": f"Failed to fetch native balance: {e}"
        })
    # USDC & USDT via on-chain calls
    balances = {
        "native": {
            "symbol": native_symbol,
            "balance": native_balance
        }
    }
    for sym in ["USDC", "USDT"]:
        token_addr = TOKEN_MAP.get(chain, {}).get(sym)
        if not token_addr:
            continue
        try:
            bal, _, _ = _erc20_balance(w3, token_addr, address)
            balances[sym.lower()] = {
                "symbol": sym,
                "balance": bal,
                "token_address": token_addr
            }
        except Exception:
            # Skip token if call fails
            pass
    
    return json.dumps({
        "action_type": "balance_query",
        "status": "success",
        "query_type": "main_balances",
        "address": address,
        "chain": chain,
        "balances": balances
    })

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
        return json.dumps({
            "action_type": "transaction_history",
            "status": "error",
            "address": address,
            "chain": chain,
            "error": f"Unsupported chain: {chain}. Supported: {list(EVM_CHAINS.keys())}"
        })
    if not Web3.is_address(address):
        return json.dumps({
            "action_type": "transaction_history",
            "status": "error",
            "address": address,
            "chain": chain,
            "error": "Invalid wallet address."
        })
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
                return json.dumps({
                    "action_type": "transaction_history",
                    "status": "error",
                    "address": address,
                    "chain": chain,
                    "error": f"No transactions found or error: {data.get('message')}"
                })
            txs = data["result"][:limit]
            summary = []
            for tx in txs:
                direction = "IN" if tx["to"].lower() == address.lower() else "OUT"
                value = int(tx["value"]) / 1e18
                summary.append({
                    "hash": tx['hash'],
                    "direction": direction,
                    "value": value,
                    "block_number": int(tx['blockNumber']),
                    "timestamp": int(tx['timeStamp'])
                })
            return json.dumps({
                "action_type": "transaction_history",
                "status": "success",
                "address": address,
                "chain": chain,
                "transactions": summary
            })
        except Exception as e:
            return json.dumps({
                "action_type": "transaction_history",
                "status": "error",
                "address": address,
                "chain": chain,
                "error": f"Failed to fetch transactions: {e}"
            })
    else:
        return json.dumps({
            "action_type": "transaction_history",
            "status": "error",
            "address": address,
            "chain": chain,
            "error": f"No explorer API key set for {chain}. Please set the appropriate API key in the environment."
        })

# --- RESPONSE STANDARDIZATION FUNCTIONS ---

def create_standard_response(action_type: str, data: dict, message: str = None) -> str:
    """
    Creates a standardized response format for all tool functions
    
    Args:
        action_type: The type of response (transaction, chat, error, etc.)
        data: The main data payload
        message: Optional human-readable message
    
    Returns:
        JSON string with standardized format
    """
    response = {
        "action_type": action_type,
        **data
    }
    if message:
        response["message"] = message
    return json.dumps(response, ensure_ascii=False)

def normalize_agent_response(output: str) -> dict:
    """
    Normalizes agent responses to consistent format
    
    Args:
        output: Raw output from agent
    
    Returns:
        Standardized response dictionary
    """
    try:
        import re
        
        # Step 1: Extract JSON from markdown if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', output, re.DOTALL)
        if json_match:
            output = json_match.group(1)
        
        # Step 2: Parse JSON
        parsed = json.loads(output)
        
        # Step 3: Ensure consistent structure
        if isinstance(parsed, dict):
            if "action_type" not in parsed:
                parsed["action_type"] = "chat"
            return parsed
        else:
            return {"action_type": "chat", "message": output}
            
    except (json.JSONDecodeError, TypeError):
        return {"action_type": "chat", "message": output}

# --- NEW FUNCTIONS START ---

@tool
def prepare_native_transfer(sender: str, recipient: str, amount: float, chain: str = "polygon") -> str:
    """
    Prepares an unsigned native token (ETH, MATIC, BNB, U2U, MONAD, etc.) transfer transaction.
    
    Supported chains: polygon, ethereum, bsc, arbitrum, u2u_mainnet, u2u_testnet, monad_testnet
    
    Parameters:
    - sender: The address sending the tokens.
    - recipient: The address receiving the tokens.
    - amount: The amount of native token to send.
    - chain: The blockchain network (default: "polygon").
      Use "monad_testnet" for Monad testnet transactions.
    
    Returns:
    - JSON string with action_type "transaction" and unsigned transaction details
    """
    try:
        w3 = _get_w3(chain)
        if not Web3.is_address(sender) or not Web3.is_address(recipient):
            return json.dumps({
                "action_type": "transaction",
                "status": "error",
                "chain": chain,
                "from": sender,
                "to": recipient,
                "amount": amount,
                "unit": _get_native_symbol(chain),
                "error": "Invalid sender or recipient address."
            })
        
        sender_checksum = to_checksum_address(sender)
        recipient_checksum = to_checksum_address(recipient)
        
        # Estimate gas
        estimated_gas = w3.eth.estimate_gas({
            'from': sender_checksum,
            'to': recipient_checksum,
            'value': w3.to_wei(amount, 'ether')
        })
        
        # Get current block number for nonce
        current_block_number = w3.eth.get_block_number()
        nonce = w3.eth.get_transaction_count(sender_checksum, block_identifier=current_block_number)
        
        # Get gas price
        gas_price = w3.eth.gas_price
        
        # Get chain ID and native symbol
        chain_id = _get_chain_id(chain)
        native_symbol = _get_native_symbol(chain)
        
        # Prepare the unsigned transaction
        unsigned_tx = {
            'chainId': chain_id,
            'from': sender_checksum,
            'to': recipient_checksum,
            'value': str(w3.to_wei(amount, 'ether')),
            'token': native_symbol,
            'gas': str(estimated_gas),
            'gasPrice': str(gas_price),
            'nonce': nonce
        }

        # Format amount to avoid scientific notation
        formatted_amount = f"{amount:.10f}".rstrip('0').rstrip('.')
        
        return create_standard_response(
            action_type="transaction",
            data={
                "chain": chain,
                "unsigned_tx": unsigned_tx
            },
            message=f"Initiate MetaMask transaction to send {formatted_amount} {native_symbol} from {sender} to {recipient}."
        )
    except Exception as e:
        # Format amount to avoid scientific notation
        formatted_amount = f"{amount:.10f}".rstrip('0').rstrip('.')
        
        return create_standard_response(
            action_type="error",
            data={
                "chain": chain,
                "from": sender,
                "to": recipient,
                "amount": formatted_amount,
                "unit": _get_native_symbol(chain),
                "error": f"Failed to prepare native transfer: {str(e)}"
            }
        )

@tool
def prepare_token_transfer(sender: str, recipient: str, token_address: str, amount: float, chain: str = "polygon") -> str:
    """
    Prepares an unsigned ERC-20 token transfer transaction.
    
    Supported chains: polygon, ethereum, bsc, arbitrum, u2u_mainnet, u2u_testnet, monad_testnet
    
    Parameters:
    - sender: The address sending the tokens.
    - recipient: The address receiving the tokens.
    - token_address: The contract address of the ERC-20 token (user must provide this).
    - amount: The amount of tokens to send (in human-readable units).
    - chain: The blockchain network (default: "polygon").
      Use "monad_testnet" for Monad testnet transactions.
    
    Returns:
    - JSON string with action_type "transaction" and unsigned transaction details
    """
    try:
        w3 = _get_w3(chain)
        if not Web3.is_address(sender) or not Web3.is_address(recipient) or not Web3.is_address(token_address):
            return json.dumps({
                "action_type": "transaction",
                "status": "error",
                "chain": chain,
                "from": sender,
                "to": recipient,
                "token_address": token_address,
                "amount": amount,
                "error": "Invalid sender, recipient, or token address."
            })
        
        sender_checksum = to_checksum_address(sender)
        recipient_checksum = to_checksum_address(recipient)
        token_checksum = to_checksum_address(token_address)
        
        # Get token contract
        token_contract = w3.eth.contract(address=token_checksum, abi=ERC20_ABI)
        
        # Get token decimals to convert amount and symbol
        try:
            decimals = token_contract.functions.decimals().call()
            symbol = token_contract.functions.symbol().call()
        except Exception as e:
            return json.dumps({
                "action_type": "transaction",
                "status": "error",
                "chain": chain,
                "from": sender,
                "to": recipient,
                "token_address": token_address,
                "amount": amount,
                "error": f"Failed to read token metadata (decimals/symbol): {e}"
            })
        
        amount_wei = int(amount * (10 ** decimals))
        
        # Estimate gas for the transfer function
        estimated_gas = token_contract.functions.transfer(recipient_checksum, amount_wei).estimate_gas({
            'from': sender_checksum
        })
        
        # Get current block number for nonce
        current_block_number = w3.eth.get_block_number()
        nonce = w3.eth.get_transaction_count(sender_checksum, block_identifier=current_block_number)
        
        # Get gas price
        gas_price = w3.eth.gas_price
        
        # Get chain ID
        chain_id = _get_chain_id(chain)
        
        # Prepare the unsigned transaction for the transfer function
        unsigned_tx = token_contract.functions.transfer(recipient_checksum, amount_wei).build_transaction({
            'from': sender_checksum,
            'gas': estimated_gas,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': chain_id
        })

        # Remove 'data' field from the unsigned_tx dict if present (it's usually auto-generated)
        unsigned_tx.pop('data', None)
        # Remove 'value' field as it's a token transfer, not native
        unsigned_tx.pop('value', None)

        # Format the unsigned transaction to match the native transfer format
        formatted_tx = {
            'chainId': chain_id,
            'from': sender_checksum,
            'to': token_checksum,
            'value': "0",  # Token transfers have value 0
            'token': symbol,
            'gas': str(estimated_gas),
            'gasPrice': str(gas_price),
            'nonce': nonce,
            'data': token_contract.functions.transfer(recipient_checksum, amount_wei).build_transaction({'from': sender_checksum})['data']
        }

        # Format amount to avoid scientific notation
        formatted_amount = f"{amount:.10f}".rstrip('0').rstrip('.')
        
        return create_standard_response(
            action_type="transaction",
            data={
                "chain": chain,
                "unsigned_tx": formatted_tx
            },
            message=f"Initiate MetaMask transaction to send {formatted_amount} {symbol} from {sender} to {recipient}."
        )
    except Exception as e:
        # Format amount to avoid scientific notation
        formatted_amount = f"{amount:.10f}".rstrip('0').rstrip('.')
        
        return create_standard_response(
            action_type="error",
            data={
                "chain": chain,
                "from": sender,
                "to": recipient,
                "token_address": token_address,
                "amount": formatted_amount,
                "error": f"Failed to prepare token transfer: {e}"
            }
        )

@tool
def prepare_token_approval(owner: str, spender: str, token_address: str, amount: float, chain: str = "polygon") -> str:
    """
    Prepares an unsigned ERC-20 token approval transaction.
    
    Parameters:
    - owner: The address owning the tokens.
    - spender: The address approved to spend the tokens.
    - token_address: The contract address of the ERC-20 token.
    - amount: The amount of tokens to approve (in human-readable units).
    - chain: The blockchain network (default: "polygon").
    """
    try:
        w3 = _get_w3(chain)
        if not Web3.is_address(owner) or not Web3.is_address(spender) or not Web3.is_address(token_address):
            return json.dumps({
                "action_type": "transaction",
                "status": "error",
                "chain": chain,
                "owner": owner,
                "spender": spender,
                "token_address": token_address,
                "amount": amount,
                "error": "Invalid owner, spender, or token address."
            })
        
        owner_checksum = to_checksum_address(owner)
        spender_checksum = to_checksum_address(spender)
        token_checksum = to_checksum_address(token_address)
        
        # Get token contract
        token_contract = w3.eth.contract(address=token_checksum, abi=ERC20_ABI)
        
        # Get token decimals to convert amount and symbol
        try:
            decimals = token_contract.functions.decimals().call()
            symbol = token_contract.functions.symbol().call()
        except Exception as e:
            return json.dumps({
                "action_type": "transaction",
                "status": "error",
                "chain": chain,
                "owner": owner,
                "spender": spender,
                "token_address": token_address,
                "amount": amount,
                "error": f"Failed to read token metadata (decimals/symbol): {e}"
            })
        
        amount_wei = int(amount * (10 ** decimals))
        
        # Estimate gas for the approve function
        estimated_gas = token_contract.functions.approve(spender_checksum, amount_wei).estimate_gas({
            'from': owner_checksum
        })
        
        # Get current block number for nonce
        current_block_number = w3.eth.get_block_number()
        nonce = w3.eth.get_transaction_count(owner_checksum, block_identifier=current_block_number)
        
        # Get gas price
        gas_price = w3.eth.gas_price
        
        # Get chain ID
        chain_id = _get_chain_id(chain)
        
        # Prepare the unsigned transaction for the approve function
        unsigned_tx = token_contract.functions.approve(spender_checksum, amount_wei).build_transaction({
            'from': owner_checksum,
            'gas': estimated_gas,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': chain_id
        })

        # Remove 'data' field from the unsigned_tx dict if present (it's usually auto-generated)
        unsigned_tx.pop('data', None)
        # Remove 'value' field as it's an approval, not a transfer
        unsigned_tx.pop('value', None)

        # Format the unsigned transaction to match the native transfer format
        formatted_tx = {
            'chainId': chain_id,
            'from': owner_checksum,
            'to': token_checksum,
            'value': "0",  # Approvals have value 0
            'token': symbol,
            'gas': str(estimated_gas),
            'gasPrice': str(gas_price),
            'nonce': nonce,
            'data': token_contract.functions.approve(spender_checksum, amount_wei).build_transaction({'from': owner_checksum})['data']
        }

        # Format amount to avoid scientific notation
        formatted_amount = f"{amount:.10f}".rstrip('0').rstrip('.')
        
        return create_standard_response(
            action_type="transaction",
            data={
                "chain": chain,
                "unsigned_tx": formatted_tx
            },
            message=f"Initiate MetaMask transaction to approve {spender} to spend {formatted_amount} {symbol} on behalf of {owner}."
        )
    except Exception as e:
        # Format amount to avoid scientific notation
        formatted_amount = f"{amount:.10f}".rstrip('0').rstrip('.')
        
        return create_standard_response(
            action_type="error",
            data={
                "chain": chain,
                "owner": owner,
                "spender": spender,
                "token_address": token_address,
                "amount": formatted_amount,
                "error": f"Failed to prepare token approval: {e}"
            }
        )

@tool
def check_transaction_status(tx_hash: str, chain: str = "polygon") -> str:
    """
    Checks the status (success/failure) of a given transaction hash.
    
    Parameters:
    - tx_hash: The transaction hash to check.
    - chain: The blockchain network (default: "polygon").
    """
    try:
        w3 = _get_w3(chain)
        if not Web3.is_hex_encoded(tx_hash) or len(tx_hash) != 66: # Standard tx hash length
            return json.dumps({
                "action_type": "transaction_status",
                "status": "error",
                "tx_hash": tx_hash,
                "chain": chain,
                "error": "Invalid transaction hash format."
            })
        
        # Get the transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        if receipt is None:
             return json.dumps({
                "action_type": "transaction_status",
                "status": "pending",
                "tx_hash": tx_hash,
                "chain": chain,
                "message": "Transaction is still pending or not found."
            })

        status_code = receipt['status']
        success = (status_code == 1)
        
        return json.dumps({
            "action_type": "transaction_status",
            "status": "success",
            "tx_hash": tx_hash,
            "chain": chain,
            "is_successful": success,
            "block_number": receipt['blockNumber'],
            "gas_used": receipt['gasUsed'],
            "message": f"Transaction {'succeeded' if success else 'failed'}."
        })
    except Exception as e:
        return json.dumps({
            "action_type": "transaction_status",
            "status": "error",
            "tx_hash": tx_hash,
            "chain": chain,
            "error": f"Failed to check transaction status: {e}"
        })

@tool
def estimate_gas(sender: str, recipient: str, amount: float, chain: str = "polygon", token_address: str | None = None) -> str:
    """
    Estimates the gas required for a native transfer or contract interaction.
    
    Parameters:
    - sender: The address initiating the transaction.
    - recipient: The address receiving the tokens or interacting with the contract.
    - amount: The amount of native token to send (ignored if token_address is provided).
    - chain: The blockchain network (default: "polygon").
    - token_address: Optional. If provided, estimates gas for an ERC-20 transfer instead of native.
    """
    try:
        w3 = _get_w3(chain)
        if not Web3.is_address(sender) or not Web3.is_address(recipient):
            return json.dumps({
                "action_type": "gas_estimation",
                "status": "error",
                "error": "Invalid sender or recipient address."
            })
        
        sender_checksum = to_checksum_address(sender)
        recipient_checksum = to_checksum_address(recipient)

        if token_address:
            # Estimate gas for ERC-20 transfer
            if not Web3.is_address(token_address):
                 return json.dumps({
                    "action_type": "gas_estimation",
                    "status": "error",
                    "error": "Invalid token address."
                })
            
            token_checksum = to_checksum_address(token_address)
            token_contract = w3.eth.contract(address=token_checksum, abi=ERC20_ABI)
            
            # Get token decimals to convert amount
            try:
                decimals = token_contract.functions.decimals().call()
            except Exception:
                decimals = 18 # Default if decimals call fails
            
            amount_wei = int(amount * (10 ** decimals))
            
            estimated_gas = token_contract.functions.transfer(recipient_checksum, amount_wei).estimate_gas({
                'from': sender_checksum
            })
        else:
            # Estimate gas for native transfer
            estimated_gas = w3.eth.estimate_gas({
                'from': sender_checksum,
                'to': recipient_checksum,
                'value': w3.to_wei(amount, 'ether')
            })
        
        return json.dumps({
            "action_type": "gas_estimation",
            "status": "success",
            "estimated_gas": estimated_gas,
            "message": f"Estimated gas: {estimated_gas}"
        })
    except Exception as e:
        return json.dumps({
            "action_type": "gas_estimation",
            "status": "error",
            "error": f"Failed to estimate gas: {e}"
        })

# --- NEW FUNCTIONS END ---


tools = [add, sub, mul, web_search, get_balance, get_main_balances, get_wallet_transactions,
         prepare_native_transfer, prepare_token_transfer, prepare_token_approval, check_transaction_status, estimate_gas] # Added new tools

#From Youtube video https://youtu.be/zCwuAlpQKTM    
from langchain.chat_models import init_chat_model

#ChatGoogleGenerativeAI(model="gemini-2.0-flash").bind_tools(tools)
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder

llm = init_chat_model(model="gemini-2.0-flash",  model_provider="google_genai")

prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful blockchain and web search agent. You support transactions and queries on the following EVM chains: Polygon, Ethereum, BSC, Arbitrum, U2U mainnet, U2U testnet, Monad testnet. You can check wallet balances, transaction history, prepare transactions, check status, estimate gas, and search the web. Be friendly and chatty like a human. CRITICAL RESPONSE FORMAT: For ALL responses, return ONLY valid JSON objects. NEVER wrap responses in markdown code blocks (```json). NEVER add explanatory text outside the JSON. For transaction requests, call the appropriate function and return the raw JSON response. For chat responses, return JSON with action_type 'chat' and your message. Example chat response: {{\"action_type\": \"chat\", \"message\": \"Your response here\"}}. If you don't know something, say 'I don't know' or 'I am not sure'. Never reveal that you are an AI or mention your model."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
agent = create_tool_calling_agent(llm, tools=tools, prompt=prompt)

# Custom agent executor to handle transaction responses
class TransactionAgentExecutor(AgentExecutor):
    def invoke(self, inputs, config=None):
        result = super().invoke(inputs, config)
        output = result.get("output", "")
        
        # Normalize the response using our new function
        normalized_response = normalize_agent_response(output)
        
        # If normalization changed the response, return the normalized version
        if normalized_response != output:
            return {"output": json.dumps(normalized_response)}
        
        return result

agent_executor = TransactionAgentExecutor(agent=agent, tools=tools, verbose=True)

# response = agent_executor.invoke({"input": "What balance of 0xB702203B9FD0ee85aeDB9d314C075D480d716635"})
__all__ = ["agent_executor"]
