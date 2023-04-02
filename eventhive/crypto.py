import hmac
import hashlib
import os
import base64 as b64
import json

from .external import aes


def _dict_to_json_bytes(message):
    return bytes(
        json.dumps(
            message,
            indent=0,
            sort_keys=True,
            separators=(
                ',',
                ':')),
        'utf8')


def sign(secret, message, algo='sha1'):
    tosign = _dict_to_json_bytes(message)
    return hmac.HMAC(secret, tosign, algo).hexdigest()


def verify(secret, message, signature, algo='sha1'):
    toverify = sign(secret, message)
    return hmac.compare_digest(toverify, signature)


def create_aes_obj(secret):
    key = create_aes_key(secret)
    return {"obj": aes.AES(key),
            "key": key}


def create_aes_key(secret):
    return hashlib.sha256(secret).digest()[:16]


def encrypt(secret, message, iv=None, base64=True, aes_obj=None):
    if secret is None:
        return message

    if aes_obj is None:
        aes_obj = create_aes_obj(secret)
    if iv is None:
        iv = os.urandom(16)

    data = _dict_to_json_bytes(message)
    ciphertext = aes_obj.encrypt_ctr(data, iv)

    if base64:
        return {
            "iv": str(
                b64.b64encode(iv), 'utf8'),
            "ciphertext": str(
                b64.b64encode(ciphertext), 'utf8')
        }

    return {"iv": iv, "ciphertext": ciphertext}


def decrypt(secret, ciphertext_dict, base64=True, aes_obj=None):
    if secret is None:
        return ciphertext_dict

    try:
        ciphertext = ciphertext_dict['ciphertext']
        iv = ciphertext_dict['iv']
    except KeyError as e:
        return ciphertext_dict

    if aes_obj is None:
        aes_obj = create_aes_obj(secret)

    if base64:
        ciphertext = b64.b64decode(ciphertext)
        iv = b64.b64decode(iv)

    plaintext = aes_obj.decrypt_ctr(ciphertext, iv)
    json_data = str(plaintext, 'utf8')
    message = json.loads(json_data)
    return message
