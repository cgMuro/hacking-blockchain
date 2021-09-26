#include <stdio.h>
#include <stdlib.h>
#include "linked_list.h"


// Reverse the linked list
NODE* reverse(NODE * node) 
{
    NODE * temp;
    NODE * previous = NULL;

    while (node != NULL) {
        temp = node->next;
        node->next = previous;
        previous = node;
        node = temp;
    }
    return previous;
}

// Inits a new linked list given a heading node
void init(NODE ** head)
{
    *head = NULL;
}

// Appends a new node to the liked list
NODE * add(NODE * node, DATA data)
{
    NODE * temp = (NODE*) malloc(sizeof(NODE));
    // Check if there is memory available
    if (temp == NULL) {
        exit(0);
    }

    temp->data = data;
    temp->next = node;
    node = temp;
    return node;
}

// Prints the entire linked list
void print_list(NODE * head)
{
    head = reverse(head);
    NODE * temp;
    int indent = 0;
    printf("Print chain\n");
    printf("=======\n");
    for (temp = head; temp; temp = temp->next, indent = indent + 2) {
        printf("%*sPrevious hash\t%d\n", indent,"", temp->data.info.previous_block_hash);
        printf("%*sBlock hash\t%d\n", indent,"", temp->data.info.block_hash);
        printf("%*sTransaction\t%s\n", indent,"", temp->data.info.transactions);
        printf("%*s\n", indent, "");
    }
    printf("\r\n");
}

// Add new node after given node
void add_at(NODE * node, DATA data)
{
    NODE * temp = (NODE*) malloc(sizeof(NODE));
    // Check if there is memory available
    if (temp == NULL) {
        exit(EXIT_FAILURE);
    }
    temp->data = data;
    temp->next = node->next;
    node->next = temp;
}

// Remove node first node after head
void remove_node(NODE * head)
{
    NODE * temp = (NODE*) malloc(sizeof(NODE));
    // Check if there is memory available
    if (temp == NULL) {
        exit(EXIT_FAILURE);
    }
    temp = head->next;
    head->next = head->next->next;
    free(temp);
}

// Remove all node from list
NODE * free_list(NODE * head)
{
    NODE * tmpPtr = head;
    NODE * followPtr;
    while (tmpPtr != NULL) {
        followPtr = tmpPtr;
        tmpPtr = tmpPtr->next;
        free(followPtr);
    }
    return NULL;
}
