import requests, json
from typing import List, Optional, Dict
import yaml


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
        return config
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise  # Re-raise the YAMLError after printing the message
    except Exception as e:
        raise



def send_request(host: str, port: int, endpoint_name: str, request_data: dict) -> requests.Response:
    """
    Sends a POST request to a specified endpoint.

    Args:
        host (str): The hostname or IP address of the server.
        port (int): The port number of the server.
        endpoint_name (str): The name of the endpoint to send the request to.
        request_data (dict): The data to be sent in the request body as a JSON object.

    Returns:
        requests.Response: The response object from the server.
    """
    url = f"http://{host}:{port}/{endpoint_name}"
    request_data = json.dumps(request_data)
    response = requests.post(url, data=request_data, stream=True)
    return response


def generate_word(
    connection_params: dict,
    generation_params: dict,
    conv: Optional[List] = None,
    input_text: Optional[str] = None,
):
    """
    Generates a word using a language model API.

    This function handles both single-turn and conversational interactions.

    Args:
        connection_params (dict): Parameters for connecting to the language model API (e.g., host, port).
        generation_params (dict): Parameters controlling the word generation process (e.g., temperature, top_k).
        conv (Optional[List], optional): A list representing the conversation history. Defaults to None.
        input_text (Optional[str], optional): The text input for the current turn. Defaults to None.

    Returns:
        str: The generated word.

    Raises:
        ValueError: If both `conv` and `input_text` are None.
    """

    # Prepare the input for the language model
    if input_text is not None and conv is not None:
        conv.append(dict(role="user", content=input_text))
        the_model_input = conv
    elif input_text is not None:
        the_model_input = input_text
    else:
        raise ValueError("Conversation and input strings both are None")

    # Construct the request data
    request_data = dict(
        input_messages=the_model_input,
        generation_params=generation_params,
    )

    # Send the request to the language model API
    generated_text = ""
    response = send_request(request_data=request_data, **connection_params)

    # Process the response in chunks
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        chunk = json.loads(chunk)
        new_text = chunk["new_word"]
        yield new_text # Yield the generated word for immediate use
        # Can be used for storing the outputs and provide reports later or for many various purposes.
        generated_text += new_text 

    # Update the conversation history if provided
    if conv is not None:
        conv.append(dict(role="assistant", content=generated_text))


def main(configs):
    """
    Main function to handle user input, generate text, and print the output.

    This function continuously prompts the user for input, validates the input,
    and then generates text based on the provided input and configurations.
    The generated text is streamed to the console.

    Args:
        configs (dict): A dictionary containing configuration parameters for 
                         text generation and connection.  It should contain
                         keys "generation_params" and "connection_params"
                         with appropriate values.
    """
    generation_params = configs["generation_params"] # Initial generation parameters from config
    connection_params = configs["connection_params"] # Connection parameters for the text generation service

    while True:
        try:
            input_text = input("INPUT: ")
            if input_text == "":
                print("Invalid input, input cannot be empty.")
                continue

            print("==" * 20, "Log Analysis", "==" * 20, "\n")
            # Stream the generated words/tokens to the console
            for word in generate_word(
                input_text=input_text,
                connection_params=connection_params,
                generation_params=generation_params,
            ):
                print(word, end="", flush=True) # Print immediately without buffering
            
            print() # Newline after generation
            print("==" * 20, "Finished", "==" * 20, "\n")
        except KeyboardInterrupt:
            exit() # Exit gracefully on Ctrl+C


if __name__ == "__main__":
    # Can also be provided in the commandline arguments.
    config_file_path = "./client_config.yaml"

    # Read the configurations from yaml file.
    configs = read_config(config_file_path)
    main(configs)
