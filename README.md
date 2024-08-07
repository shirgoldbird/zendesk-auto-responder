# README

## Goal
Automate responding to Zendesk tickets based on the status of the Linear tickets linked to them.

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
            * If status is ANYTHING but done,
                * "Hi, the ticket for this work ([TICKET TITLE]) is currently [STATUS]. I'll be in touch with updates as soon as I have them."
            * If status is done
                * "Hi, happy to let you know this work ([TICKET TITLE]) is finished and should be available for you to test. Could you please give it a try and let me know how it works?
    * Print out the pre-written message for each tick

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