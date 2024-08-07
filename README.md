# README

## Goal
Automate writing responses to Zendesk tickets based on the status of linked Linear tickets.

⚠️ This script does NOT reply to the Zendesk ticket with the responses it writes. (That seems dangerous, eh?) This allows the user to review and customize the responses before sending.

Sample responses:

> Hi all, the ticket for this work (TICKET_TITLE_REDACTED) is currently in the backlog. While I don't have a timeline right now for when this work will be complete, I'll be in touch with updates as soon as I have them.

> Hi all, the ticket for this work (TICKET_TITLE_REDACTED) is currently in progress. I'll let you know as soon as it's ready to test.

> Hi all, the ticket for this work (TICKET_TITLE_REDACTED) is currently in review. I'll let you know as soon as it's ready to test.

### Business Logic
* Every day (cron job), go through all open Zendesk tickets assigned to me
* For each ticket
    * Check all associated Linear issues
    * If Linear issue has changes (customer should get an update) OR Zendesk ticket has changes (customer asked for an update)
        * Write a quick response indicating the current Linear status
        * Print out the message for each ticket needing an update

## Set Up

Requirements:

* Python 3
* A Linear personal API key
* A Zendesk API key

Install:

1. Copy `.env.example` to `.env` and fill out the values.
1. `pip install -r requirements.txt`

Run:

`python respond_to_zendesks.py`