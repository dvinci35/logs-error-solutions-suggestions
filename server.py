from starlette.applications import Starlette
from starlette.responses import StreamingResponse
from starlette.routing import Route
from transformers import (
    TextIteratorStreamer,
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    BitsAndBytesConfig,
)
import asyncio
from pathlib import Path
from threading import Thread

import yaml, json
import requests

# The configuration file's path must be provided in the docker file.
# from os import environ
# CONFIG_FILE_PATH = environ.get("CONFIG_FILE_PATH")
CONFIG_FILE_PATH = "./server_config.yaml"


# Load the configurations by reading the config yaml file
def read_config(file_path: str) -> dict:
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)
    return config


# Complete the chat incomming from the client and put it into async queue
async def chat_completion(request):
    # Load the payload
    payload = await request.body()
    payload = json.loads(payload)
    input_messages = payload["input_messages"]
    generation_params = payload["generation_params"]

    # Create the response queue
    response_q = asyncio.Queue()

    # Put the input string, response queue and the generation parameters the input model queue
    # The generation parameters would be for only this input string and every client will give their
    # own generation parameters
    # Then wait for the response
    await request.app.model_queue.put((input_messages, response_q, generation_params))

    async def word_streamer():
        streamer = await response_q.get()
        generated_text = ""
        for word in streamer:
            generated_text += word
            sending_payload = json.dumps(
                dict(new_word=word, full_response=generated_text)
            )
            yield sending_payload

    return StreamingResponse(word_streamer())


# Create a Starlette app
app = Starlette(
    routes=[
        Route("/chat_completion", chat_completion, methods=["POST"]),
    ],
)


# An async task that will keep running infinitely to generate response as soon as
# it recieves the request.
async def server_loop(the_input_queue, config):
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,  # Enables 4-bit quantization
        bnb_4bit_quant_type="nf4",  #  NF4 (NormalFloat4) is generally recommended
        bnb_4bit_use_double_quant=True,  # Helps with accuracy (especially for larger models)
    )

    # LOAD THE MODELS REQUIRED
    chat_completion_model = AutoModelForCausalLM.from_pretrained(
        **config["chat_completion_model_params"],
        quantization_config=quantization_config,
    )
    chat_model_tokenizer = AutoTokenizer.from_pretrained(
        config["chat_completion_model_params"]["pretrained_model_name_or_path"],
        token=config["chat_completion_model_params"]["token"],
    )

    streamer = TextIteratorStreamer(
        chat_model_tokenizer,
        **config["streamer_params"],
    )

    chat_completion_pipeline = pipeline(
        "text-generation",
        model=chat_completion_model,
        tokenizer=chat_model_tokenizer,
    )

    log_explanation_prompt = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": config["log_explanation_prompt"]},
    ]

    # The infinite loop to generate response.
    while True:
        # input_messages is the string of logs.
        (input_messages, response_q, generation_params) = await the_input_queue.get()

        log_extraction_conv = [
            {"role": "system", "content": "You are a helpful assistant"},
            {
                "role": "user",
                "content": config[
                    "log_extraction_prompt".format(input_logs=input_messages)
                ],
            },
        ]
        extracted_logs = chat_completion_pipeline(
            text_inputs=log_extraction_conv,
            max_new_tokens=4096,
            return_full_text=False,
        )[0]["generated_text"]

        log_explanation_prompt = [
            {"role": "system", "content": "You are a helpful assistant"},
            {
                "role": "user",
                "content": config["log_explanation_prompt"].format(
                    input_logs=extracted_logs
                ),
            },
        ]

        trd = Thread(
            target=chat_completion_pipeline,
            kwargs=dict(
                text_inputs=log_explanation_prompt,
                streamer=streamer,
                **generation_params,
            ),
        )
        trd.start()

        await response_q.put((streamer))


# Create an event that will run on startup and
@app.on_event("startup")
async def startup_event():
    input_queue = asyncio.Queue()

    app.model_queue = input_queue
    config = read_config(Path(CONFIG_FILE_PATH))
    asyncio.create_task(server_loop(the_input_queue=input_queue, config=config))
