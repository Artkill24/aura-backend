// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AURANotary {
    struct Report {
        bytes32 sha256Hash;
        string  verdict;
        uint256 score;      // score * 10000 (es. 5160 = 51.60%)
        uint256 timestamp;
        address notarizer;
    }

    mapping(string => Report) private reports;
    mapping(string => bool)   private exists;

    event ReportNotarized(
        string  indexed jobId,
        bytes32         sha256Hash,
        string          verdict,
        uint256         score,
        uint256         timestamp
    );

    function notarize(
        string  calldata jobId,
        bytes32          sha256Hash,
        string  calldata verdict,
        uint256          score
    ) external {
        require(!exists[jobId], "Already notarized");
        reports[jobId] = Report({
            sha256Hash: sha256Hash,
            verdict:    verdict,
            score:      score,
            timestamp:  block.timestamp,
            notarizer:  msg.sender
        });
        exists[jobId] = true;
        emit ReportNotarized(jobId, sha256Hash, verdict, score, block.timestamp);
    }

    function verify(string calldata jobId) external view returns (
        bool   found,
        bytes32 sha256Hash,
        string memory verdict,
        uint256 score,
        uint256 timestamp,
        address notarizer
    ) {
        if (!exists[jobId]) return (false, 0, "", 0, 0, address(0));
        Report memory r = reports[jobId];
        return (true, r.sha256Hash, r.verdict, r.score, r.timestamp, r.notarizer);
    }
}
