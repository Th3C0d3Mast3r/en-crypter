from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


class AESUtils:
    def __init__(self, key: str, iv: str, mode: str = "cbc"):
        self.key = key.encode("utf-8")
        self.iv = iv.encode("utf-8")
        self.mode = mode.lower()

        self._validate()

    def _validate(self):
        if len(self.key) not in (16, 24, 32):
            raise ValueError(
                "AES key must be exactly 16, 24, or 32 bytes"
            )

        if len(self.iv) != 16:
            raise ValueError(
                "AES-CBC IV must be exactly 16 bytes"
            )

        if self.mode != "cbc":
            raise ValueError(
                f"Unsupported AES mode: {self.mode}. "
                "Currently only 'cbc' is supported."
            )

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext and return HEX encoded ciphertext.
        """

        # AES block size = 128 bits = 16 bytes
        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        padded_data = (
            padder.update(plaintext.encode("utf-8"))
            + padder.finalize()
        )

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(self.iv)
        )

        encryptor = cipher.encryptor()

        encrypted = (
            encryptor.update(padded_data)
            + encryptor.finalize()
        )

        # Return HEX
        return encrypted.hex()

    def decrypt(self, ciphertext_hex: str) -> str:
        """
        Decrypt HEX encoded ciphertext and return plaintext.
        """

        encrypted = bytes.fromhex(ciphertext_hex)

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(self.iv)
        )

        decryptor = cipher.decryptor()

        padded_data = (
            decryptor.update(encrypted)
            + decryptor.finalize()
        )

        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        plaintext = (
            unpadder.update(padded_data)
            + unpadder.finalize()
        )

        return plaintext.decode("utf-8")
