#include <stdio.h>
#include <search.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "block.h"
#include "linked_list.h"


// Init external function from hash.c
extern hash string_hash(void *string);

// Init number of total votes to add to the blockchain
int NUM_VOTES = 10;

// Define enum for the party code
typedef enum party_code_t {
    GOOD_PARTY, MEDIOCRE_PARTY, EVIL_PARTY, MAX_PARTIES
} party_code;
// Define array of party names
char * party_name[MAX_PARTIES] = {"GOOD PARTY", "MEDIOCRE PARTY", "EVIL PARTY"};

// Picks a random party
static party_code get_vote()
{
    int r = rand();
    return r % MAX_PARTIES;
}


int main() 
{
    // Set the seed
    srand(time(NULL));

    // Init head node and data
    NODE *head;
    DATA genesis_element;

    // Init blockchain
    init(&head);

    /* Create first block */
    // Create first transaction by randomly picking a vote
    transaction genesis_transactions = {party_name[get_vote()]};
    // Create first block
    block_t genesis_block = {
        0,                                  // Previous block hash
        string_hash(genesis_transactions),  // Hash and store transaction (it's the current block hash)
        genesis_transactions                // Store data (i.e. the vote)
    };
    // Update node's data with the block
    genesis_element.info = genesis_block;
    // Add the just create block to the blockchain
    head = add(head, genesis_element);

    /* Submit n random votes to the blockchain */
    // Get previous hash
    int previous_hash = genesis_element.info.previous_block_hash;
    // Init transaction list
    transaction transactions_list = (transaction) malloc(NUM_VOTES * sizeof(char)*10);
    
    for (int i = 0; i < NUM_VOTES; i++) {
        // Init data and block
        DATA * el = malloc(sizeof(DATA));
        block_t * b = malloc(sizeof(block_t));

        // Create new transaction
        transaction t = {party_name[get_vote()]};
        // Concatenate new transaction to list of transactions
        strcat(transactions_list, t);
        // Update current block parameters
        b->previous_block_hash = previous_hash;
        b->block_hash = string_hash(transactions_list);
        b->transactions = t;
        // Update node's data with the block
        el->info = *b;
        // Update previous_hash variable with hash of just created block
        previous_hash = b->block_hash;
        // Add new node to blockchain
        head = add(head, *el);
    }

    print_list(head);
}
