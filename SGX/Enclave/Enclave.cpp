#include "Enclave.h"
#include "Enclave_t.h"
#include <string.h>
#include <stdlib.h>


/*We obtain the init and the crypt from public repositories*/

// RC4 Generate SBox
void rc4_init(unsigned char *s, const unsigned char *key, size_t key_len)
{
    int i, j = 0;
    unsigned char k[256];
    unsigned char tmp;

    for (i = 0; i < 256; i++)
    {
        s[i] = (unsigned char)i;
        k[i] = key[i % key_len];
    }

    for (i = 0; i < 256; i++)
    {
        j = (j + s[i] + k[i]) % 256;
        tmp = s[i];
        s[i] = s[j];
        s[j] = tmp;
    }
}

// RC4 Generate Keystream and apply XOR for encryption/decryption
void rc4_crypt(unsigned char *s, unsigned char *data, size_t len, unsigned char *keystream)
{
    int i = 0, j = 0;
    size_t k;
    unsigned char tmp;

    for (k = 0; k < len; k++)
    {
        i = (i + 1) % 256;
        j = (j + s[i]) % 256;
        tmp = s[i];
        s[i] = s[j];
        s[j] = tmp;
        unsigned char ks_byte = s[(s[i] + s[j]) % 256];
        if (keystream != NULL)
        {
            keystream[k] = ks_byte;
        }
        data[k] ^= ks_byte;
    }
}

/*We create the global variable such that it can be used within the module*/

// Global variables for RC4
unsigned char global_key[256];
size_t global_key_len;
unsigned char s[256]; // S-box

/*We define the implementation of the interface function below. These functions
call the needed trusted and untrusted defined in the EDL, else they would
implement the code needed for the Enclave*/

extern "C" void ecall_set_key(const char *key, size_t len)
{
    if (len > 256)
        len = 256;
    memcpy(global_key, key, len);
    global_key_len = len;
}

extern "C" void ecall_rc4_sbox_init()
{
    rc4_init(s, global_key, global_key_len);
}

extern "C" void ecall_rc4_generate_keystream(size_t length)
{
    unsigned char s_local[256];
    memcpy(s_local, s, 256); // Use a local copy of S-box for keystream generation

    unsigned char data[256] = {0};
    unsigned char keystream[256]; // Local keystream buffer

    rc4_crypt(s_local, data, length, keystream);
    ocall_print_result((char *)keystream, length);
}

extern "C" void ecall_rc4_decrypt(char *ciphertext, size_t len)
{
    unsigned char s_local[256];
    memcpy(s_local, s, 256); // Use a local copy of S-box for decryption

    rc4_crypt(s_local, (unsigned char *)ciphertext, len, NULL);
    ocall_print_result(ciphertext, len);
}
