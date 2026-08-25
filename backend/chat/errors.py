class ToolError(Exception):
    """
    Raised when a tool cannot answer as asked (unknown course, unwritable schedule).
    The message is returned to the model as an errored tool result so it can recover,
    so it should read as an explanation, not a stack trace.
    """
