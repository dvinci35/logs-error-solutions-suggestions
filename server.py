from starlette.applications import Starlette
from starlette.responses import StreamingResponse, JSONResponse
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

from typing import Dict
import yaml, json
from json import JSONDecodeError


def read_config(file_path: str) -> Dict:
    """Loads configuration from a YAML file.

    Args:
        file_path: The path to the YAML configuration file.

    Returns:
        A dictionary containing the loaded configuration.
        Returns an empty dictionary if the file is not found or if there's an error during parsing.

    Raises:
        yaml.YAMLError: If there's an error parsing the YAML file.  
                      The original exception is re-raised after printing an error message.
    """
    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise  # Re-raise the YAMLError after printing the message
    except Exception as e:
        raise


# Complete the chat incomming from the client and put it into async queue
async def chat_completion(request):
    """
    Handles incoming chat completion requests from clients.

    This function receives a request containing input messages and generation parameters,
    places them in a queue for processing by the language model, and streams the generated
    text back to the client word by word.

    Args:
        request: The incoming request object.

    Returns:
        A StreamingResponse that yields chunks of the generated text.
    """
    try:
        # Load the payload
        payload = await request.body()
        payload = json.loads(payload)

        input_messages = payload["input_messages"] # Extract input logs
        generation_params = payload["generation_params"] # Extract generation parameters

        # 2. Create a response queue for this specific request
        response_q = asyncio.Queue()

        # 3. Enqueue the request for processing by the language model
        #    The queue contains:
        #       - input_messages: The messages to be processed.
        #       - response_q: The queue where the model will put the generated text stream.
        #       - generation_params: Parameters for text generation (e.g., max_tokens, temperature).
        await request.app.model_queue.put((input_messages, response_q, generation_params))

        # 4. Define an asynchronous generator for streaming the response
        async def word_streamer():
            """
            Asynchronously streams the generated text word by word.

            This inner function retrieves the generated text stream from the response queue
            and yields JSON payloads containing the new word and the complete generated text so far.
            """
            streamer = await response_q.get() # Wait for the model to put the streamer in the queue
            generated_text = ""
            for word in streamer:
                generated_text += word
                sending_payload = json.dumps( # Create JSON payload for each word
                    dict(new_word=word, full_response=generated_text)
                )
                yield sending_payload # Yield the payload to the client

        # 5. Return a StreamingResponse to handle the asynchronous generator
        return StreamingResponse(word_streamer())
    
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON payload"}, status_code=400)
    
    except Exception as e:  # Catch any other exceptions
        return JSONResponse({"error": str(e)}, status_code=500)




# Create a Starlette app
app = Starlette(
    routes=[
        Route("/chat_completion", chat_completion, methods=["POST"]),
    ],
)


async def server_loop(the_input_queue, config):
    """
    Infinitely runs a server loop to process incoming chat completion requests.

    This function listens to an asynchronous queue for incoming requests, performs log extraction
    and explanation using a language model, and streams the generated responses back to the client.

    Args:
        the_input_queue (asyncio.Queue): The asynchronous queue where incoming requests are placed.
                                        Each item in the queue is a tuple: (input_messages, response_q, generation_params)
        config (dict): A dictionary containing configuration parameters for the model, tokenizer,
                       and prompts.
    """
    # 1. Configure and load the quantized language model
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

    # 2. Create a text streamer for streaming responses
    streamer = TextIteratorStreamer(
        chat_model_tokenizer,
        **config["streamer_params"],
    )

    # Create a text generation pipeline
    chat_completion_pipeline = pipeline(
        "text-generation",
        model=chat_completion_model,
        tokenizer=chat_model_tokenizer,
    )

    # 5. Main server loop
    while True:
        # Get the next request from the queue
        (input_messages, response_q, generation_params) = await the_input_queue.get()


        # Log Extraction: Extract relevant logs using the language model
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


        # Log Explanation: Generate explanations for the extracted logs
        log_explanation_prompt = [
            {"role": "system", "content": "You are a helpful assistant"},
            {
                "role": "user",
                "content": config["log_explanation_prompt"].format(
                    input_logs=extracted_logs
                ),
            },
        ]

        # Run the pipeline in a separate thread for streaming
        # Using a thread here allows the main loop to continue processing other requests
        # while the model is generating the response.
        trd = Thread(
            target=chat_completion_pipeline, # The pipeline function to run
            kwargs=dict( # Keyword arguments for the pipeline
                text_inputs=log_explanation_prompt,
                streamer=streamer, # Use the streamer for streaming output
                **generation_params,  # Client-provided generation parameters
            ),
        )
        trd.start()

        # Put the streamer in the response queue so the `chat_completion` function can consume it.
        await response_q.put((streamer))
        # the_input_queue.task_done() # Indicate that the item has been processed


# Create an event that will run on startup and
@app.on_event("startup")
async def startup_event():
    """
    Runs on application startup to initialize the model queue and start the server loop.

    This event handler creates an asyncio.Queue to hold incoming requests, assigns it to
    `app.model_queue` to make it accessible from request handlers, reads the configuration,
    and starts the `server_loop` task to process the requests.
    """
    # CONFIG_FILE_PATH = environ.get("CONFIG_FILE_PATH")
    CONFIG_FILE_PATH = "./server_config.yaml"

    try:  # Add error handling
        input_queue = asyncio.Queue()

        app.model_queue = input_queue # Make the queue accessible via the app instance
        config = read_config(Path(CONFIG_FILE_PATH))
        asyncio.create_task(server_loop(the_input_queue=input_queue, config=config))
        
        print("Server loop started successfully.")

    except FileNotFoundError:
        print(f"Error: Config file not found at {CONFIG_FILE_PATH}")  # Handle file not found error
        # Consider raising an exception or exiting the application if the config is crucial
    except Exception as e:  # Catch other potential errors during startup
        print(f"An error occurred during startup: {e}")
        # Take appropriate action, like logging the error or exiting
