from datetime import datetime
from zenpy import Zenpy
from python_graphql_client import GraphqlClient
from tinydb import TinyDB, Query
from dotenv import dotenv_values

config = dotenv_values(".env")

db = TinyDB('db.json')
Ticket = Query()

headers = { "Authorization":  config["LINEAR_API_KEY"]}
client = GraphqlClient(endpoint="https://api.linear.app/graphql", headers=headers)

# Create a Zenpy instance
credentials = {
  "subdomain": config["ZENDESK_SUBDOMAIN"],
  "token": config["ZENDESK_API_TOKEN"],
  "email": config["ZENDESK_EMAIL"]
}

zenpy_client = Zenpy(**credentials)
base_ticket_url = f"https://{config["ZENDESK_SUBDOMAIN"]}.zendesk.com/tickets/"

def compare_timestamp_strings(timestamp_str_1, timestamp_str_2):
    timestamp_1 = datetime.fromisoformat(timestamp_str_1)
    timestamp_2 = datetime.fromisoformat(timestamp_str_2)
    # was updated
    if timestamp_1 < timestamp_2:
        return True
    return False

def compare_timestamps(timestamp_1, timestamp_2):
    # was updated
    if timestamp_1 < timestamp_2:
        return True
    return False

# Perform a simple search
for ticket in zenpy_client.search(type='ticket', assignee=config["ZENDESK_ASSIGNEE_NAME"]):
    if config["ALWAYS_WRITE_RESPONSE"] == "true":
        write_response = True
    else:
        write_response = False
    if ticket.status != "solved" and ticket.status != "closed":
        ticket_url = f"{base_ticket_url}{ticket.id}"
        query = f"{{ attachmentsForURL(url: \"{ticket_url}\") {{ nodes {{ id issue {{ id identifier title updatedAt priorityLabel state {{ name }} }} }} }} }}"

        data = client.execute(query=query)
        linked_linear_tickets = []
        for node in data['data']['attachmentsForURL']['nodes']:
            issue = node['issue']
            linked_linear_tickets.append({
                "linear_ticket_id": issue['identifier'],
                "linear_ticket_status": issue['state']['name'],
                "linear_last_updated": issue['updatedAt'],
                "linear_ticket_title": issue['title'],
                "linear_ticket_priority": issue['priorityLabel']
            })

        zendesk_ticket = {
            "zendesk_ticket_id": ticket.id, 
            "zendesk_ticket_status": ticket.status,
            "zendesk_last_updated": ticket.updated_at,
            "zendesk_ticket_title": ticket.subject,
            "linked_linear_tickets": linked_linear_tickets
        }
        stored_zendesk_ticket = db.search(Ticket.zendesk_ticket_id == ticket.id)
        if len(stored_zendesk_ticket) == 0:
            db.insert(zendesk_ticket)
            write_response = True
        elif len(stored_zendesk_ticket) > 1:
            print(f"Multiple DB rows found for Zendesk #{ticket.id}, please investigate. Skipping for now...")
            continue
        else:
            stored_zendesk_ticket = stored_zendesk_ticket[0]
            zendesk_was_updated = compare_timestamp_strings(
                stored_zendesk_ticket["zendesk_last_updated"], 
                zendesk_ticket["zendesk_last_updated"]
            )

            try:
                stored_linear_tickets_timestamps = [datetime.fromisoformat(stored_linear_ticket['linear_last_updated']) for stored_linear_ticket in stored_zendesk_ticket["linked_linear_tickets"]]
                stored_linear_tickets_timestamps_latest = max(stored_linear_tickets_timestamps)
                linear_tickets_timestamps = [datetime.fromisoformat(linear_ticket['linear_last_updated']) for linear_ticket in zendesk_ticket["linked_linear_tickets"]]
                linear_tickets_timestamps_latest = max(linear_tickets_timestamps)
                
                linear_was_updated = compare_timestamps(
                    stored_linear_tickets_timestamps_latest,
                    linear_tickets_timestamps_latest
                )
            # handle case where there are no linked linear tickets
            except ValueError:
                linear_was_updated = False

            if linear_was_updated:
                print("Linear was updated, will write response")
                write_response = True

            if zendesk_was_updated:
                print("Zendesk was updated, will write response")
                write_response = True
                
            db.update(zendesk_ticket, Ticket.zendesk_ticket_id == ticket.id)

        # now do some creative writing!
        if write_response:
            # TODO: handle >1 Linear ticket
            if len(zendesk_ticket["linked_linear_tickets"]) == 1:
                linear_ticket = zendesk_ticket["linked_linear_tickets"][0]
                cleaned_up_title = linear_ticket["linear_ticket_title"].split("]")[-1].strip()
                cleaned_up_status = linear_ticket["linear_ticket_status"].lower()
                cleaned_up_priority = linear_ticket["linear_ticket_priority"].lower()
                ending_line = "I'll be in touch with updates as soon as I have them."
                # actually clean up the title and status
                if cleaned_up_title[-1] == ".":
                    cleaned_up_title = cleaned_up_title[:-1]
                if cleaned_up_status == "triage":
                    cleaned_up_status = "being prioritized"
                elif cleaned_up_status == "backlog":
                    cleaned_up_status = f"in the backlog as a {cleaned_up_priority} priority"
                    ending_line = f"While I don't have a timeline right now for when this work will be picked up, {ending_line}"
                elif cleaned_up_status == "in progress" or cleaned_up_status == "in review":
                    ending_line = f"I'll let you know as soon as it's ready to test."
                elif cleaned_up_status == "done":
                    ending_line = "Please test it out and let me know if it's working as expected."

                print(f"Hi all, the ticket for this work ({cleaned_up_title}) is currently {cleaned_up_status}. {ending_line}")

