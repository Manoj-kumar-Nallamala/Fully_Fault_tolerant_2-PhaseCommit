import socket
import threading
import time

# Configuration
tc_address = 'localhost', 1025  # Transaction Coordinator's address
participant_address = 'localhost', 1026  # This participant's address
prepare_timeout = 60  # Timeout in seconds for the "prepare" message

# State
state = {'transaction_id': None, 'prepared': False, 'decision': 'abort'}

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
                    handle_prepare()

def handle_prepare():
    """ Handles the "prepare" message from the TC. """
    global state
    state['prepared'] = True

    print(f"Node preparing for transaction {state['transaction_id']}...")
    # Simulate decision making
    user_decision = input("Do you want to commit the transaction? (yes/no): ").lower()

    if user_decision == 'yes':
        print(f"Transaction {state['transaction_id']} prepared successfully.")
        send_response_to_tc('YES')
    else:
        print(f"Transaction {state['transaction_id']} aborted.")
        send_response_to_tc('NO')


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
    listen_thread = threading.Thread(target=listen_to_tc)
    listen_thread.start()
    listen_thread.join()

if __name__ == "__main__":
    main()
