import socket
import threading
import time
import os
# Configuration
participant_nodes = ['localhost:1026', 'localhost:1027']  # Example addresses for participant nodes

# States
state = {'transaction_id': None, 'prepare_sent': False, 'responses': {}}

def notify_participant_nodes_of_new_transaction(transaction_id):
    """ Notify participant nodes about the start of a new transaction. """
    for node in participant_nodes:
        host, port = node.split(':')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, int(port)))
                s.sendall(f"START {transaction_id}".encode())
                print(f"Notified {node} about the start of transaction {transaction_id}")
        except ConnectionError as e:
            print(f"Failed to notify {node} about the start of transaction {transaction_id}: {e}")

def send_prepare_message(transaction_id, simulate_failure):
    global state
    state['transaction_id'] = transaction_id
    state['prepare_sent'] = False
    state['responses'] = {node: None for node in participant_nodes}

    # Check if we need to simulate TC failure
    if simulate_failure:
        notify_participant_nodes_of_new_transaction(transaction_id)
        print(f"Simulating TC failure for transaction {transaction_id}. No 'prepare' message will be sent.")
        time.sleep(40)

    # Send prepare message to each participant node
    for node in participant_nodes:
        host, port = node.split(':')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, int(port)))
                s.sendall(f"PREPARE {transaction_id}".encode())
                print(f"Sent PREPARE to {node}")
            except ConnectionError as e:
                print(f"Failed to send PREPARE to {node}: {e}")

    state['prepare_sent'] = True


def write_transaction_to_file(transaction_id, nodes_commit_status):
    """ Writes the transaction information and commit status to a file. """
    filename = f"transaction_{transaction_id}.txt"
    with open(filename, 'w') as file:
        data_entries = [f"{node}:{status}" for node, status in nodes_commit_status.items()]
        data = f"{transaction_id},{'|'.join(data_entries)}"
        file.write(data)




def send_commit_messages(transaction_id, nodes_commit_status):
    """ Sends a commit message to each participant node and updates the file upon success. """
    for node, status in nodes_commit_status.items():
        if status == 'pending':
            host, port = node.split(':')
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, int(port)))
                    s.sendall(f"COMMIT {transaction_id}".encode())
                    print(f"Sent COMMIT to {node}")
                    nodes_commit_status[node] = 'done'
            except ConnectionError as e:
                print(f"Failed to send COMMIT to {node}: {e}")
    
    write_transaction_to_file(transaction_id, nodes_commit_status)

def handle_inquiry(transaction_id, client_socket):
    """ Handle an inquiry about a transaction's status. """
    try:
        filename = f"transaction_{transaction_id}.txt"
        if os.path.exists(filename):
            # Assuming that the existence of the file means the transaction was committed
            response_message = f"COMMIT {transaction_id}"
        else:
            response_message = f"ABORT {transaction_id}"
        client_socket.sendall(response_message.encode())
    except Exception as e:
        print(f"Error handling inquiry for transaction {transaction_id}: {e}")

def listen_for_requests():
    """ Listen for and handle incoming requests from participant nodes. """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 1025))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024).decode()
                if data.startswith("INQUIRE"):
                    transaction_id = data.split()[1]
                    handle_inquiry(transaction_id, conn)
                # Handle other types of messages...



def recover_transactions():
    """ Recover transactions from files and complete any unfinished commitments. """
    for filename in os.listdir('.'):
        if filename.startswith('transaction_') and filename.endswith('.txt'):
            with open(filename, 'r') as file:
                data = file.read()

            transaction_id, nodes_data = data.split(',')
            nodes_commit_status = {}
            for node_data in nodes_data.split('|'):
                node_address, status = node_data.rsplit(':', 1)  # Split from the right at the last colon
                nodes_commit_status[node_address] = status

            pending_nodes = {node: status for node, status in nodes_commit_status.items() if status == 'pending'}

            if pending_nodes:
                send_commit_messages(transaction_id, pending_nodes)






def listen_for_responses():
    global state
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 1025))
        s.listen()

        responses_received = 0
        expected_responses = len(participant_nodes)
        start_time = time.time()  # Record the start time

        while responses_received < expected_responses and time.time() - start_time < 60:  # 30-second timeout
            try:
                s.settimeout(60 - (time.time() - start_time))  # Adjust the timeout as time elapses
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024).decode()
                    transaction_id, responding_port, response = data.split()
                    if transaction_id == state['transaction_id']:
                        responding_node = f'localhost:{responding_port}'
                        if responding_node in participant_nodes:
                            state['responses'][responding_node] = response
                            responses_received += 1
                            print(f"Received response: {response} from {responding_node}")
                            if response == 'NO':  # Abort immediately if any node responds with 'NO'
                                print("At least one participant voted to abort. Aborting transaction.")
                                return
            except socket.timeout:
                # Timeout occurred before receiving all responses
                print("Response timeout. Aborting transaction.")
                return

        # Check if all responses are 'YES'
        if all(response == 'YES' for response in state['responses'].values()):
            nodes_commit_status = {node: 'pending' for node in participant_nodes}
            write_transaction_to_file(state['transaction_id'], nodes_commit_status)
            print("All participants agreed to commit. Writing to file and committing transaction.")
            send_commit_messages(state['transaction_id'], nodes_commit_status)
        else:
            print("At least one participant voted to abort or did not respond. Aborting transaction.")


def listen_for_node_requests():
    """ Continuously listen for and handle requests from participant nodes. """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 1025))
        s.listen()

        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024).decode()
                if data.startswith("INQUIRE"):
                    transaction_id = data.split()[1]
                    handle_inquiry(transaction_id, conn)
                elif data.startswith("PREPARE"):
                    # Add logic to handle 'PREPARE' requests
                    pass
                # Add other request types as necessary


def main():
    while True:
        # Choose the mode of operation for the TC
        mode = input("Select mode - 'normal' for transactions, 'recovery' for node requests, 'exit' to stop: ").lower()

        if mode == 'normal':
            # Normal mode: Handle transactions
              # Recover any incomplete transactions
            while True:
                recover_transactions() ##Recovering TC transactions
                transaction_id = input("Enter transaction ID to initiate (or 'exit' to stop): ")
                if transaction_id.lower() == 'exit':
                    break
                simulate_failure = input("Simulate TC failure? (yes/no): ").lower() == 'yes'
                prepare_thread = threading.Thread(target=send_prepare_message, args=(transaction_id, simulate_failure))
                response_thread = threading.Thread(target=listen_for_responses)

                prepare_thread.start()
                response_thread.start()

                prepare_thread.join()  # Wait for prepare phase to complete
                state['prepare_sent'] = False  # Signal response thread to stop
                response_thread.join()  # Wait for response thread to complete

                print("Transaction state after prepare phase:", state)

        elif mode == 'recovery':
            # Recovery mode: Listen for node requests
            print("Starting in recovery mode. Listening for node requests...")
            node_listener_thread = threading.Thread(target=listen_for_node_requests)
            node_listener_thread.start()
            node_listener_thread.join()

        elif mode == 'exit':
            print("Exiting TC.")
            break
        else:
            print("Invalid mode. Please choose 'normal', 'recovery', or 'exit'.")

if __name__ == "__main__":
    main()
