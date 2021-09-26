#ifndef BLOCK_H
#define BLOCK_H

// Define types hash and transaction
typedef int hash;
typedef char * transaction;

// Define struct type for block
typedef struct Block_T {
    hash previous_block_hash;
    hash block_hash;
    transaction transactions;
} block_t;

#endif
