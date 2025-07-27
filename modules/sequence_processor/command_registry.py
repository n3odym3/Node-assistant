import re

command_registry = []

import re
import inspect

command_registry = []

import re
import inspect

command_registry = []

def register_command(pattern):
	def decorator(func):
		regex = re.compile(pattern)
		sig = inspect.signature(func)
		n_args = len(sig.parameters)

		if n_args == 1:
			def wrapper(cmd):
				match = regex.fullmatch(cmd)
				return func(cmd) if match else None
		elif n_args == 2:
			def wrapper(cmd):
				match = regex.fullmatch(cmd)
				return func(cmd, match) if match else None
		else:
			raise TypeError(f"Function '{func.__name__}' must take 1 or 2 parameters.")

		# Enregistrer la fonction encapsulée
		command_registry.append((regex, wrapper))
		return func
	return decorator

@register_command(r"(\d+)(ms|s|m|h)")
def cmd_delay(cmd, match):
	duration = int(match.group(1))
	unit = match.group(2)
	duration_s = {
		"ms": duration / 1000,
		"s": duration,
		"m": duration * 60,
		"h": duration * 3600,
	}[unit]
	
	return {
		"valid": True,
		"description": f"Wait {duration}{unit}",
		"duration": duration_s,
		"cmd": {
            "wait": duration_s
        }
	}

@register_command(r"volt(\d+(?:\.\d+)?)")
def cmd_voltage(cmd, match):
	volt = float(match.group(1))
	return {
		"valid": True,
		"description": f"Set PSU to {volt}V",
		"duration": 1,
		"cmd": {
			"volt" : volt
        }
	}

@register_command(r"amp(\d+(?:\.\d+)?)")
def cmd_current(cmd, match):
	amp = float(match.group(1))
	return {
		"valid": True,
		"description": f"Set PSU to {amp}A",
		"duration": 1,
		"cmd": {
			"amp" : amp
        }
	}

