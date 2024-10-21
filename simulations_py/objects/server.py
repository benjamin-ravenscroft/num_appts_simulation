from collections import deque
import queue
from objects.patient import Patient
from objects.waitlist import Waitlist
import numpy as np

class ServerException(Exception):
    def __init__(self, message):
        super().__init__(message)

class Server():
    def __init__(self, n_clients: int):
        self._n_clients = n_clients
        self._clients = deque() # initialize the empty queue
        self.att_probs = {'att': 0.85,
                          'ns': 0.4,
                          'lm_canc': 0.6,
                          'adv_canc': 0.5}

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
    
    def cancellation_check(self, client: Patient):
        """Check if the client has cancelled/no-showed their appointment, based on parameters.

        Args:
            client (Patient): client object

        Returns:
            int: 0 for attended, 1 for no-show/last-minute cancellation, 2 for advanced cancellation
        """
        prob = np.random.uniform(0,1)
        if prob < self.att_probs['att']:
            return 0
        elif prob < self.att_probs['att'] + self.att_probs['ns']:
            return 1
        elif prob < self.att_probs['att'] + self.att_probs['ns'] + self.att_probs['lm_canc']:
            return 1
        else:
            return 2

    def serve_clients(self, epoch: int, output_queue: queue.Queue, cancellation=False):
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
                if not cancellation:
                    rem -= c.add_appt(epoch, rem)
                else:
                    canc_ind = self.cancellation_check(c)
                    match canc_ind:
                        case 0: # attended
                            rem -= c.add_appt(epoch, rem)
                        case 1: # no-show/last-minute cancellation
                            rem -= 1 # "waste" the slot
                        case 2: # advanced cancellation
                            # do not give the patient an appointment, 
                            # but keep appt slot for epoch available
                            continue
            else:
                output_queue.put(c.get_patient_data(epoch, age_out=True))
                continue
            if c.check_appts():
                output_queue.put(c.get_patient_data(epoch, age_out=False))
                continue
            else:
                self._clients.append(c)
    

    