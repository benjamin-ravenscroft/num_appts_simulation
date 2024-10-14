from collections import deque    # use to enable processing of servers on different threads
import queue
from objects.patient import Patient
import numpy as np
# multithreading
from threading import Thread

class Waitlist():
    def __init__(self, priorities: list, arrival_rates: dict, priority_wlist: bool=False,
                 max_age: float=4, appts_needed: dict=None, wait_flag: bool=False,
                 max_ax_age: float=3):
        self._priorities = priorities
        self._priority_wlist = priority_wlist
        self._waitlist = self.create_waitlist()
        self._arrival_rates = arrival_rates
        self._max_age = max_age
        self._appts_needed = appts_needed
        self._wait_flag = wait_flag
        self._max_ax_age = max_ax_age*52    # conver to weeks
        pass

    def create_waitlist(self):
        """Create the waitlist for the simulation.

        Returns:
            dict: dictionary of waitlist queues.
        """
        return {i: queue.Queue() for i in self._priorities}

    def add_clients(self, n, s_val: int, epoch: int, waitlist: queue.Queue):
        """Expand a classes waitlist by n patients for the new epoch.

        Args:
            n (int): Number of clients to add
            s_val (int): priority value
            epoch (int): current epoch
            waitlist (queue.Queue): priority score's repsective queue
        """
        for _ in range(n):
            p = Patient(s_val, np.random.random()*130 + 26, epoch,
                        appts_needed=self._appts_needed[s_val],
                        max_age=self._max_age, wait_flag=self._wait_flag)
            waitlist.put(p)
            waitlist.task_done()
        
    def process_epoch(self, epoch: int):
        """Process the waitlist for the current epoch. 
        Runs at the start of each epoch and adds patients to 
        the waitlist according to the arrival process. Pulls
        the number of patients off of the waitlist according to the
        number of empty slots in the servers.

        Args:
            epoch (int): Epoch number.
        """
        prod_threads = []
        for s_val, rate in self._arrival_rates.items():
            n = np.random.poisson(rate)
            prod_threads.append(Thread(target=self.add_clients, args=(n, s_val, epoch, self._waitlist[s_val])))
        for t in prod_threads:
            t.start()
        for t in prod_threads:
            t.join()

    def get_clients(self, n):
        """Get the next patient from the waitlist.

        Args:
            epoch (int): Epoch number.

        Returns:
            Patient: Next patient in the waitlist.
        """
        clients = []
        if not self._priority_wlist:
            for _ in range(n):
                i = np.random.choice(self._priorities)
                try:
                    item = self._waitlist[i].get_nowait()
                except queue.Empty:
                    continue
                clients.append(item)
                n -= 1
                if n == 0:
                    return clients
            return clients
        else:
            for i in [3, 2, 1]:
                for _ in range(n):
                    try:
                        item = self._waitlist[i].get_nowait()
                    except queue.Empty:
                        break
                    clients.append(item)
                    n -= 1
                    if n == 0:
                        return clients
            return clients
                
    
    def get_waitlist(self):
        """Get the waitlist.

        Returns:
            dict: Waitlist.
        """
        return [self._waitlist[i] for i in self._priorities]
    
    def get_waitlist_size(self):
        """Get the size of the waitlist.
        
        Returns:
            dict[int]: Sizes of the waitlist for each priority.
        """
        return {i: self._waitlist[i].qsize() for i in self._priorities}

