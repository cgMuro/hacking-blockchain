#ifndef LINKEDLIST_H
#define LINKEDLIST_H

#include <stdio.h>
#include <stdlib.h>
#include "block.h"


// Define struct type for data
typedef struct {
    block_t info;
} DATA;
// Define struct type for node
typedef struct node {
    DATA data;
    struct node* next;
} NODE;


// LINKED LIST MAIN FUNCTIONS //

// Inits a new linked list given a heading node
void init(NODE ** head);

// Appends a new node to the liked list
NODE * add(NODE * node, DATA data);

// Add new node after given node
void add_at(NODE * node, DATA data);

// Prints the entire linked list
void print_list(NODE * head);

// Reverse the linked list
NODE * reverse(NODE * node);

// Get a list of all transactions in the linked list
void get_list_transactions(NODE* head, unsigned char *list_transactions);

// Remove node first node after head
void remove_node(NODE * head);

// Remove all node from list
NODE * free_list(NODE * head);

#endif
