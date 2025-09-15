# routing_agent.py
def route_ticket(ticket_id: str, topic: str) -> dict:
    """Route tickets that are outside the RAG scope."""

    # Topics RAG agent handles
    rag_topics = {"How-to", "Product", "Best practices", "API/SDK", "SSO"}

    if topic not in rag_topics:
        routing_message = (
            f"This ticket has been classified as a '{topic}' issue "
            f"and routed to the appropriate team."
        )
    else:
        routing_message = (
            f"This ticket belongs to RAG scope ('{topic}'), "
            f"so it will be answered by the RAG agent."
        )

    return {
        "ticket_id": ticket_id,
        "routing_message": routing_message
    }


# Quick test
if __name__ == "__main__":
    test_ticket1 = {"ticket_id": "TICKET-245", "topic": "Connector"}
    test_ticket2 = {"ticket_id": "TICKET-246", "topic": "Product"}

    print(route_ticket(**test_ticket1))
    print(route_ticket(**test_ticket2))
