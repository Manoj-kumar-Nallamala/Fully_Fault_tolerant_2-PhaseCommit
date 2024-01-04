#Fault-Tolerant 2-Phase Distributed Commit Protocol Implementation
#System Architecture
This project implements a fault-tolerant 2-phase distributed commit (2PC) protocol. It involves a Transaction Coordinator (TC) and multiple participant nodes. The system is designed to handle node crashes and recover appropriately, ensuring transaction integrity.

Components
Transaction Coordinator (TC): The central control unit that initiates transactions, sends prepare and commit messages to participant nodes, and handles transaction recovery in case of failures.

Participant Nodes: These nodes participate in the transactions. They vote on the transaction outcome (commit or abort) and communicate their decisions to the TC.

Setup Instructions
To run this project, ensure you have Python installed on your system. Each node (including the TC) is represented by a separate Python script. Here's how to set them up:

Clone the project repository to your local machine.
Navigate to the project directory.
There are three main scripts: node1.py (TC), node2.py, and node3.py (participant nodes).
Running the Project
Transaction Coordinator
Open a terminal and run:
python node1.py
Participant Nodes
Open separate terminals for each participant node and run:
For Node 2:
python node2.py
For Node 3:
python node3.py

Testing Scenarios
The project is designed to handle various failure scenarios to test the robustness of the 2PC protocol. Here are instructions for testing each part:

Part 1: TC Fails Before Sending "Prepare"
Objective: To simulate the scenario where the TC fails before sending the "prepare" message.
How to Test:
Run the TC and initiate a transaction.
Choose to simulate a failure before the "prepare" message is sent.
Observe the behavior of participant nodes (they should timeout and abort).
Restart the TC and check the recovery and final state of the transaction.


Part 2: Node Does Not Respond "Yes"
Objective: To test the situation where a participant node does not respond with "yes".
How to Test:
Run the TC and participant nodes.
Initiate a transaction and, when prompted on a participant node, choose not to commit (respond with "no").
Observe the TC aborting the transaction.


Part 3: TC Handles Incomplete Commit
Objective:
This part tests the TC's ability to recover from a scenario where it fails after sending a "commit" message to some but not all participant nodes. This is achieved by simulating the TC's failure during the commit phase.

How to Test:

Initiate a Transaction:

Run the TC and participant nodes.
Initiate a transaction and have all nodes agree to commit.
Simulate TC Failure:

In the send_commit_messages function of the TC, uncomment the sleep timer lines.
Run the transaction process. The TC will send a commit message to at least one node and then pause (simulating a crash).
Stop the TC during this sleep period.

Restart TC and Observe Recovery:

Restart the TC.
The TC should automatically detect the incomplete transaction from the transaction file.
It will attempt to send the commit message to the remaining nodes that are still in the 'pending' state.
Verify Final State:

Examine the transaction file and participant node logs to confirm that the commit process has been successfully completed for all nodes.
Notes:

This test demonstrates the TC's resilience and its ability to ensure the completion of a distributed transaction in cases where it experiences a partial failure during the commit phase.
It's important to ensure consistency in the transaction ID and to verify the integrity of the transaction file after the TC restarts.
The recovery mechanism is key to maintaining the integrity and consistency of the distributed commit process in a fault-tolerant system.


Part 4: Node Recovery After Failing Post-'Yes' Confirmation

Objective:
This part aims to test and ensure the proper recovery of a participant node if it fails after sending a 'yes' vote to the Transaction Coordinator (TC), but before the actual commit takes place. The focus is on the node's ability to inquire about the transaction status from the TC upon recovery.

How to Test:

Prepare the Environment:

Run the TC and participant nodes.
Ensure that the TC is initially in its normal operation mode.
Initiate and Interrupt a Transaction:

Initiate a transaction.
Have one of the participant nodes (either Node 2 or Node 3) respond with 'yes' to the prepare request.
Simulate a failure (like a crash) immediately after the 'yes' response by uncommenting the sleep lines in the node's code and stopping the node during this period.
Switch TC to Recovery Mode:

Change the mode of the TC to 'recovery'. In this mode, the TC starts listening for inquiries from participant nodes.
Ensure Aborted Transaction Record:

Verify that the transaction ID is listed in the 'aborted commits' file (node2_aborted_commits.txt or node3_aborted_commits.txt) of the failed node. This file represents the node's knowledge of transactions that were in progress at the time of its failure.
Restart and Recover the Failed Node:

Restart the failed participant node.
Upon restart, the node should automatically check its 'aborted commits' file.
The node will send an 'INQUIRE' message to the TC for each transaction listed in the file.
Observe the Recovery Process:

The TC, upon receiving an 'INQUIRE' message, should respond with the current status of the transaction (commit or abort).
The participant node should then follow through with the TC's instructions to either commit or abort the transaction.
Notes:

This test demonstrates the resilience of the participant nodes and their ability to recover and complete transactions after unexpected failures.
It highlights the importance of the TC's recovery mode in assisting participant nodes to reconcile their state with the overall transaction state.
The automated inquiry and response mechanism ensures the integrity and consistency of the distributed commit process even in the face of node failures.

#Additional Notes
Ensure all nodes and the TC are running on the same network.
The default ports are set in the scripts, but they can be modified if needed.
Detailed logging is implemented for easier debugging and understanding of the protocol flow.
