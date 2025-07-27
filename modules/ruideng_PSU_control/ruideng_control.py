import serial.tools.list_ports
from pymodbus.client import ModbusSerialClient

class RuidengControl:
    def __init__(self):
        self.device = None

        # Register addresses
        self.vset_port = 8
        self.iset_port = 9
        self.vout_port = 10
        self.iout_port = 11
        self.vin_port = 14
        self.power_port = 18
        self.temp_port = 5

        self.i_multiplier = 100  # Current multiplier for iout

    def list_com_ports(self) -> dict:
        """List available COM ports with descriptions."""
        ports = serial.tools.list_ports.comports()
        return {
            port.device: {
                'description': port.description,
                'hwid': port.hwid
            } for port in ports
        }

    def select_port(self, port: str) -> bool:
        """Connect to the RD6006 via the specified COM port."""
        self.close()
        try:
            self.device = ModbusSerialClient(port=port, baudrate=115200)
            return self.device.connect()
        except Exception:
            self.device = None
            return False

    def _read_registers(self, address: int, count: int = 1) -> list | None:
        """Read Modbus holding registers."""
        if self.device:
            result = self.device.read_holding_registers(address=address, count=count)
            if not result.isError():
                return result.registers
        return None

    def _write_register(self, address: int, value: int) -> bool:
        """Write a value to a single Modbus register."""
        if self.device:
            result = self.device.write_register(address=address, value=value)
            return not result.isError()
        return False

    def close(self) -> None:
        """Close the Modbus connection."""
        if self.device:
            self.device.close()
            self.device = None

    def check_status(self) -> dict | None:
        """Return a dict with voltage, current, power and temperature readings."""
        result = self._read_registers(0, 50)

        if result is None:
            return None
        
        if "6006" in str(result[0]):
            self.i_multiplier = 1000  # Adjust multiplier for RD6006
        elif "6012" in str(result[0]):
            self.i_multiplier = 100

        return {
            'vset': result[self.vset_port] / 100.0,
            'iset': result[self.iset_port] / self.i_multiplier,
            'vout': result[self.vout_port] / 100.0,
            'iout': result[self.iout_port] / self.i_multiplier,
            'vin': result[self.vin_port] / 100.0,
            'power': bool(result[self.power_port]),
            'temp': result[self.temp_port]
        }

    def set_voltage(self, voltage: float) -> None:
        """Set the target voltage."""
        self._write_register(self.vset_port, int(voltage * self.i_multiplier))

    def set_current(self, current: float) -> None:
        """Set the target current."""
        self._write_register(self.iset_port, int(current * self.i_multiplier))

    def set_power(self, power: bool) -> None:
        """Enable or disable the power output."""
        self._write_register(self.power_port, int(power))

ruidengcontrol = RuidengControl()