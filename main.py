from openai import OpenAI
import os
import json
import time
import json


def show_json(obj):
    print(json.loads(obj.model_dump_json()))


function_json = {
    "name": "display_quiz",
    "description": "Displays a quiz to the student, and returns the student's response. A single quiz can have multiple questions.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "questions": {
                "type": "array",
                "description": "An array of questions, each with a title and potentially options (if multiple choice).",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_text": {"type": "string"},
                        "question_type": {
                            "type": "string",
                            "enum": ["MULTIPLE_CHOICE", "FREE_RESPONSE"],
                        },
                        "choices": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["question_text"],
                },
            },
        },
        "required": ["title", "questions"],
    },
}

# Create the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

# Create the assistant
assistant = client.beta.assistants.create(
    name="Recruiter_2",
    instructions="You are a big company recruiter. Answer questions briefly, in a sentence or less.",
    model="gpt-4-1106-preview",
        tools=[
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {"type": "function", "function": function_json},
    ],
)
show_json(assistant)

ASSISTANT_ID = assistant.id

# Create a thread
thread = client.beta.threads.create()
show_json(thread)

# Create a run
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
)
show_json(run)

# Submit a message
def submit_message(assistant_id, thread, user_message):
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )


def get_response(thread):
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")

# Pretty printing helper
def pretty_print(messages):
    print("# Messages")
    for m in messages:
        print(f"{m.role}: {m.content[0].text.value}")
    print()


# Waiting in a loop
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# Create a quiz
def create_thread_and_run(user_input):
    thread = client.beta.threads.create()
    run = submit_message(ASSISTANT_ID, thread, user_input)
    return thread, run

thread, run = create_thread_and_run(
    "Make a quiz with 2 questions: One open ended, one multiple choice. Then, give me feedback for the responses."
)
run = wait_on_run(run, thread)
run.status

show_json(run)

# Extract single tool call
tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
name = tool_call.function.name
arguments = json.loads(tool_call.function.arguments)

# Print the function name and arguments
print("Function Name:", name)
print("Function Arguments:")
arguments
print(arguments)