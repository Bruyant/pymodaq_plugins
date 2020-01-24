"""
.. module:: VisaInstrument
   :platform: Unix, Windows, mac
   :synopsis: A useful module indeed.

.. moduleauthor:: Nicolas Bruyant <nicolas.bruyant@lncmi.cnrs.fr>


"""

# TODO ceate a base class for visa instruments

from visa import ResourceManager


class VisaInstrumentClass:
    """
        ==================== ========================
        **Attributes**        **Type**
        *data_grabed_signal*  instance of pyqtSignal
        *VISA_rm*             ResourceManager
        *device*              First matching device found
        *params*              dictionnary list
        **private methods**
        *settings*
        ==================== ========================
    """
    print("class loaded")
    devices = []
    device = ''

    @classmethod
    def GetVisaResourcesList(cls, pattern='GPIB'):
        """Class method to update available resources from VISA controller

        Args:

        pattern (str) : optional matching string for instrument connection name 'GPIB' by default

        """

        try:
            cls.VISA_rm = ResourceManager()  # checking VISA resources
            cls.devices = list(cls.VISA_rm.list_resources())
            cls.device = 'toto'
            for dev in cls.devices:
                # matching pattern
                if pattern in dev:
                    cls.device = dev
                    break

        except Exception as e:
            cls.VISA_rm.close()
            raise e

#VisaInstrumentClass.GetVisaRessourceslist(pattern='GPIB')



if __name__ == '__main__':
    import VisaInstrument as module
    print("after loading",module.VisaInstrumentClass.device)
    module.VisaInstrumentClass.GetVisaResourcesList()
    print("after update", module.VisaInstrumentClass.device)
    instr = module.VisaInstrumentClass.VISA_rm.get_instrument(module.VisaInstrumentClass.device)
    # print instrument idn string
    print(instr.query('*IDN?'))
