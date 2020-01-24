from pymodaq.daq_move.utility_classes import DAQ_Move_base  # base class
from pymodaq.daq_move.utility_classes import comon_parameters  # common set of parameters for all actuators
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict

class DAQ_Move_SR830(DAQ_Move_base):
    """
        Wrapper object to access SR830 as a scan parameter

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = 'Hz'
    is_multiaxes=True
    stage_names=[]



    ##finding VISA ressources
    from visa import ResourceManager
    VISA_rm = ResourceManager()
    devices = list(VISA_rm.list_resources())

    ##checking VISA ressources
    try:
        from visa import ResourceManager
        VISA_rm = ResourceManager()
        devices = list(VISA_rm.list_resources())
        device = ''
        for dev in devices:
            if 'GPIB' in dev:
                device = dev
                break


    except:
        devices = []

    time_constants={0:'10us',1:'30us',2:'100us',3:'300us',
                     4:'1ms',5:'3ms',6:'10ms',7:'30ms',
                     8:'100ms',9:'300ms',10:'1s',11:'3s',
                     12:'10s',13:'30s',14:'100s',15:'300s',
                     16:'1ks',17:'3ks',18:'10ks',19:'30ks'}

    print(time_constants)

    params= [#elements to be added in order to control your custom stage
            {'title': 'VISA:', 'name': 'VISA_ressources', 'type': 'list',
            'values': devices, 'value': device},
            {'title': 'Manufacturer:', 'name': 'manufacturer', 'type': 'str', 'value': ""},
            {'title': 'Serial number:', 'name': 'serial_number', 'type': 'str', 'value': ""},
            {'title': 'Model:', 'name': 'model', 'type': 'str' , 'value': ""},
            {'title': 'Master/Slave:', 'name': 'MasterSlave', 'type': 'list',
            'values' : ['Master','Slave'],'value': "Master",},
            {'title': 'Time Constant', 'name': 'TC', 'type': 'list',
             'values': ['1','2'], 'value': time_constants[7]}
            ]+comon_parameters

    def __init__(self,parent=None,params_state=None):
        """
            Initialize the the class

            ============== ================================================ ==========================================================================================
            **Parameters**  **Type**                                         **Description**

            *parent*        Caller object of this plugin                    see DAQ_Move_main.DAQ_Move_stage
            *params_state*  list of dicts                                   saved state of the plugins parameters list
            ============== ================================================ ==========================================================================================

        """

        super().__init__(parent,params_state)
        self.controller = None





    def check_position(self):
        """
            Get the current position from the hardware with scaling conversion.

            Returns
            -------
            float
                The position obtained after scaling conversion.

            See Also
            --------
            DAQ_Move_base.get_position_with_scaling, daq_utils.ThreadCommand
        """
        pos=self.inst.query('FREQ?')
        return pos


    def close(self):
      """
        not implemented.
      """
      pass


    def commit_settings(self,param):
        """
            | Activate any parameter changes on the PI_GCS2 hardware.
            |
            | Called after a param_tree_changed signal from DAQ_Move_main.

        """
        pass

    def ini_stage(self,controller=None):
        """
            Initialize the controller and stages (axes) with given parameters.

            ============== ================================================ ==========================================================================================
            **Parameters**  **Type**                                         **Description**

            *controller*    instance of the specific controller object       If defined this hardware will use it and will not initialize its own controller instance
            ============== ================================================ ==========================================================================================

            Returns
            -------
            Easydict
                dictionnary containing keys:
                 * *info* : string displaying various info
                 * *controller*: instance of the controller object in order to control other axes without the need to init the same controller twice
                 * *stage*: instance of the stage (axis or whatever) object
                 * *initialized*: boolean indicating if initialization has been done corretly

            See Also
            --------
             daq_utils.ThreadCommand
        """
        try:
            # initialize the stage and its controller status
            # controller is an object that may be passed to other instances of DAQ_Move_Mock in case
            # of one controller controlling multiaxes

            self.status.update(edict(info="",controller=None,initialized=False))


            #check whether this stage is controlled by a multiaxe controller (to be defined for each plugin)

            if self.settings.child(('MasterSlave')).value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller = controller
            else:
                self.controller = self.VISA_rm.open_resource(self.settings.child(('VISA_ressources')).value())

            # force correct read&wite termination
            self.controller.write_termination = '\n'
            self.controller.read_termination = '\n'

            self.controller.timeout = self.settings.child(('timeout')).value()
            idn = self.controller.query('OUTX1;*IDN?;')
            idn = idn.rstrip('\n')
            idn = idn.rsplit(',')
            if len(idn) >= 0:
                self.settings.child(('manufacturer')).setValue(idn[0])
            if len(idn) >= 1:
                self.settings.child(('model')).setValue(idn[1])
            if len(idn) >= 2:
                self.settings.child(('serial_number')).setValue(idn[2])


            self.status.initialized=True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[getLineInfo()+ str(e),'log']))
            self.status.info=getLineInfo()+ str(e)
            self.status.initialized=False
            return self.status


    def move_Abs(self,position):
        """
            Make the absolute move from the given position after thread command signal was received in DAQ_Move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            DAQ_Move_base.set_position_with_scaling, DAQ_Move_base.poll_moving

        """
        position=self.check_bound(position)
        self.set_freq(position)


    def move_Rel(self,position):
        """
            Make the relative move from the given position after thread command signal was received in DAQ_Move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            hardware.set_position_with_scaling, DAQ_Move_base.poll_moving

        """
        self.current_position=self.get_freq()
        position=self.check_bound(self.current_position+position)-self.current_position
        self.set_freq(position)



    def move_Home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """
        self.emit_status(ThreadCommand('Update_Status',['Move Home not implemented setting frequ to 1kHz']))
        set_freq(1000)

    def stop_motion(self):
      """
        Call the specific move_done function (depending on the hardware).

        See Also
        --------
        move_done
      """
      pass

    def get_freq(self):
        res=self.controller.query('FREQ?')
        #print('actual freqency is',res)
        try:
            res=float(res)
        except:
            res = 0
        return res

    def set_freq(self,freq):
        cmd='FREQ {:.4f}'.format(freq)
        print(self.controller.write(cmd))



if __name__=='__main__':
    from time import sleep
    lockin1=DAQ_Move_SR830()
    lockin1.ini_stage()
    sleep(10)
    print(lockin1.get_freq())
    print(lockin1.set_freq(1000))
    print(lockin1.get_freq())
    print(lockin1.params)