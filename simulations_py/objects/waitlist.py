# use to enable processing of servers on different threads
from collections import deque
import queue
from objects.patient import Patient
import numpy as np
import pandas as pd
# multithreading
from threading import Thread


class Waitlist():
    def __init__(self, priorities: list, arrival_rates: dict, priority_wlist: bool = False,
                 max_age: float = 4, appts_needed: dict = None, wait_flag: bool = False,
                 max_ax_age: float = 4, priority_order: list = [1, 2, 3]):
        self._priorities = priorities
        self._priority_wlist = priority_wlist
        self._waitlist = self.create_waitlist()
        self._arrival_rates = arrival_rates
        self._max_age = max_age
        self._appts_needed = appts_needed
        self._wait_flag = wait_flag
        self._max_ax_age = max_ax_age*52    # conver to weeks
        self._priority_order = priority_order
        self._modality_flag = False
        self._modality_inter = False
        pass

    def get_modality_parametrization(self, path: str, interaction=False):
        # error checking
        try:
            df = pd.read_csv(path)
        except:
            raise Exception(f"Path '{path}' does not exist.")

        if 's_val' not in df.columns and interaction:
            raise Exception(
                f"Parametrization data missing categories but indicated use of interaction terms.")

        # assign values to dict
        self._modality_params = {}
        if interaction:
            self._modality_inter = True  # flip the indicator
            for s in df['s_val'].unique():
                self._modality_params[s] = {
                    'linear': df.loc[(df['s_val'] == s) &
                                     (df['param'] == 'pct_face'), 'coef'],
                    'quad': df.loc[(df['s_val'] == s) &
                                   (df['param'] == 'np.power(pct_face, 2)'), 'coef']
                }
        else:
            self._modality_params['linear'] = df.loc[(df['s_val'] == s) &
                                                     (df['param'] == 'pct_face'), 'coef']
            self._modality_params['linear'] = df.loc[(df['s_val'] == s) &
                                                     (df['param'] == 'np.power(pct_face, 2)'), 'coef']
        return

    def get_modality_policy(self, path: str):
        # error checking
        try:
            self.mod_policy = pd.read_csv(path)
        except:
            raise Exception(f"Path '{path}' does not exist.")
        return

    def set_priority_order(self, priorities: list):
        """Set the priority order for strict priority waitlist policy.

        Args:
            priorities (list): priorities in order
        """
        if set(priorities) != set(self._priorities):
            raise ValueError("Invalid priority order set.")
        self.priority_order = priorities

    def create_waitlist(self):
        """Create the waitlist for the simulation.

        Returns:
            dict: dictionary of waitlist queues.
        """
        if self._priority_wlist:
            return {i: queue.Queue() for i in self._priorities}
        else:
            return queue.Queue()

    def get_modality_n_appts(self, s_val: int, prop: float = 1):
        if self._modality_inter:
            return prop*self._modality_params[s_val]['linear'] + \
                (prop**2)*self._modality_params[s_val]['quad']
        else:
            return prop*self._modality_params['linear'] + \
                (prop**2)*self._modality_params['quad']

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
            if self._priority_wlist:
                prod_threads.append(Thread(target=self.add_clients, args=(
                    n, s_val, epoch, self._waitlist[s_val])))
            else:
                prod_threads.append(
                    Thread(target=self.add_clients, args=(n, s_val, epoch, self._waitlist)))
        for t in prod_threads:
            t.start()
        for t in prod_threads:
            t.join()

    def get_clients(self, n: int, epoch: int, output_queue: queue.Queue):
        """Get the next patient from the waitlist.

        Args:
            epoch (int): Epoch number.

        Returns:
            Patient: Next patient in the waitlist.
        """
        clients = []
        if not self._priority_wlist:
            while n > 0:
                try:
                    item = self._waitlist.get_nowait()
                except queue.Empty:
                    break
                if item.get_age(epoch) > self._max_ax_age:
                    output_queue.put(item.get_patient_data(epoch, True))
                else:
                    clients.append(item)
                    n -= 1
                if n == 0:
                    return clients
            return clients
        else:
            for i in self.priority_order:
                while n > 0:
                    try:
                        item = self._waitlist[i].get_nowait()
                    except queue.Empty:
                        break
                    if item.get_age(epoch) > self._max_ax_age:
                        output_queue.put(item.get_patient_data(epoch, True))
                    else:
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
        if self._priority_wlist:
            return [self._waitlist[i] for i in self._priorities]
        else:
            return self._waitlist

    def get_waitlist_size(self):
        """Get the size of the waitlist.

        Returns:
            dict[int]: Sizes of the waitlist for each priority.
        """
        if self._priority_wlist:
            return {i: self._waitlist[i].qsize() for i in self._priorities}
        else:
            return self._waitlist.qsize()

    def flush_waitlist_helper(self, epoch: int, output_queue: queue.Queue, priority: int = None):
        """Flush the waitlist for a single priority.

        Args:
            epoch (int): Epoch number.
            output_queue (queue.Queue): Queue to store the output.
            priority (int): Priority of the waitlist to flush.
        """
        while True:
            try:
                if self._priority_wlist:
                    item = self._waitlist[priority].get_nowait()
                else:
                    item = self._waitlist.get_nowait()
            except queue.Empty:
                break
            else:
                output_queue.put(item.get_patient_data(epoch,
                                                       True if item.get_age(
                                                           epoch) > self._max_ax_age else np.nan,
                                                       True))
        return

    def flush_waitlist(self, epoch: int, output_queue: queue.Queue):
        """Flush the waitlist at the end of the simulation.

        Args:
            output_queue (queue.Queue): Queue to store the output.
        """
        threads = []
        if self._priority_wlist:
            for i in self._priorities:
                threads.append(Thread(target=self.flush_waitlist_helper,
                                      args=(epoch, output_queue, i)))
        else:
            threads.append(Thread(target=self.flush_waitlist_helper,
                                  args=(epoch, output_queue)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return
