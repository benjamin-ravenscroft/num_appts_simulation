from objects.server import Server
from objects.waitlist import Waitlist
from threading import Thread
import queue
import pyarrow as pa
import pyarrow.dataset as pda
import pandas as pd

class Simulation():
    def __init__(self, n_servers: int, epoch_len: int, max_age: float,
                 priority_wlist: bool=False, patient_types: dict=None, wait_flag: bool=False):
        self._n_servers = n_servers
        self._epoch_len = epoch_len
        self._max_age = max_age
        self._priority_wlist = priority_wlist
        self._patient_types = patient_types
        self.waitlist = self.create_waitlist(wait_flag)
        self.servers = self.create_servers()
        pass
    
    def create_servers(self):
        return [Server(self._epoch_len) for _ in range(self._n_servers)]
    
    def create_waitlist(self, wait_flag):
        priorities = list(self._patient_types.keys())
        appts_needed = {k: v['appts_needed'] for k, v in self._patient_types.items()}
        arrival_rates = {k: v['arrival_rate'] for k, v in self._patient_types.items()}
        return Waitlist(priorities, arrival_rates, self._priority_wlist, 
                        self._max_age, appts_needed, wait_flag)
    
    def fill_server_slots(self, clients):
        for server in self.servers:
            while server.has_open_slot():
                p = clients.pop(0)
                server.add_client(p)
                if len(clients) == 0:
                    return

    def fill_empty_servers(self):
        # count the number of empty slots across all servers
        empty_slots = sum([s.open_slots() for s in self.servers])
        # get the number of clients needed from the waitlist
        clients = self.waitlist.get_clients(empty_slots)
        self.fill_server_slots(clients)

    def run_servers(self, epoch: int, output_queue: queue.Queue):
        threads = []
        for s in self.servers:
            t = Thread(target=s.serve_clients, args=(epoch, output_queue))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    def process_epochs(self, epochs: int, output_queue: queue.Queue):
        for epoch in range(epochs):
            self.waitlist.process_epoch(epoch)
            self.fill_empty_servers()
            self.run_servers(epoch, output_queue=output_queue)
        output_queue.put(None)

    def process_output(self, output_dir: str, output_queue: queue.Queue):
        res_list = []
        columns=['s_val', 'age_at_ref', 'ref_epoch', 
                'ax_epoch', 'n_appts', 'dis_epoch', 
                'age_out']
        batch = 0
        while True:
            item = output_queue.get()
            if item is None:
                res = pd.DataFrame(res_list, columns=columns)
                res.to_parquet(output_dir + f'/part-{batch}.parquet', index=False)
                break
            else:
                res_list.append(item)
            if len(res_list) % 100 == 0:
                res = pd.DataFrame(res_list, columns=columns)
                res.to_parquet(output_dir + f'/part-{batch}.parquet', index=False)
                res_list = []
                batch += 1
        pass

    def run_simulation(self, n_epochs: int, output_dir: str):
        output_queue = queue.Queue()
        print("Simulation starting...")
        threads = [Thread(target=self.process_epochs, args=(n_epochs, output_queue)),
                   Thread(target=self.process_output, args=(output_dir, output_queue))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("Simulation complete.")
        

    
    
