"""Utility functions"""


def menu(prompt, items):
	"""Constructs and shows a simple commandline menu.
	Returns an index of the provided items sequence."""
	for i in range(len(items)):
		print(str(i + 1) + ": " + items[i])
	result = None
	while True:
		result = input(prompt)
		try:
			result = int(result)
		except ValueError:
			print("error: Input must be a number. Please try again.")
			continue
		if result - 1 >= len(items) or result < 1:
			print("error: Provided option not in range. Please try again.")
			continue
		return result - 1


def preserve_tracebacks(func):
	"""Calls a command function, intersepting and returning exceptions (as str) if they occur"""

	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Exception as exc:
			return str(exc)

	return wrapper


def to_bool(s):
	if s == "on" or s.startswith("y") or s in ("yes", "1", "true"):
		return True
	return False


def is_track(uri):
	"""Returns True if the specified URI points to a spotify track."""
	return uri.startswith("spotify:track:") or uri.startswith(
		"https://open.spotify.com/track/"
	)
