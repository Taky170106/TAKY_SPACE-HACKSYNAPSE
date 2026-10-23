// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title SignageRegistry — on-chain authorization root of trust for SignGuard.
/// Only the transport authority can authorize content; anyone can verify.
/// Stores the SHA-256 fingerprint (bytes32) of approved content per content id.
contract SignageRegistry {
    address public authority;                       // only this address may authorize
    mapping(bytes32 => bytes32) private _hash;      // keccak(contentId) => sha256(content)

    event Authorized(bytes32 indexed contentId, bytes32 contentHash, address by);
    event DecisionLogged(string deviceId, string decision, uint256 risk, uint256 ts);

    constructor() {
        authority = msg.sender;                     // deployer = transport authority
    }

    modifier onlyAuthority() {
        require(msg.sender == authority, "SignGuard: not authority");
        _;
    }

    /// Authority records the approved SHA-256 fingerprint for a content id.
    function authorizeContent(bytes32 contentId, bytes32 contentHash) external onlyAuthority {
        _hash[contentId] = contentHash;
        emit Authorized(contentId, contentHash, msg.sender);
    }

    /// Read the authorized fingerprint (0x0 if none).
    function authorizedHash(bytes32 contentId) external view returns (bytes32) {
        return _hash[contentId];
    }

    /// True only if a fingerprint is registered AND matches.
    function verify(bytes32 contentId, bytes32 contentHash) external view returns (bool) {
        bytes32 a = _hash[contentId];
        return a != bytes32(0) && a == contentHash;
    }

    /// Immutable audit event for each decision (render/block/isolate).
    function logDecision(string calldata deviceId, string calldata decision, uint256 risk) external {
        emit DecisionLogged(deviceId, decision, risk, block.timestamp);
    }
}
