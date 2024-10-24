from objects.server import Server
from objects.waitlist import Waitlist
from threading import Thread
import queue
import pyarrow as pa
import pyarrow.dataset as pda
import pandas as pd


class Simulation():
    def __init__(self, n_servers: int, epoch_len: int, max_age: float,
                 priority_wlist: bool = False, patient_types: dict = None, wait_flag: bool = False, priority_order: list = [1, 2, 3],
                 att_probs: dict = {},
                 cancellation: bool = False):
        self._n_servers = n_servers
        self._epoch_len = epoch_len
        self._max_age = max_age
        self._priority_wlist = priority_wlist
        self._patient_types = patient_types
        self._att_probs = att_probs
        self._cancellation = cancellation
        self.waitlist = self.create_waitlist(wait_flag, priority_order)
        # self.servers = self.create_servers()
        # modality effect indicators
        self._modality_flag = False
        self._modality_inter = False
        self._modality_params = {}  # initialize empty dict
        self._modality_policy = {}
        pass

    def fetch_att_probs(self, path: str) -> None:
        """Fetch method for getting attendance probability parametrization from file.

        Args:
            path (str): Path to parametrization file in CSV format.

        Raises:
            Exception: Exception if path does not exist.
            Exception: Exception if parametrization is missing severity scores.
        """
        try:
            df = pd.read_csv(path)
        except:
            raise Exception(f"Path '{path}' does not exist.")
        if 's_val' not in df.columns:
            raise Exception(
                "Attendance probability parametrization missing severity scores.")

        self._att_probs = {int(row['s_val']): {
            'att': row['att'],
            'ns': row['ns'],
            'lm': row['lm'],
            'adv': row['adv']
        } for _, row in df.iterrows()}

    def get_att_probs(self):
        return self._att_probs

    def fetch_modality_parametrization(self, path: str, interaction=False):
        # error checking
        try:
            df = pd.read_csv(path)
        except:
            raise Exception(f"Path '{path}' does not exist.")

        if 's_val' not in df.columns and interaction:
            raise Exception(
                f"Parametrization data missing categories but indicated use of interaction terms.")

        # assign values to dict
        if interaction:
            self._modality_inter = True  # flip the indicator
            for s in df['s_val'].unique():
                self._modality_params[s] = {
                    'linear': df.loc[(df['s_val'] == s) &
                                     (df['param'] == 'pct_face'), 'coef'].values[0],
                    'quad': df.loc[(df['s_val'] == s) &
                                   (df['param'] == 'np.power(pct_face, 2)'), 'coef'].values[0]
                }
        else:
            self._modality_params['linear'] = df.loc[(df['param'] == 'pct_face'),
                                                     'coef'].values[0]
            self._modality_params['quad'] = df.loc[(df['param'] == 'np.power(pct_face, 2)'),
                                                   'coef'].values[0]
        pass

    def get_modality_parametrization(self):
        return self._modality_params

    def fetch_modality_policy(self, path: str):
        # error checking
        try:
            df = pd.read_csv(path)
        except:
            raise Exception(f"Path '{path}' does not exist.")

        self._modality_policy = {
            int(row['s_val']): row['pct_face'] for _, row in df.iterrows()}
        return

    def get_modality_policy(self):
        return self._modality_policy

    def create_servers(self):
        return [Server(self._epoch_len, self._att_probs, self._cancellation,
                       self._modality_params, self._modality_policy,
                       self._modality_flag, self._modality_inter) for _ in range(self._n_servers)]

    def create_waitlist(self, wait_flag, priority_order):
        priorities = list(self._patient_types.keys())
        appts_needed = {k: v['appts_needed']
                        for k, v in self._patient_types.items()}
        arrival_rates = {k: v['arrival_rate']
                         for k, v in self._patient_types.items()}
        return Waitlist(priorities, arrival_rates, self._priority_wlist,
                        self._max_age, appts_needed, wait_flag, 4, priority_order)

    def fill_server_slots(self, clients):
        for server in self.servers:
            while server.has_open_slot():
                p = clients.pop(0)
                server.add_client(p)
                if len(clients) == 0:
                    return

    def fill_empty_servers(self, epoch: int, output_queue: queue.Queue):
        # count the number of empty slots across all servers
        empty_slots = sum([s.open_slots() for s in self.servers])
        # get the number of clients needed from the waitlist
        clients = self.waitlist.get_clients(empty_slots, epoch, output_queue)
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
            self.fill_empty_servers(epoch, output_queue)
            self.run_servers(epoch, output_queue=output_queue)
        # flush the remaining clients from the waitlist
        self.waitlist.flush_waitlist(epoch+1, output_queue)
        output_queue.put(None)

    def process_output(self, output_dir: str, output_queue: queue.Queue):
        res_list = []
        columns = ['s_val', 'age_at_ref', 'ref_epoch',
                   'ax_epoch', 'n_appts', 'pct_face',
                   'dis_epoch', 'age_out', 'wlist_flush']
        batch = 0
        while True:
            item = output_queue.get()
            if item is None:
                res = pd.DataFrame(res_list, columns=columns)
                res.to_parquet(
                    output_dir + f'/part-{batch}.parquet', index=False)
                break
            else:
                res_list.append(item)
            if len(res_list) % 100 == 0:
                res = pd.DataFrame(res_list, columns=columns)
                res.to_parquet(
                    output_dir + f'/part-{batch}.parquet', index=False)
                res_list = []
                batch += 1
        pass

    def run_simulation(self, n_epochs: int, output_dir: str):
        # create the servers
        self.servers = self.create_servers()
        output_queue = queue.Queue()
        print("Simulation starting...")
        threads = [Thread(target=self.process_epochs, args=(n_epochs, output_queue)),
                   Thread(target=self.process_output, args=(output_dir, output_queue))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("Simulation complete.")
