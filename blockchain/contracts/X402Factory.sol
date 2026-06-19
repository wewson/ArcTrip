// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

abstract contract ReentrancyGuard {
    uint256 private constant NOT_ENTERED = 1;
    uint256 private constant ENTERED = 2;
    uint256 private _status;

    constructor() { _status = NOT_ENTERED; }

    modifier nonReentrant() {
        require(_status != ENTERED, "ReentrancyGuard: reentrant call");
        _status = ENTERED;
        _;
        _status = NOT_ENTERED;
    }
}

library SafeERC20 {
    function safeTransfer(address token, address to, uint256 value) internal {
        (bool success, bytes memory data) = token.call(abi.encodeWithSignature("transfer(address,uint256)", to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), "SafeERC20: transfer failed");
    }

    function safeTransferFrom(address token, address from, address to, uint256 value) internal {
        (bool success, bytes memory data) = token.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", from, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), "SafeERC20: transferFrom failed");
    }
}

contract X402Vault is ReentrancyGuard {
    using SafeERC20 for address;

    address public immutable factory;
    address public immutable primaryWallet;
    address public immutable backupWallet; 
    address public immutable agentOwner;
    address public immutable usdcToken;
    uint256 public immutable createdAt;
    uint256 public immutable lockDuration;
    bool public isClosed;

    event UserWithdrawn(address indexed user, uint256 amount);
    event EmergencyExtracted(address indexed target, uint256 amount);

    modifier onlyAgent() {
        require(msg.sender == agentOwner, "X402: Only Agent can rescue asset");
        _;
    }

    constructor(address _primaryWallet, address _backupWallet, address _agent, address _usdc, uint256 _lockDuration) {
        factory = msg.sender;
        primaryWallet = _primaryWallet;
        backupWallet = _backupWallet == address(0) ? _primaryWallet : _backupWallet;
        agentOwner = _agent;
        usdcToken = _usdc;
        createdAt = block.timestamp;
        lockDuration = _lockDuration;
    }

    function emergencyExtract() external onlyAgent nonReentrant {
        require(!isClosed, "X402: Vault already closed");
        require(block.timestamp <= createdAt + lockDuration, "X402: Protection period expired");
        uint256 totalBalance = IERC20(usdcToken).balanceOf(address(this));
        require(totalBalance > 0, "X402: Vault is empty");
        
        isClosed = true;
        usdcToken.safeTransfer(backupWallet, totalBalance);
        emit EmergencyExtracted(backupWallet, totalBalance);
    }

    function withdrawSuccess() external nonReentrant {
        require(msg.sender == primaryWallet, "X402: Only primary wallet can withdraw");
        require(!isClosed, "X402: Vault already closed");
        require(block.timestamp > createdAt + lockDuration, "X402: Asset is still locked under protection");
        uint256 totalBalance = IERC20(usdcToken).balanceOf(address(this));
        require(totalBalance > 0, "X402: Vault is empty");

        isClosed = true;
        usdcToken.safeTransfer(primaryWallet, totalBalance);
        emit UserWithdrawn(primaryWallet, totalBalance);
    }
}

contract X402Factory is ReentrancyGuard {
    using SafeERC20 for address;

    struct OrderInfo { address vault; bool activated; bytes32 subRoom; }

    mapping(bytes32 => OrderInfo) public orders;
    address public agentOwner; 
    address public usdcToken;
    uint256 public accumulatedFees; 

    event VaultCreated(bytes32 indexed orderHash, address vaultAddress, address indexed user);
    event X402ProtocolActivated(bytes32 indexed orderHash, bytes32 subRoomId, uint256 settlementFee);

    constructor(address _agent, address _usdc) {
        agentOwner = _agent;
        usdcToken = _usdc;
    }

    function createPersonalVault(bytes32 _orderHash, bytes32 _subRoomId, address _backupWallet, uint256 _premium, uint256 _deposit, uint256 _lockDuration) external nonReentrant returns (address) {
        require(orders[_orderHash].vault == address(0), "X402: Order hash already deployed");
        require(_deposit > 0 && _premium > 0, "X402: Invalid amounts");   
        require(_subRoomId != bytes32(0), "X402: Invalid X402 Sub-Room ID"); 

        X402Vault newVault = new X402Vault(msg.sender, _backupWallet, agentOwner, usdcToken, _lockDuration);
        address vaultAddr = address(newVault);

        orders[_orderHash] = OrderInfo(vaultAddr, true, _subRoomId);
        accumulatedFees += _premium; 

        uint256 before = IERC20(usdcToken).balanceOf(address(this));
        usdcToken.safeTransferFrom(msg.sender, address(this), _premium);
        require(IERC20(usdcToken).balanceOf(address(this)) - before == _premium, "X402: Fee-on-transfer not supported");

        usdcToken.safeTransferFrom(msg.sender, vaultAddr, _deposit);

        emit X402ProtocolActivated(_orderHash, _subRoomId, _premium);
        emit VaultCreated(_orderHash, vaultAddr, msg.sender);
        return vaultAddr;
    }

    function withdrawPlatformFees(address to) external onlyAgent nonReentrant {
        uint256 fees = accumulatedFees;
        require(fees > 0, "X402: No fees to withdraw");
        accumulatedFees = 0; 
        usdcToken.safeTransfer(to, fees);
    }
    
    modifier onlyAgent() { require(msg.sender == agentOwner, "X402: Only agent owner"); _; }
}