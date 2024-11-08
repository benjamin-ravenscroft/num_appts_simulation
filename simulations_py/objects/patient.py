import scipy.stats as ss
import numpy as np

class Patient():
    def __init__(self, s_val: int, age: float, epoch: int, appts_needed: int, max_age: float, 
                 wait_flag: bool = False, wait_inter_flag: bool=False):
        self._s_val = s_val
        self._age_at_ref = age
        self._ref_epoch = epoch
        # initialize to None until (and only if) patient is assessed
        self._ax_epoch = None
        self.n_appts = 0
        self._n_face = 0  # keep track of num in-person appts
        # self._base_appts_needed = appts_needed    # uncomment to use deterministic effect
        # self._base_appts_needed = ss.norm.rvs(loc=appts_needed, scale=1)  # uncomment to use stochastic effect
        self._base_appts_needed = self._random_integer_round(appts_needed)  # uncomment to use stochastic integer rounding effect
        self._appts_needed = self._base_appts_needed
        self._max_age = max_age
        self._wait_flag = wait_flag
        self._wait_inter_flag = wait_inter_flag

    def _random_integer_round(self, x: float) -> int:
        """Randomly rounds a float to the higher/lower integer. Does so proportionally to the decimal value.

        Args:
            x (float): float number of estimated appointments

        Returns:
            int: integer rounded number of appointments
        """
        return np.random.choice([np.floor(x), np.ceil(x)], p=[1 - (x % 1), x % 1])

    def assessment(self, epoch: int) -> None:
        """Set the epoch the patient was assessed at.

        Args:
            epoch (int): epoch assessment occured during
        """
        self._ax_epoch = epoch
        if self._wait_flag:
            wait_time = (epoch - self._ref_epoch)/52
            # hard coded coefficients for wait time effect
            # To-Do: need to add an import method to pull from the csv file directly (or import from user)
            if self._wait_inter_flag:
                match self._s_val:
                    case 1: self._base_appts_needed += (0.1483 * wait_time) + (-0.06277 * (wait_time**2))
                    case 2: self._base_appts_needed += (2.862 * wait_time) + (-0.6642 * (wait_time ** 2))
                    case 3:
                        self._base_appts_needed += (1.4022 * wait_time) + (-0.3463 * (wait_time ** 2))
                    case _:
                        pass
            else:
                self._base_appts_needed += 1.2 * wait_time
            # pass base appointments to appointments needed
            # self._appts_needed = self._base_appts_needed  # uncomment to use deterministic effect
            # self._appts_needed = ss.norm.rvs(loc=self._base_appts_needed, scale=1)   # uncomment to use stochastic effect
            self._appts_needed = self._random_integer_round(self._base_appts_needed)  # uncomment to use stochastic integer rounding effect

    def get_s_val(self) -> int:
        return self._s_val

    def get_age(self, epoch: int) -> float:
        """Get the current age of the patient in terms of epochs.

        Args:
            epoch (int): current epoch.

        Returns:
            float: age of the patient in terms of epochs.
        """
        return self._age_at_ref + (epoch - self._ref_epoch)

    def check_age(self, epoch: int) -> bool:
        """Check if the patient is too old to have an appointment.

        Args:
            epoch (int): current epoch.

        Returns:
            bool: True if the patient is not too old, False otherwise.
        """
        return self.get_age(epoch) <= self._max_age

    def get_modality_prop(self) -> float:
        match self.n_appts:
            case 0:
                return 0
            case _:
                return self._n_face/self.n_appts

    def inc_appts_needed(self, inc: int = 0) -> None:
        # self._appts_needed = ss.norm.rvs(loc=self._base_appts_needed + inc, scale=1)  # uncomment to use stochastic effect
        self._appts_needed = self._random_integer_round(self._base_appts_needed + inc)    # uncomment to use integer rounding effect

    def add_appt(self, epoch: int, slot_time: float, modality: int = 1) -> float:
        """Incremement the number of appointments the patient has had

        Args:
            epoch (int): Current epoch
            slot_time (float): Amount of remaining time in the appointment slot.
            modality (int, optional): Modality of the appointment. Defaults to 1 (in-person). 0 is virtual.

        Returns:
            float: fraction of the appointment slot that was used.
        """
        # check if it is the first appt
        if self.n_appts == 0:
            self.assessment(epoch)
        if (self._appts_needed - self.n_appts) % 1 == 0:
            rem = min(1, slot_time)
            self.n_appts += rem
        else:
            rem = min(self._appts_needed - self.n_appts, slot_time)
            self.n_appts += rem
        # increment modality counter
        if modality == 1:
            self._n_face += rem
        return rem

    def check_appts(self) -> bool:
        """Check if the patient has had enough appointments.

        Returns:
            bool: True if the patient has had enough appointments, False otherwise.
        """
        return self.n_appts >= self._appts_needed

    def get_patient_data(self, epoch: int, age_out: bool = False, wlist_flush: bool = False) -> list:
        """Returns a summary of the client's service history.

        Args:
            epoch (int): epoch number at the time of the summary.
            age_out (bool, optional): True if the patient aged-out. 
                                      False if they were discharged for 
                                      acheiving adequate outcomes.
                                      np.nan if they were just flushed from the waitlist.
                                      Defaults to False.
            wlist_flush (bool, optional): True if the patient was flushed from the waitlist. 
                                          Defaults to False.

        Returns:
            list: patient data.
        """
        return [self._s_val,
                self._age_at_ref,
                self._ref_epoch,
                self._ax_epoch,
                self.n_appts,
                self.get_modality_prop(),
                epoch,
                age_out,
                wlist_flush]
