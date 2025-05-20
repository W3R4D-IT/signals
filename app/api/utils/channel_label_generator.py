import string
import random


def generate_random_channel_label(length=10, prefix= "CH_")-> str:
    """
    Generates a random channel label.

    :param length: The length of the random part of the label.
    :param prefix: A prefix to prepend to the label.
    :return: A randomly generated channel label.
    """
    
    # Define characters to use: letters, digits
    characters = string.ascii_letters + string.digits
    random_part = ''.join(random.choices(characters, k=length))
    return f"{prefix}{random_part}"