import logging


class Logger:
    def __init__(self, name, level='WARNING'):
        # Save the arguments
        self.name = name

        # Initialize the level
        self._init_level(level)

        # Initialize the logger
        self._init_logger()

    def debug(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the debugging message
        self.logger.debug(flattened_message)

        # Return the flattened message
        return flattened_message

    def info(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the info
        self.logger.info(flattened_message)

        # Return the flattened message
        return flattened_message

    def warning(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the warning
        self.logger.warning(flattened_message)

        # Return the flattened message
        return flattened_message

    def error(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the error
        self.logger.error(flattened_message)

        # Return the flattened message
        return flattened_message

    def exception(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the exception
        self.logger.exception(flattened_message)

        # Return the flattened message
        return flattened_message

    def _init_level(self, level):
        # Create a mapping from string to predefined logging level
        mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.error,
            'CRITICAL': logging.CRITICAL,
        }

        # Set the logging level by mapping the string to the level
        self.logging_level = mapping[level]

    def _init_logger(self):
        # Get the logger and save
        self.logger = logging.getLogger(self.name)

        # Set the logging level
        self.logger.setLevel(self.logging_level)

        # Create a stream handler
        ch = logging.StreamHandler()

        # Create the formatter
        formatter = logging.Formatter(
            '%(asctime)-15s %(name)-8s %(levelname)-8s %(message)s')

        # Set the formatter of the stream handler
        ch.setFormatter(formatter)

        # Add the handlers to the logger
        self.logger.addHandler(ch)

    def _flatten_messages(self, messages):
        # Check the messages type
        if isinstance(messages, list):
            # Concatenate all messages and return
            return '\n'.join(messages)
        elif isinstance(messages, str):
            # Return the message
            return messages
        else:
            raise ValueError(
                'Unknown messages type "{}"'.format(type(messages)))
