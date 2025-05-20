import base64

class SignalEncryption:
    @staticmethod
    def decrypt(ciphertext: str, key: str):
        """
        Decrypts a Base64 string encrypted using the Pine Script encryption method.

        Args:
            ciphertext (str): The encrypted Base64 string.
            key (str): The encryption key used during encryption.

        Returns:
            str: The decrypted original message.
        """
        assert key, "Key must not be empty"
        assert ciphertext, "Encrypted string must not be empty"
        
        base64_alphabet = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        )
        decrypted_base64 = ""
        key_length = len(key)

        ciphertext = base64.b64decode(ciphertext).decode()

        for i, char in enumerate(ciphertext):
            if char == "=":
                decrypted_base64 += "="  # Preserve padding
                continue

            # Find the index of the character in the Base64 alphabet
            idx = base64_alphabet.find(char)
            if idx == -1:
                raise ValueError(f"Invalid Base64 character: {char}")

            # Calculate the shift dynamically using the key
            key_char = key[i % key_length] if key_length > 0 else ""
            shift = ord(key_char) % 64 if key_char else 0

            # Reverse the shift to get the original Base64 character index
            original_idx = (idx - shift) % 64
            decrypted_base64 += base64_alphabet[original_idx]

        # Decode the Base64 string to get the original message
        try:
            # Add padding if necessary
            padding_length = len(decrypted_base64) % 4
            if padding_length:
                decrypted_base64 += "=" * (4 - padding_length)

            original_message = base64.b64decode(decrypted_base64).decode("utf-8")
            return original_message
        except Exception as e:
            raise ValueError(f"Failed to decode ciphertext: {e}")
