import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

import '@rainbow-me/rainbowkit/styles.css'
import { RainbowKitProvider, darkTheme, connectorsForWallets } from '@rainbow-me/rainbowkit'
import { metaMaskWallet, okxWallet, rabbyWallet, injectedWallet } from '@rainbow-me/rainbowkit/wallets'
import { createConfig, WagmiProvider } from 'wagmi'
import { http } from 'viem'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const arcTestnet = {
  id: 5042002,
  name: 'Arc Testnet',
  nativeCurrency: {
    decimals: 6,
    name: 'USDC',
    symbol: 'USDC',
  },
  rpcUrls: {
    default: { http: ['https://rpc.testnet.arc.network'] },
    public: { http: ['https://rpc.testnet.arc.network'] },
  },
  blockExplorers: {
    default: { name: 'ArcScan', url: 'https://rpc.testnet.arc.network' },
  },
}

const connectors = connectorsForWallets(
  [
    {
      groupName: 'Wallets',
      wallets: [metaMaskWallet, okxWallet, rabbyWallet, injectedWallet],
    },
  ],
  {
    appName: 'ArcTrip X402 Core',
    projectId: 'a2a97a7ae4b8bf71c45f2721fe6c441c', 
  }
)

const config = createConfig({
  connectors,
  chains: [arcTestnet],
  transports: {
    [arcTestnet.id]: http('https://rpc.testnet.arc.network'),
  },
  ssr: false,
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false, 
      refetchOnWindowFocus: false, 
    },
  },
})

const currentLocale = localStorage.getItem('app_locale') === 'zh' ? 'zh-CN' : 'en-US';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider theme={darkTheme()} locale={currentLocale}>
          <App />
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  </React.StrictMode>,
)