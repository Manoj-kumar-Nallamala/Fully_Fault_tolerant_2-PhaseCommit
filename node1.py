import socket
import threading
import time
# Configuration
participant_nodes = ['localhost:1026', 'localhost:1027']  # Example addresses for participant nodes

# States
state = {'transaction_id': None, 'prepare_sent': False, 'responses': {}}

def send_prepare_message(transaction_id, simulate_failure):
    global state
    state['transaction_id'] = transaction_id
    state['prepare_sent'] = False
    state['responses'] = {node: None for node in participant_nodes}

    # Check if we need to simulate TC failure
    if simulate_failure:
        print(f"Simulating TC failure for transaction {transaction_id}. No 'prepare' message will be sent.")
        return

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

import time  # Make sure to import the time module

def listen_for_responses():
    global state
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 1025))
        s.listen()

        responses_received = 0
        expected_responses = len(participant_nodes)
        start_time = time.time()  # Record the start time

        while responses_received < expected_responses and time.time() - start_time < 30:  # 30-second timeout
            try:
                s.settimeout(30 - (time.time() - start_time))  # Adjust the timeout as time elapses
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
            print("All participants agreed to commit. Committing transaction.")
        else:
            print("At least one participant voted to abort or did not respond. Aborting transaction.")






        # Check if all responses are 'YES'
        if all(response == 'YES' for response in state['responses'].values()):
            print("All participants agreed to commit.")
            # Send commit message to all participants
            # ...
        else:
            print("At least one participant voted to abort.")
            # Send abort message to all participants
            # ...



def main():
    while True:  # Loop to handle multiple transactions
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

if __name__ == "__main__":
    main()
