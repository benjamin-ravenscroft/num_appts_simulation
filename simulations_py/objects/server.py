from collections import deque
import queue
from objects.patient import Patient
from objects.waitlist import Waitlist
import numpy as np


class ServerException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Server():
    def __init__(self, n_clients: int, att_probs: dict, cancellation: bool = False,
                 modality_params: dict = {}, modality_policy: dict = {},
                 modality_flag: bool = False, modality_inter: bool = False):
        self._n_clients = n_clients
        self._clients = deque()  # initialize the empty queue
        self._att_probs = att_probs
        self._cancellation = cancellation
        self._modality_params = modality_params
        self._modality_policy = modality_policy
        self._modality_flag = modality_flag
        self._modality_inter = modality_inter

    def has_open_slot(self) -> bool:
        """Check if the server has an open slot."""
        return len(self._clients) < self._n_clients

    def open_slots(self) -> int:
        """Get the number of open slots in the server."""
        return self._n_clients - len(self._clients)

    def add_client(self, client: Patient) -> None:
        """Add a client to the server queue.

        Args:
            client (Patient): patient to add to the server queue.
        """
        if len(self._clients) < self._n_clients:
            self._clients.append(client)
        else:
            raise ServerException("Server queue is full. Cannot add client.")

    def get_n_clients(self) -> int:
        """Get the number of clients in the server queue."""
        return len(self._clients)

    def get_queue(self) -> queue.Queue:
        """Get the queue of clients."""
        return self._clients

    def cancellation_check(self, modality: int, client: Patient) -> int:
        # To-Do: implement functionality to vary attendance probabilities by modality, perhaps known future bookings
        """Check if the client has cancelled/no-showed their appointment, based on parameters.

        Args:
            client (Patient): client object

        Returns:
            int: 0 for attended, 1 for no-show/last-minute cancellation, 2 for advanced cancellation
        """
        prob = np.random.uniform(0, 1)
        if prob < self._att_probs[modality]['att']:
            return 0
        elif prob < self._att_probs[modality]['att'] + self._att_probs[modality]['ns']:
            return 1
        elif prob < self._att_probs[modality]['att'] + \
                self._att_probs[modality]['ns'] + self._att_probs[modality]['lm']:
            return 1
        else:
            return 2

    def _get_appt_modality(self, s_val: int) -> int:
        """Get modality of the appointment based on policy.

        Args:
            patient (Patient): patient instance

        Returns:
            int: 0 for virtual, 1 for in-person.
        """
        rand = np.random.uniform(0, 1)
        if rand < self._modality_policy[s_val]:
            return 0
        else:
            return 1

    def _get_modality_inc(self, prop: float, s_val: int) -> float:
        if self._modality_inter:
            return prop*self._modality_params[s_val]['linear'] + \
                (prop**2)*self._modality_params[s_val]['quad']
        else:
            return prop*self._modality_params['linear'] + \
                (prop**2)*self._modality_params['quad']

    def serve_clients(self, epoch: int, output_queue: queue.Queue) -> None:
        """Serve the next client in the queue.
        Uses a queue to store the output data when a patient ages-out
        or completes all appointments. This allows for servers to be
        run in parallel, separate threads while sharing a single output queue.
        The output queue is then written to a file or other output mechanism.
        """
        rem = 1  # initialize the remaining slot time to 1
        while rem > 0 and len(self._clients) > 0:
            c = self._clients.popleft()
            if c.check_age(epoch):
                # add modality adjustment to number of appointments needed
                if self._modality_flag:
                    inc = self._get_modality_inc(
                        c.get_modality_prop(), c.get_s_val())
                    c.inc_appts_needed(inc)
                # process giving appointment
                if not self._cancellation:
                    mod = self._get_appt_modality(c.get_s_val())
                    rem -= c.add_appt(epoch, rem, mod)
                else:
                    canc_ind = self.cancellation_check(c)
                    match canc_ind:
                        case 0:  # attended
                            rem -= c.add_appt(epoch, rem, mod)
                        case 1:  # no-show/last-minute cancellation
                            rem -= 1  # "waste" the slot
                        case 2:  # advanced cancellation
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
