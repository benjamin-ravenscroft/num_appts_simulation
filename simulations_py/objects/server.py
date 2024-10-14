from collections import deque
import queue
from objects.patient import Patient
from objects.waitlist import Waitlist

class ServerException(Exception):
    def __init__(self, message):
        super().__init__(message)

class Server():
    def __init__(self, n_clients: int):
        self._n_clients = n_clients
        self._clients = deque() # initialize the empty queue

    def has_open_slot(self):
        """Check if the server has an open slot."""
        return len(self._clients) < self._n_clients
    
    def open_slots(self):
        """Get the number of open slots in the server."""
        return self._n_clients - len(self._clients)
    
    def add_client(self, client: Patient):
        """Add a client to the server queue.
        
        Args:
            client (Patient): patient to add to the server queue.
        """
        if len(self._clients) < self._n_clients:
            self._clients.append(client)
        else:
            raise ServerException("Server queue is full. Cannot add client.")
    
    def get_n_clients(self):
        """Get the number of clients in the server queue."""
        return len(self._clients)
    
    def get_queue(self):
        """Get the queue of clients."""
        return self._clients

    def serve_clients(self, epoch: int, output_queue: queue.Queue):
        """Serve the next client in the queue.
        Uses a queue to store the output data when a patient ages-out
        or completes all appointments. This allows for servers to be
        run in parallel, separate threads while sharing a single output queue.
        The output queue is then written to a file or other output mechanism.
        """
        rem = 1 # initialize the remaining slot time to 1
        while rem > 0 and len(self._clients) > 0:
            c = self._clients.popleft()
            if c.check_age(epoch):
                rem -= c.add_appt(epoch, rem)
            else:
                output_queue.put(c.get_patient_data(epoch, age_out=True))
                continue
            if c.check_appts():
                output_queue.put(c.get_patient_data(epoch, age_out=False))
                continue
            else:
                self._clients.append(c)
    

    