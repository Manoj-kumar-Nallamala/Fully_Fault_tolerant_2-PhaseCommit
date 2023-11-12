import socket
import threading
import time

# Configuration
tc_address = 'localhost', 1025  # Transaction Coordinator's address
participant_address = 'localhost', 1027  # This participant's address
prepare_timeout = 60  # Timeout in seconds for the "prepare" message

# State
state = {'transaction_id': None, 'prepared': False, 'decision': 'abort'}

timed_out_transactions = []

def transaction_timeout(transaction_id):
    """ Function to be called when the transaction times out """
    global timed_out_transactions
    if transaction_id not in timed_out_transactions:
        timed_out_transactions.append(transaction_id)
    print(f"Transaction {transaction_id} timed out waiting for 'prepare' message.")

def start_transaction_timeout(duration, transaction_id):
    """ Start a timer for the transaction """
    timeout_timer = threading.Timer(duration, transaction_timeout, [transaction_id])
    timeout_timer.start()

# Global state
state = {
    'transaction_id': None,
    'prepared': False,
    'timed_out': False
}


def handle_start_transaction(transaction_id):
    """ Handle the start of a new transaction. """
    global state
    state['transaction_id'] = transaction_id
    state['prepared'] = False
    state['timed_out'] = False
    start_transaction_timeout(30,transaction_id)

def listen_to_tc():
    """ Listens for messages from the Transaction Coordinator. """
    global state

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(participant_address)
        s.listen()

        while True:  # Loop to handle multiple transactions
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024).decode()
                print(f"Received message from TC: {data}")
                
                if data.startswith("PREPARE"):
                    transaction_id = data.split()[1]
                    state['transaction_id'] = transaction_id
                    state['prepared'] = False  # Reset the prepared state for the new transaction
                    state['decision'] = 'abort'  # Reset the decision for the new transaction
                    handle_prepare(transaction_id)
                elif data.startswith("COMMIT"):
                    transaction_id = data.split()[1]
                    append_to_committed_file(transaction_id)
                    remove_aborted_commit(transaction_id)
                    print(f"Transaction {transaction_id} committed.")

def handle_prepare(transaction_id):
    """ Handles the "prepare" message from the TC. """
    global state
    user_decision = input("Do you want to commit the transaction? (yes/no): ").lower()
    if transaction_id in timed_out_transactions:
        print(f"Transaction {transaction_id} already timed out. Responding 'no'.")
        send_response_to_tc('NO', transaction_id)
        return
    state['prepared'] = True

    print(f"Node preparing for transaction {state['transaction_id']}...")
    # Simulate decision making
    

    if user_decision == 'yes':
        write_aborted_commit(state['transaction_id'])
        print(f"Transaction {state['transaction_id']} prepared successfully.")
        send_response_to_tc('YES')
    else:
        print(f"Transaction {state['transaction_id']} aborted.")
        send_response_to_tc('NO')

def write_aborted_commit(transaction_id):
    """ Write the transaction ID to the aborted commit file. """
    with open('node3_aborted_commits.txt', 'a') as file:  # Use 'node3_aborted_commits.txt' for Node3
        file.write(transaction_id + "\n")

def remove_aborted_commit(transaction_id):
    """ Remove the transaction ID from the aborted commit file. """
    with open('node3_aborted_commits.txt', 'r') as file:  # Use 'node3_aborted_commits.txt' for Node3
        lines = file.readlines()
    with open('node3_aborted_commits.txt', 'w') as file:  # Use 'node3_aborted_commits.txt' for Node3
        for line in lines:
            if line.strip() != transaction_id:
                file.write(line)
def append_to_committed_file(transaction_id):
    """ Append the committed transaction ID to the committed transactions file. """
    # Use the appropriate file name for each node
    committed_file = 'node3committed.txt'  # Use 'node3committed.txt' for Node3
    with open(committed_file, 'a') as file:
        file.write(transaction_id + "\n")

def inquire_transaction_status(transaction_id):
    """ Inquire about the status of a transaction from the TC. """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(tc_address)
            s.sendall(f"INQUIRE {transaction_id}".encode())
            response = s.recv(1024).decode()
            print(f"Received response for transaction {transaction_id}: {response}")
            # Handle the response (commit or abort) accordingly
        except ConnectionError as e:
            print(f"Failed to connect to TC: {e}")

def check_aborted_transactions():
    """ Check for any aborted transactions and inquire about their status. """
    try:
        with open('node3_aborted_commits.txt', 'r') as file:  # Use the correct file name for each node
            transaction_ids = file.readlines()
        for transaction_id in transaction_ids:
            transaction_id = transaction_id.strip()
            inquire_transaction_status(transaction_id)
    except FileNotFoundError:
        pass  # No aborted commits file found

# Call check_aborted_transactions periodically or during startup

def send_response_to_tc(response):
    """ Sends a response to the Transaction Coordinator along with the node's identifier (port number). """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(tc_address)
            message = f"{state['transaction_id']} {participant_address[1]} {response}"
            s.sendall(message.encode())
            print(f"Sent {response} to TC for transaction {state['transaction_id']}")
        except ConnectionError as e:
            print(f"Failed to send response to TC: {e}")


def main():
    check_aborted_transactions()
    listen_thread = threading.Thread(target=listen_to_tc)
    listen_thread.start()
    listen_thread.join()

if __name__ == "__main__":
    main()
