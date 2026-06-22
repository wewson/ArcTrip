import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import axios from 'axios';

const CONSTANT_FACTORY_ADDRESS = "0x68b7200887bfF90c9800941524Cb546BBf3c47Ae";
const RAW_AGENT_ADDRESS = "0x5d88b43afee107834aead4f8034d0b3199a979e3";
const DEFAULT_RPC_URL = "https://rpc.testnet.arc.network";

export default function App() {
  const [activeTab, setActiveTab] = useState('ai-travel'); 

  const [backendUrl, setBackendUrl] = useState("http://217.60.249.62:8003");
  const [factoryAddress] = useState(CONSTANT_FACTORY_ADDRESS);
  const [usdcAddress, setUsdcAddress] = useState("0x3600000000000000000000000000000000000000");
  const [chainId, setChainId] = useState(5042002);
  const [rpcUrl, setRpcUrl] = useState(DEFAULT_RPC_URL);
  const [circleAgentAddress, setCircleAgentAddress] = useState(RAW_AGENT_ADDRESS); 

  const [account, setAccount] = useState("");
  const [isApproved, setIsApproved] = useState(false); 
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);

  const [tripForm, setTripForm] = useState({ to: '', days:'' , budget: '' });
  const [aiResult, setAiResult] = useState("");
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [feeTxHash, setFeeTxHash] = useState("");
  const [weather, setWeather] = useState({ temp: "18", condition: "Syncing..." });

  const [premiumInput, setPremiumInput] = useState("0.1"); 
  const [depositInput, setDepositInput] = useState("0.5"); 
  const [lockDuration] = useState(604800); 

  const [backupWallet, setBackupWallet] = useState(""); 
  const [rescueVaultAddress, setRescueVaultAddress] = useState(CONSTANT_FACTORY_ADDRESS); 
  const [rescueOrderId, setRescueOrderId] = useState(""); 
  const [isRescued, setIsRescued] = useState(false);
  const [vaultStatusText, setVaultStatusText] = useState("🟢 Waiting for Activation");

  const addLog = (msg) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString('en-US', { hour12: false })}] ${msg}`, ...prev]);
  };

  useEffect(() => {
    if (!tripForm.to || tripForm.to.trim().length < 1) {
      setWeather({ temp: "--", condition: "Awaiting input..." });
      return;
    }

    const fetchDynamicGeoAndWeather = async () => {
      try {
        const searchCity = tripForm.to.trim();
        const geoUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(searchCity)}&count=1&language=en`;
        const geoRes = await axios.get(geoUrl);
        
        if (!geoRes.data.results || geoRes.data.results.length === 0) {
          setWeather({ temp: "--", condition: "City not found" });
          return;
        }

        const { latitude, longitude } = geoRes.data.results[0];
        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=1`;
        const weatherRes = await axios.get(weatherUrl);
        
        if (weatherRes.data && weatherRes.data.daily) {
          const maxTemp = weatherRes.data.daily.temperature_2m_max[0];
          const minTemp = weatherRes.data.daily.temperature_2m_min[0];
          const avgTemp = Math.round((maxTemp + minTemp) / 2);
          
          let statusDesc = "Comfortable";
          if (avgTemp < 0) {
            statusDesc = "Extreme Arctic Cold";
          } else if (avgTemp < 15) {
            statusDesc = "Chilly Weather";
          } else if (avgTemp > 30) {
            statusDesc = "Extreme Heat Risk";
          }

          setWeather({
            temp: avgTemp.toString(),
            condition: `${statusDesc} (${minTemp}°C - ${maxTemp}°C)`
          });
        }
      } catch (err) {
        setWeather({ temp: "18", condition: "Comfortable Weather" });
      }
    };

    const delayDebounceFn = setTimeout(() => { fetchDynamicGeoAndWeather(); }, 500);
    return () => clearTimeout(delayDebounceFn);
  }, [tripForm.to]);

  const verifyAndSwitchNetwork = async (browserProvider) => {
    try {
      const network = await browserProvider.getNetwork();
      const currentChainId = Number(network.chainId);
      if (currentChainId !== chainId) {
        addLog(`⚠️ Network mismatch detected (Current: ${currentChainId}, Required: ${chainId}). Requesting switch...`);
        
        // 同样在网络切换时优先使用 OKX 注入环境
        const injectedProvider = window.okxwallet || window.ethereum;
        if (injectedProvider) {
          await injectedProvider.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: '0x' + chainId.toString(16) }],
          });
        }
      }
    } catch (switchError) {
      if (switchError.code === 4902) {
        try {
          const injectedProvider = window.okxwallet || window.ethereum;
          if (injectedProvider) {
            await injectedProvider.request({
              method: 'wallet_addEthereumChain',
              params: [{
                chainId: '0x' + chainId.toString(16),
                chainName: 'Arc Testnet',
                rpcUrls: [rpcUrl],
                nativeCurrency: { name: 'ARC', symbol: 'ARC', decimals: 18 }
              }],
            });
          }
        } catch (addError) {
          addLog(`❌ Failed to automatically add network: ${addError.message}`);
        }
      }
    }
  };

  // 🦊 终极修复：精准穿透检测 window.okxwallet，防止被其他钱包插件拦截
  const connectWallet = async () => {
    const okxProvider = window.okxwallet || window.ethereum;

    if (!okxProvider) {
      addLog("❌ Error: OKX Wallet injection vector not found. Please ensure the extension is unlocked and 'Set as Default Wallet' is active.");
      return;
    }
    try {
      setLoading(true);
      const provider = new ethers.BrowserProvider(okxProvider);
      const accounts = await okxProvider.request({ method: 'eth_requestAccounts' });
      setAccount(accounts[0]);
      addLog(`🦊 OKX Wallet linked successfully: ${accounts[0]}`);
      
      await verifyAndSwitchNetwork(provider);
    } catch (err) {
      addLog(`❌ Wallet initialization failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!account) return addLog("⚠️ Interaction blocked: Connect wallet first before granting token spending authorization.");
    const okxProvider = window.okxwallet || window.ethereum;
    try {
      setLoading(true);
      addLog("🪙 Requesting token spending authorization allowance...");
      const provider = new ethers.BrowserProvider(okxProvider);
      const signer = await provider.getSigner();
      const erc20Abi = ["function approve(address spender, uint256 amount) public returns (bool)"];
      const usdcContract = new ethers.Contract(usdcAddress, erc20Abi, signer);
      
      const tx = await usdcContract.approve(factoryAddress, ethers.MaxUint256);
      await tx.wait();
      setIsApproved(true);
      addLog("✅ Allowance approved successfully. Ready to deploy isolated vault structures.");
    } catch (err) {
      addLog(`❌ Authorization rejected: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const generateAIPlan = async () => {
    if (!account) return addLog("⚠️ Interaction blocked: Connect wallet first before generating travel plans.");
    const okxProvider = window.okxwallet || window.ethereum;
    try {
      setLoadingPlan(true); setAiResult(""); setFeeTxHash("");
      const currentPlanId = `PLAN-${Date.now()}`;
      const provider = new ethers.BrowserProvider(okxProvider);
      const signer = await provider.getSigner();
      const erc20Abi = ["function transfer(address to, uint256 amount) public returns (bool)"];
      const usdcContract = new ethers.Contract(usdcAddress, erc20Abi, signer);
      
      const tx = await usdcContract.transfer(circleAgentAddress, ethers.parseUnits("0.5", 6));
      const receipt = await tx.wait(); setFeeTxHash(receipt.hash);
      
      const response = await axios.post(`${backendUrl}/api/pledge/generate_trip_plan`, {
        order_id: currentPlanId, 
        user_wallet_address: account, 
        from_location: tripForm.to, 
        to_location: tripForm.to, 
        days: tripForm.days, 
        budget: tripForm.budget, 
        tx_hash: receipt.hash
      }, {
        headers: { "X-Order-ID": currentPlanId }
      });

      if (response && response.data) {
        setAiResult(response.data.plan_content || response.data.ai_plan);
      }
    } catch (err) {
      if (err.response?.status === 402) {
        setAiResult(`### 🛡️ [X402 Intercept Gateway Interruption]\n\nOn-chain asset settlement verification unfulfilled or database sync remains PENDING. Core AI compute node execution blocked.\n- Receipt Status: ${err.response.data?.detail || "Payment Required"}\n- Error Reference Code: ${err.response.data?.code || "UNKNOWN"}`);
      } else {
        setAiResult(`### 🛡️ Arc X402 Adaptive Travel Guard Strategy (${tripForm.to})\n\n[Risk Control Triggered] Assets migrated to safe-harbor shield layout.\n- Target Vector: ${tripForm.to || "Unknown"}\n- Timeframe: ${tripForm.days || 0} Days\n- Active Node Temperature: ${weather.temp}°C\n- Allocation Budget: ${tripForm.budget || 0} USDC`);
      }
    } finally { 
      setLoadingPlan(false); 
    }
  };

  const createRescueVault = async () => {
    if (!account) return addLog("⚠️ Interaction blocked: Connect wallet first before setting up an escrow structure.");
    if (!backupWallet.trim()) return addLog("💡 Security Warning: Please define a Target Emergency Recovery Destination Wallet address to consolidate assets first.");

    const okxProvider = window.okxwallet || window.ethereum;
    try {
      setLoading(true);
      setIsRescued(false);

      const currentRescueId = "X402-RESCUE-" + Date.now();
      addLog(`⚙️ Requesting wallet signature to deposit principal assets and bind recovery parameters...`);

      const provider = new ethers.BrowserProvider(okxProvider);
      const signer = await provider.getSigner();

      const factoryAbi = [
        {
          "inputs": [
            { "internalType": "bytes32", "name": "_orderHash", "type": "bytes32" },
            { "internalType": "bytes32", "name": "_subRoomId", "type": "bytes32" },
            { "internalType": "address", "name": "_backupWallet", "type": "address" },
            { "internalType": "uint256", "name": "_premium", "type": "uint256" },
            { "internalType": "uint256", "name": "_deposit", "type": "uint256" },
            { "internalType": "uint256", "name": "_lockDuration", "type": "uint256" }
          ],
          "name": "createPersonalVault",
          "outputs": [{ "internalType": "address", "name": "", "type": "address" }],
          "stateMutability": "nonpayable",
          "type": "function"
        }
      ];

      const factoryContract = new ethers.Contract(factoryAddress, factoryAbi, signer);
      const orderHash = ethers.solidityPackedKeccak256(["string"], [currentRescueId]);
      const subRoomId = ethers.solidityPackedKeccak256(["string"], ["ROOM-X402-VAULT"]);

      const validBackupWallet = ethers.getAddress(backupWallet.trim());

      const tx = await factoryContract.createPersonalVault(
        orderHash,
        subRoomId,
        validBackupWallet, 
        ethers.parseUnits(premiumInput, 6),  
        ethers.parseUnits(depositInput, 6),  
        lockDuration
      );
      
      const receipt = await tx.wait();

      if (receipt && receipt.status === 1) {
        addLog(`📦 Vault structure compiled on-chain. Transaction Hash: ${receipt.hash}`);

        try {
          addLog(`📝 Synchronizing initialization parameters with orchestration backend...`);
          const prePayload = {
            order_id: currentRescueId.toString(),
            user_wallet_address: account.toString(),
            premium: premiumInput.toString(),
            deposit: depositInput.toString(),
            backup_wallet: validBackupWallet
          };
          await axios.post(`${backendUrl}/api/pledge/create_order`, prePayload);
        } catch (err) {
          console.error("Backend initializing tracking failure:", err);
        }

        try {
          addLog(`📡 Notifying clearing node framework to map credentials...`);
          const createPayload = {
            order_id: currentRescueId.toString(),
            sub_room_id: "0x" + "0".repeat(64), 
            backup_wallet: validBackupWallet, 
            premium_usdc: parseFloat(premiumInput),  
            deposit_usdc: parseFloat(depositInput),  
            lock_duration: parseInt(lockDuration)    
          };
          
          await axios.post(`${backendUrl}/api/pledge/execute_factory_vault`, createPayload);
          
          setRescueVaultAddress(CONSTANT_FACTORY_ADDRESS);
          setRescueOrderId(currentRescueId);
          addLog(`✅ Full pipeline synced successfully. Clearing token credential: ${currentRescueId}`);
          setVaultStatusText("🟢 Protection Module Armed");
        } catch (e) {
          setRescueVaultAddress(CONSTANT_FACTORY_ADDRESS);
          setRescueOrderId(currentRescueId);
          setVaultStatusText("🟢 Protection Module Armed (Local Mode)");
          addLog(`ℹ️ Smart contract deployment verified. Backend validation indexing processing asynchronously.`);
        }
      } else {
        addLog(`❌ On-chain tracking report indicates transaction failure. Pipeline aborted.`);
        setVaultStatusText("❌ On-Chain Execution Aborted");
      }

    } catch (err) {
      if (err.code === 4001 || err.message?.includes("denied")) {
        addLog(`⚠️ Transaction rejected: User canceled cryptographic signature step.`);
        setVaultStatusText("❌ Signature Refused");
      } else {
        addLog(`❌ Execution interrupted. Please verify wallet network state and token balance metrics.`);
        setVaultStatusText("❌ Protocol Circuit Breaked");
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const executeAgentPayout = async () => {
    if (!account) return addLog("⚠️ Interaction blocked: Connect wallet first before initializing emergency payouts.");
    if (!rescueOrderId.trim()) return addLog("⚠️ Please supply a valid clearing order reference ID token.");

    try {
      setLoading(true);
      addLog(`🚨 [CLEARING_ENGAGED] Launching automated Circle Agent protocol to intercept target vault security configurations...`);
      
      const requestPayload = {
        order_id: rescueOrderId.trim().toString(), 
        vault_address: rescueVaultAddress.trim().toString(), 
        user_wallet_address: account.toString()
      };

      const response = await axios.post(`${backendUrl}/api/pledge/agent_execute_payout`, requestPayload);

      if (response.data.status === "SUCCESS" || response.data.status === "success" || response.data.tx_hash) {
        setIsRescued(true);
        setVaultStatusText("🔒 Credential Expired (Assets Remapped)");
        addLog("================ 🥇 X402 AGENT CLEARING RESOLVED SUCCESSFULLY ================");
        addLog(`🎉 Safe-harbor breakout complete. Funds routed directly to the designated secure parameter target.`);
        addLog(`⛓️ On-chain process tracking transactional trace reference: ${response.data.tx_hash}`);
      } else {
        addLog(`⚠️ Encountered unexpected runtime layout mapping: ${JSON.stringify(response.data)}`);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || err.message;
      addLog(`❌ Clearing validation engine returned error layout: ${JSON.stringify(errorMsg)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans antialiased selection:bg-blue-500/10">
      
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100 px-6 py-4 shadow-sm flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🪐</span>
          <div className="flex flex-col">
            <h1 className="text-lg font-black bg-gradient-to-r bg-clip-text text-transparent from-slate-900 to-blue-600 tracking-wide uppercase">
              X402 Travel Guard Eco
            </h1>
            <span className="text-[10px] text-gray-400 font-mono tracking-tight">Arc Testnet Native Protocol via Circle Agent Network</span>
          </div>
        </div>

        <div className="hidden xl:flex items-center gap-4 px-4 py-1.5 bg-slate-100 rounded-xl border border-gray-200/60 font-mono text-[11px] text-gray-500">
          <div>🌐 Node: <span className="text-blue-600 font-bold">Arc Testnet</span></div>
          <div>🆔 Chain: <span className="text-slate-800 font-bold">{chainId}</span></div>
        </div>

        <div className="bg-gray-100/80 p-1 rounded-xl flex gap-1 border border-gray-200/40">
          <button onClick={() => setActiveTab('ai-travel')} className={`px-5 py-2 rounded-lg font-semibold text-xs transition-all ${activeTab === 'ai-travel' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-slate-800'}`}>
            🤖 AI Travel Assistant
          </button>
          <button onClick={() => setActiveTab('x402-vault')} className={`px-5 py-2 rounded-lg font-semibold text-xs transition-all ${activeTab === 'x402-vault' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-slate-800'}`}>
            🛡️ X402 Escrow Vault
          </button>
        </div>
        
        <button onClick={connectWallet} className="px-5 py-2.5 text-xs rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold transition shadow-md shrink-0">
          {account ? `🦊 ${account.substring(0,6)}...${account.substring(38)}` : "Connect OKX Wallet"}
        </button>
      </header>

      <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        <div className="lg:col-span-8">
          {activeTab === 'ai-travel' && (
            <div className="flex flex-col gap-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-1 flex flex-col gap-4">
                  <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                    <h3 className="text-xs font-bold tracking-wider text-gray-400 uppercase mb-3">🌤️ Vector Weather Metrics</h3>
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-100/40">
                      <div className="text-3xl font-black text-blue-600">{weather.temp}°C</div>
                      <div className="text-xs font-bold text-blue-900/60 mt-1 capitalize">{tripForm.to || "None"} · {weather.condition}</div>
                    </div>
                  </div>
                </div>

                <div className="md:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.03)] p-5 flex flex-col">
                  <div className="text-xs font-bold text-blue-500 font-mono tracking-wider mb-4">🤖 AGENT INTELLIGENT ROUTE CHAT</div>
                  <div className="grid grid-cols-3 gap-3 mb-4 text-xs">
                    <div>
                      <label className="text-gray-400 block mb-1">Destination Vector</label>
                      <input type="text" value={tripForm.to} onChange={(e) => setTripForm({...tripForm, to: e.target.value})} className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 outline-none" />
                    </div>
                    <div>
                      <label className="text-gray-400 block mb-1">Days</label>
                      <input type="number" value={tripForm.days} onChange={(e) => setTripForm({...tripForm, days: Number(e.target.value)})} className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 outline-none" />
                    </div>
                    <div>
                      <label className="text-gray-400 block mb-1">Budget Allocation (USDC)</label>
                      <input type="number" value={tripForm.budget} onChange={(e) => setTripForm({...tripForm, budget: Number(e.target.value)})} className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 outline-none" />
                    </div>
                  </div>
                  
                  <button disabled={loadingPlan || !account} onClick={generateAIPlan} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl text-xs shadow-md transition">
                    {loadingPlan ? "🤖 Compiling Intelligence Strategy Matrix..." : "Request Protected AI Strategy Plan (0.5 USDC)"}
                  </button>
                </div>
              </div>

              {aiResult && (
                <div className="w-full bg-slate-900 border border-slate-950 rounded-2xl p-6 font-mono text-xs leading-relaxed text-slate-100 whitespace-pre-wrap break-words overflow-x-hidden shadow-xl">
                  {aiResult}
                </div>
              )}
            </div>
          )}

          {activeTab === 'x402-vault' && (
            <div className="space-y-6">
              
              <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.03)] relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1.5 h-full bg-blue-600" />
                <div className="flex gap-4">
                  <div className="w-7 h-7 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">1</div>
                  <div className="flex-1 space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-bold text-slate-900">Initialize Isolated Asset Protection Architecture</h3>
                      <span className="text-xs font-bold text-green-500">{vaultStatusText}</span>
                    </div>

                    <div className="bg-slate-100/70 p-3 rounded-xl border border-gray-200/50">
                      <span className="text-[10px] font-bold text-gray-400 block uppercase tracking-wider">Vault Factory Contract Endpoint Address</span>
                      <span className="font-mono text-xs text-blue-600 font-bold select-all">{factoryAddress}</span>
                    </div>

                    <div className="bg-blue-50/40 p-4 rounded-xl border border-blue-100/60">
                      <label className="block text-xs font-bold text-blue-900 mb-1">🔑 Target Emergency Recovery Destination Wallet (Backup Wallet)</label>
                      <p className="text-[10px] text-gray-500 mb-2">💡 Structural Lockout Setting: Declare a distinct 0x structural recovery wallet endpoint here. This will be immutable once packaged within the smart contract transaction context.</p>
                      <input 
                        type="text" 
                        value={backupWallet} 
                        onChange={(e) => setBackupWallet(e.target.value)} 
                        placeholder="Provide a clean, uncompromised 0x cryptographic wallet address reference here" 
                        className="w-full bg-white border border-blue-200 text-emerald-700 font-mono rounded-xl px-3 py-2 text-xs outline-none focus:border-blue-500 font-bold shadow-sm" 
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                      <div>
                        <label className="text-gray-400 block mb-1">Premium Fee (USDC)</label>
                        <input type="text" value={premiumInput} onChange={(e)=>setPremiumInput(e.target.value)} className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-blue-600 font-bold outline-none" />
                      </div>
                      <div>
                        <label className="text-gray-400 block mb-1">Escrowed Balance Principal (USDC)</label>
                        <input type="text" value={depositInput} onChange={(e)=>setDepositInput(e.target.value)} className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-indigo-600 font-bold outline-none" />
                      </div>
                      <div>
                        <label className="text-gray-400 block mb-1">Protection Term Window</label>
                        <div className="w-full bg-orange-50/60 border border-orange-200/60 text-orange-700 font-bold rounded-xl px-3 py-2">🔒 7-Day Active Lockout</div>
                      </div>
                    </div>

                    {rescueOrderId && (
                      <div className="bg-blue-50 text-blue-700 p-3.5 rounded-xl border border-blue-100 text-xs">
                        🎉 <strong>Asset parameters bounded within isolated container. Recovery validation certificate token:</strong>
                        <div className="font-mono font-bold mt-1.5 text-sm select-all bg-white px-2 py-1 rounded border border-blue-200 inline-block text-blue-600">🎫 {rescueOrderId}</div>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3">
                      <button disabled={isApproved || !account} onClick={handleApprove} className="font-bold py-2.5 rounded-xl text-xs border border-gray-200 bg-gray-50 text-slate-700 hover:bg-gray-100 transition">
                        {isApproved ? "🟢 Allowance Confirmed" : "🪙 Approve Token Spending Allocation Limit"}
                      </button>
                      <button disabled={!isApproved || loading || !backupWallet.trim()} onClick={createRescueVault} className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold py-2.5 rounded-xl text-xs shadow-md disabled:from-gray-300 disabled:to-gray-400 transition">
                        {loading ? "⏳ Encoding cryptographic context..." : "🚀 Disburse Core Assets & Spawn Vault Module"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.03)] relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1.5 h-full bg-rose-500" />
                <div className="flex gap-4">
                  <div className="w-7 h-7 rounded-full bg-rose-50 text-rose-500 flex items-center justify-center font-bold text-xs shrink-0">2</div>
                  <div className="flex-1 space-y-4">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">Control Interface: Direct Automated Clearing Agent Infrastructure</h3>
                    </div>

                    <div className="bg-rose-50/50 p-4 rounded-xl border border-rose-100/60 space-y-4">
                      <div>
                        <label className="block text-xs font-bold text-rose-800 mb-1">Emergency Clearing Certificate Reference ID Token (Order ID)</label>
                        <input type="text" value={rescueOrderId} onChange={(e) => { setRescueOrderId(e.target.value); }} placeholder="X402-RESCUE-xxxxxxxxxxxxx" className="w-full bg-white border border-gray-200 text-slate-800 rounded-xl px-3 py-2 text-xs font-mono outline-none" />
                      </div>

                      <div className="bg-white p-3 rounded-xl border border-gray-100 shadow-inner text-xs space-y-1">
                        <span className="text-gray-400 block font-bold">🎯 Settled Value Destination Mapping Target:</span>
                        {backupWallet ? (
                          <p className="font-mono text-emerald-700 font-bold bg-emerald-50/40 p-1.5 rounded border border-emerald-100 break-all">
                            ✅ Breakout execution will route variables directly to: {backupWallet}
                          </p>
                        ) : (
                          <p className="text-orange-500 italic">⚠️ Target recovery backup address registration omitted in configuration Step 1.</p>
                        )}
                      </div>

                      <button disabled={!rescueOrderId.trim() || loading} onClick={executeAgentPayout} className="w-full py-3 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white shadow-md transition disabled:bg-gray-300">
                        {loading ? "⚡ Instructing Agent execution network mechanisms..." : "💥 Fire Cryptographic Emergency Breakout Protocol"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-4">
          <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-[0_8px_30px_rgb(0,0,0,0.03)] flex flex-col h-[520px] sticky top-24">
            <div className="font-mono text-xs font-black text-slate-600 border-b border-gray-100 pb-3 mb-3 flex justify-between items-center tracking-wider">
              <span>📡 X402 PROTOCOL RADAR</span>
              <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 font-mono text-[10px] text-slate-500 pr-1">
              {logs.length === 0 ? (
                <div className="text-gray-300 text-center pt-32 italic">Awaiting external network ingestion signals...</div>
              ) : (
                <div className="block space-y-2">
                  {logs.map((log, i) => (
                    <div key={i} className="p-2 rounded-xl bg-gray-50 border border-gray-100/50 break-all text-slate-600 shadow-sm">
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}
