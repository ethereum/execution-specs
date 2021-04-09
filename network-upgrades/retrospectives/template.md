# Ethereum network upgrade retrospective report template

## Simple Summary

Recommendation for creating Ethereum network upgrade analysis report a.k.a. upgrade postmortem report.

## Motivation

The purpose of this document is to create a template to standardize the network upgrade retrospective report. This has several advantages:
* the reports will describe the chain of events that occurred during the network upgrade process, 
* it will help understand what combination of events created the scenario (successful or not), and 
* how we can make it better for the future.

This template aims to provide a template for retrospective report after every upgrade that will help shape the future coordination and prepare the community for potential process improvements and recommend a repository to save them for future references.

## Specification

```
# Upgrade summary 
(Write a summary of the upgrade including)

* Date and time (in UTC) 
* Block Number (Mainnet) 
* Synced node (%)
* Winner miner 
* Block Reward
* Uncles Reward 
* Difficulty
* Block number (Ropsten)
* Any other details

# EIPs Included 
(EIPs which are included and what are the proposed improvements? List new features added to the blockchain and advantages.)

* EIP-1
* EIP-2
* EIP-3
* Meta EIP# (Used till Muir Glacier upgrade)

# EIP selection process
(EIP for upgrade selection process eg. Schedule based, EIP Centric etc.)

* CFI selection highlights
* Describe the proposal selection process (if other than present [Ethereum Network Upgrade Process](https://medium.com/ethereum-cat-herders/shedding-light-on-the-ethereum-network-upgrade-process-4c6186ed442c))

# Timeline - Backlog check
(List sequence of events with date)

* Discovery of problem 
* Validation of problem
* Discussion & decision making 
* Implementation

# Best Practices
(List of best practices to be followed in the future.)

# Process Evaluation
(Review the timeline and meeting notes to find out if there was any unplanned EIP added at the last minute that could have been planned, or at least moved to the next upgrade?)

# Suggested Corrective Action
(How can we optimize the decision-making process?)

* List of problems and possible suggestions.
```

## Rationale
The aim is to collect relevant information to support the need, process, and deployment of the next network upgrade. While this information is available in some of the Ethereum All Core Devs meetings, it is highly recommended to capture in an upgrade retrospective report. 

## Test Cases
Not applicable. This is for documentation purposes only.

## Implementation
Muir Glacier postmortem upgrade. 

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
