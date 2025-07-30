import base64
import json

from jnius import autoclass

from plyer.facades import Keystore
from plyer.platforms.android import activity


class AndroidKeystore(Keystore):
    def _set_key(self, servicename, key, value, **kwargs):
        cipher_text, iv = self.encrypt_value(value, servicename)

        value = json.dumps({
            'cipher': base64.b64encode(cipher_text).decode(),
            'iv': base64.b64encode(iv).decode()
        })

        mode = kwargs.get("mode", 0)
        settings = activity.getSharedPreferences(servicename, mode)
        editor = settings.edit()
        editor.putString(key, value)
        editor.commit()

    def _get_key(self, servicename, key, **kwargs):
        mode = kwargs.get("mode", 0)
        default = kwargs.get("default", "__None")

        settings = activity.getSharedPreferences(servicename, mode)
        ret = settings.getString(key, default)
        if ret == default:
            return None

        blob = json.loads(ret)
        return self.decrypt_value(servicename, blob)

    def encrypt_value(self, value, servicename):
        Cipher = autoclass('javax.crypto.Cipher')
        secret_key = self.get_secret_key(servicename)

        cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, secret_key)

        ciphertext = cipher.doFinal(value.encode("utf-8"))
        iv = cipher.getIV()
        return ciphertext, iv

    def decrypt_value(self, servicename, data):
        GCMParameterSpec = autoclass('javax.crypto.spec.GCMParameterSpec')
        Cipher = autoclass('javax.crypto.Cipher')
        String = autoclass('java.lang.String')

        secret_key = self.get_secret_key(servicename)
        cipher = Cipher.getInstance("AES/GCM/NoPadding")

        iv = base64.b64decode(data['iv'])
        ct = base64.b64decode(data['cipher'])

        spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, secret_key, spec)
        plaintext_bytes = cipher.doFinal(ct)
        return str(String(plaintext_bytes, "UTF-8"))

    @staticmethod
    def get_secret_key(servicename):
        KeyProperties = autoclass('android.security.keystore.KeyProperties')
        KeyGenerator = autoclass('javax.crypto.KeyGenerator')
        KeyGenParameterSpec = autoclass('android.security.keystore.KeyGenParameterSpec$Builder')
        KeyStore = autoclass('java.security.KeyStore')

        key_store = KeyStore.getInstance("AndroidKeyStore")
        key_store.load(None)

        if not key_store.containsAlias(servicename):
            builder = KeyGenParameterSpec(servicename,
                                        KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            builder.setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            builder.setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            key_gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
            key_gen.init(builder.build())
            key_gen.generateKey()

        return key_store.getKey(servicename, None)

def instance():
    return AndroidKeystore()
