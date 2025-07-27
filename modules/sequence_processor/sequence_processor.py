
from modules.sequence_processor.command_registry import command_registry
import re
class Sequence_Processor():
	def __init__(self):
		self.sequence = ""

	def _split_sequence(self, sequence: str) -> list:
		"""Split the sequence into individual commands."""
		return sequence.replace('\n', '').strip().split(',')
	
	def _expand_groups(self,sequence: str) -> str:
		"""
		Recursively expands a sequence with nested parentheses.

		Args:
			sequence (str): The input sequence containing patterns like 2(10s,2(T100)).

		Returns:
			str: The expanded sequence.
		"""
		# Regex to find the innermost pattern of the form N(...), where N is a number
		pattern = re.compile(r'(\d+)\(([^()]+)\)')
		
		# While there are still expandable patterns in the sequence
		while (match := pattern.search(sequence)):
			# Extract the multiplier and the content inside the parentheses
			multiplier = int(match.group(1))
			content = match.group(2)
			
			# Expand the content by repeating it 'multiplier' times
			expanded_content = ','.join([content] * multiplier)
			
			# Replace the current match with the expanded content
			sequence = sequence[:match.start()] + expanded_content + sequence[match.end():]

		return sequence
	
	def get_commands(self, sequence:str="") -> list:
		return self._split_sequence(self._expand_groups(sequence))

	def trad_cmd(self,cmd: str) -> dict:
		cmd = cmd.lower()
		for regex, func in command_registry:
			result = func(cmd)
			if result:
				return result

		return {
			"valid": False,
			"description": "Unknown command",
			"duration": 0,
			"error": "unknown"
		}
sequence_processor = Sequence_Processor()