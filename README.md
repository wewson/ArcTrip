# ArcTrip ✈️

ArcTrip is a next-generation asset security recovery and automated payment ecosystem that seamlessly integrates blockchain smart contracts (X402 protocol) with intelligent agents (AI Agents). This project aims to explore the practical applications of the "Agentic Web" within the contexts of tourism, micro-payments, and decentralized wallet backup and rescue scenarios.

---

## 🚀 Core Features

* **X402 Protocol Integration**: Leverages the HTTP 402 (Payment Required) status line to enable automated, on-demand micro-payments executed directly by AI Agents.
* **X402Factory & Vault**: On-chain smart contract vaults providing users with a decentralized wallet backup and loss recovery mechanism (`X402-RESCUE`).
* **AI Tour Guide / Assistant**: Built-in intelligent agent services that automatically handle micro-payments on-chain and verify credentials during travel itineraries.
* **Full-Stack Architecture**:
  * `backend/`: Python-based Agent services and API routing (integrated with an SQLite database for local state management).
  * `blockchain/`: Contains Solidity smart contracts, compiled ABIs, and deployment configurations.
  * `frontend/`: Responsive Web frontend user interface.

---

## 🛠️ Project Structure

```text
ARCTRIP/
├── backend/            # Backend Python API and Agent logic
│   ├── app/            # Core application code
│   └── arctrip.db      # Local SQLite database (ignored, untracked)
├── blockchain/         # Smart contracts and Web3 interactions
│   ├── abis/           # Compiled contract ABI files (X402Factory, X402Vault)
│   └── contracts/      # Solidity source code (X402Factory.sol)
├── frontend/           # Frontend UI interface
├── .env                # Environment configuration file (ignored, untracked)
├── requirements.txt    # Python dependency manifest
└── README.md           # Project readme file


## 📦 Quick Start

1.Clone the Repository
1.1git clone [https://github.com/wewson/ArcTrip.git](https://github.com/wewson/ArcTrip.git)
cd ArcTrip
2.Backend Configuration and Execution
2.1 pip install -r requirements.txt
2.2 Configure Environment Variables:
CIRCLE_WALLET_SET_ID=
CIRCLE_AGENT_WALLET_ID=
CIRCLE_API_KEY=TEST_API_KEY:
CIRCLE_ENTITY_SECRET=
CIRCLE_AGENT_ADDRESS=
FACTORY_ADDRESS=
ARC_TESTNET_RPC=https://rpc.testnet.arc.network
DEEPSEEK_API_KEY=sk-
USDC_CONTRACT_ADDRESS=0x3600000000000000000000000000000000000000
CHAIN_ID=5042002
2.3
Start the Backend Service:
uvicorn app.main:app --reload  

3.Contracts
The contract source files and corresponding ABIs are located under the blockchain/ directory.
X402Factory.sol：Used to dynamically deploy and manage user-specific X402Vault security rescue vaults.
## 🛠️ Tech Stack
Backend: Python, Pydantic, Web3.py

Smart Contracts: Solidity, EVM Compatible

Database: SQLite

Protocol Standard: HTTP 402 / ARC x402 Micropayments

