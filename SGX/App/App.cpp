#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include "sgx_urts.h"
#include "App.h"
#include "Enclave_u.h"

#define ENCLAVE_FILENAME "enclave.signed.so"

sgx_enclave_id_t global_eid = 0;

void ocall_print_result(char *buf, size_t len)
{
    printf("Result: ");
    for (size_t i = 0; i < len; ++i)
        printf("%02X ", (unsigned char)buf[i]);
    printf("\n");
}

int initialize_enclave(void)
{
    sgx_status_t ret = SGX_ERROR_UNEXPECTED;
    ret = sgx_create_enclave(ENCLAVE_FILENAME, SGX_DEBUG_FLAG, NULL, NULL, &global_eid, NULL);
    if (ret != SGX_SUCCESS)
    {
        printf("Failed to create enclave, ret code: %d\n", ret);
        return -1;
    }
    return 0;
}

void hex_to_bytes(const char *hex, unsigned char *bytes, size_t len)
{
    for (size_t i = 0; i < len; i++)
    {
        sscanf(&hex[2 * i], "%2hhx", &bytes[i]);
    }
}

int main(int argc, char *argv[])
{
    (void)(argc);
    (void)(argv);

    if (initialize_enclave() < 0)
    {
        printf("Enter a character before exit ...\n");
        getchar();
        return -1;
    }

    // Set the encryption key
    char key[] = "gosecgosec";
    ecall_set_key(global_eid, key, sizeof(key) - 1); // Exclude the null terminator

    // Initialize the S-box
    ecall_rc4_sbox_init(global_eid);

    // Generate and print the keystream
    printf("Generated Keystream: ");
    ecall_rc4_generate_keystream(global_eid, 19);

    // Prompt user for the ciphertext
    char hex_ciphertext[512];
    printf("Enter the ciphertext (hex format): ");
    fgets(hex_ciphertext, sizeof(hex_ciphertext), stdin);

    // Remove the newline character if present
    size_t len = strlen(hex_ciphertext);
    if (hex_ciphertext[len - 1] == '\n')
    {
        hex_ciphertext[len - 1] = '\0';
        len--;
    }

    // Convert hex string to byte array
    size_t ciphertext_len = len / 2;
    unsigned char *byte_ciphertext = (unsigned char *)malloc(ciphertext_len);
    hex_to_bytes(hex_ciphertext, byte_ciphertext, ciphertext_len);

    // Print the input ciphertext in bytes
    printf("Ciphertext: ");
    for (size_t i = 0; i < ciphertext_len; ++i)
        printf("%02X ", byte_ciphertext[i]);
    printf("\n");

    // Decrypt the ciphertext
    ecall_rc4_decrypt(global_eid, (char *)byte_ciphertext, ciphertext_len);

    // Clean up
    free(byte_ciphertext);

    // Destroy the enclave
    sgx_destroy_enclave(global_eid);
    printf("Info: SampleEnclave successfully returned.\n");
    printf("Enter a character before exit ...\n");
    getchar();
    return 0;
}
