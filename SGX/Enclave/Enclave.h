#ifndef ENCLAVE_H
#define ENCLAVE_H

#include <stddef.h>  // Include size_t

#ifdef __cplusplus
extern "C" {
#endif

void ecall_set_key(const char *key, size_t len);
void ecall_rc4_encrypt(char *plaintext, size_t len); // Include this if implemented
void ecall_rc4_decrypt(char *ciphertext, size_t len);

#ifdef __cplusplus
}
#endif

#endif // ENCLAVE_H