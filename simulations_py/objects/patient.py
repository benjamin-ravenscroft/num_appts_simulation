class Patient():
    def __init__(self, s_val: int, age: float, epoch: int, appts_needed: int, max_age: float, wait_flag: bool = False):
        self._s_val = s_val
        self._age_at_ref = age
        self._ref_epoch = epoch
        self._ax_epoch = None   # initialize to None until (and only if) patient is assessed
        self.n_appts = 0
        self._appts_needed = appts_needed
        self._max_age = max_age
        self._wait_flag = wait_flag

    def assessment(self, epoch: int):
        """Set the epoch the patient was assessed at.

        Args:
            epoch (int): epoch assessment occured during
        """
        self._ax_epoch = epoch
        if self._wait_flag:
            wait_time = (epoch - self._ref_epoch)/52
            match self._s_val:
                case 1: self._appts_needed += 1.562 * wait_time
                case 2: self._appts_needed += 1.35 * wait_time
                case 3:
                    self._appts_needed += 0.05 * wait_time
                case _:
                    pass

    def get_age(self, epoch: int):
        """Get the current age of the patient in terms of epochs.

        Args:
            epoch (int): current epoch.

        Returns:
            float: age of the patient in terms of epochs.
        """
        return self._age_at_ref + (epoch - self._ref_epoch)
    
    def check_age(self, epoch: int):
        """Check if the patient is too old to have an appointment.

        Args:
            epoch (int): current epoch.

        Returns:
            bool: True if the patient is not too old, False otherwise.
        """
        return self.get_age(epoch) <= self._max_age
    
    def add_appt(self, epoch: int, slot_time: float):
        """Incremement the number of appointments the patient has had

        Args:
            epoch (int): Current epoch
            slot_time (float): Amount of remaining time in the appointment slot.

        Returns:
            float: fraction of the appointment slot that was used.
        """
        # check if it is the first appt
        if self.n_appts == 0:
            self.assessment(epoch)
        if (self._appts_needed - self.n_appts) % 1 == 0:
            rem = min(1, slot_time)
            self.n_appts += rem
            return rem
        else:
            rem = min(self._appts_needed - self.n_appts, slot_time)
            self.n_appts += rem
            return rem

    def check_appts(self):
        """Check if the patient has had enough appointments.

        Returns:
            bool: True if the patient has had enough appointments, False otherwise.
        """
        return self.n_appts >= self._appts_needed
    
    def get_patient_data(self, epoch: int, age_out: bool = False):
        return [self._s_val,
                self._age_at_ref,
                self._ref_epoch,
                self._ax_epoch,
                self.n_appts,
                epoch,
                age_out]


